"""
컨텐츠 생성 서비스
OpenAI gpt-4.1-mini API를 사용하여 정치 컬럼을 생성하는 전용 모듈
"""

import logging
from typing import Dict, List, Any
from openai import AsyncOpenAI

from schemas import Source
from core.exceptions import GeminiAPIException, ContentGenerationException
from .prompts import PromptGenerator

logger = logging.getLogger(__name__)


class ContentGenerationService:
    """컨텐츠 생성 전용 서비스 클래스"""
    
    def __init__(self, api_key: str):
        """
        컨텐츠 생성 서비스 초기화
        
        Args:
            api_key: OpenAI API 키
        """
        self.api_key = api_key
        
        # OpenAI 클라이언트 초기화
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # 사용할 모델 설정
        self.model = "gpt-4.1-mini"
        
        self.prompt_generator = PromptGenerator()
    
    async def generate_column_from_news(
        self, 
        topic: str, 
        news_data: List[Dict[str, Any]]
    ) -> str:
        """
        뉴스 데이터를 기반으로 정치 컬럼 생성
        
        Args:
            topic: 컬럼 주제
            news_data: 네이버 뉴스 검색 결과
            
        Returns:
            str: 생성된 컬럼 텍스트
        """
        try:
            logger.info(f"뉴스 기반 컬럼 생성 시작: {topic}")
            
            # 뉴스 데이터를 프롬프트용으로 포맷
            news_summary = self._format_news_for_prompt(news_data)
            
            # 뉴스 소스 정보 추출
            news_sources = [{
                'title': item.get('title', 'N/A'),
                'url': item.get('originalLink', item.get('link', '#'))
            } for item in news_data[:10]]
            
            # 뉴스 기반 컬럼 생성 프롬프트 생성
            prompt = self.prompt_generator.get_draft_prompt_with_news(topic, news_summary, news_sources)
            
            # OpenAI API 호출하여 컬럼 생성
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "당신은 전문 정치 저널리스트입니다. 제공된 뉴스 데이터를 바탕으로 균형잡힌 정치 컬럼을 작성해주세요."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_completion_tokens=3000
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise ContentGenerationException("OpenAI API가 빈 응답을 반환했습니다.")
            
            generated_text = response.choices[0].message.content
            logger.info(f"뉴스 기반 컬럼 생성 완료: {len(generated_text)} 글자")
            return generated_text
            
        except Exception as e:
            logger.error(f"뉴스 기반 컬럼 생성 실패: {str(e)}")
            raise ContentGenerationException(f"컬럼 생성 중 오류: {str(e)}")
    
    
    async def generate_with_web_search(self, topic: str) -> tuple[str, List[Source]]:
        """
        ⚠️ 이 함수는 더 이상 사용되지 않습니다.
        모든 컬럼 생성은 반드시 네이버 뉴스 데이터에 기반해야 합니다.
        
        Args:
            topic: 컬럼 주제
            
        Returns:
            tuple[str, List[Source]]: 오류 발생
        """
        logger.error(f"뉴스 데이터 없이 컬럼 생성 시도 거부됨: {topic}")
        raise ContentGenerationException(
            "팩트 기반 정치 컬럼 생성을 위해 뉴스 데이터가 반드시 필요합니다. "
            "네이버 뉴스 검색 결과가 없어 컬럼을 생성할 수 없습니다."
        )
    
    def _format_news_for_prompt(self, news_data: List[Dict[str, Any]]) -> str:
        """
        뉴스 데이터를 프롬프트에 사용할 수 있는 형식으로 포맷
        
        Args:
            news_data: 검색된 뉴스 데이터
            
        Returns:
            str: 프롬프트용으로 포맷된 뉴스 텍스트
        """
        if not news_data:
            return "관련 뉴스를 찾을 수 없습니다."
        
        formatted_news = []
        
        for i, item in enumerate(news_data[:10], 1):  # 최대 10개만 사용
            news_text = f"""
                [뉴스 {i}] {item.get('title', 'N/A')}
                - 내용: {item.get('description', 'N/A')}
                - 발행일: {item.get('pubDate', 'N/A')}
                - 출처: {item.get('originalLink', item.get('link', 'N/A'))}
                """
            formatted_news.append(news_text.strip())
        
        formatted_result = "\n\n".join(formatted_news)
        logger.debug(f"뉴스 프롬프트 포맷팅 완료: {len(news_data)}개 → {len(formatted_result)} 글자")
        
        return formatted_result
    
    
    async def extract_title_and_summary(self, content: str) -> tuple[str, str]:
        """
        생성된 마크다운 컬럼에서 제목과 요약 추출
        
        Args:
            content: 생성된 마크다운 컬럼 텍스트
            
        Returns:
            tuple[str, str]: 제목과 요약
        """
        try:
            logger.info("마크다운 컬럼에서 제목과 요약 추출 시작")
            
            lines = content.split('\n')
            title = "정치 컬럼"
            summary = "정치 이슈에 대한 균형잡힌 분석입니다."
            
            # 첫 번째 ## 헤딩을 제목으로 사용
            for line in lines:
                line = line.strip()
                if line.startswith('## ') and not line.startswith('## 💬') and not line.startswith('## 🧨') and not line.startswith('## 📌'):
                    title = line[3:].strip()  # '## ' 제거
                    break
            
            # 제목 다음의 첫 번째 비어있지 않은 문단을 요약으로 사용
            found_title = False
            for line in lines:
                line = line.strip()
                if line.startswith('## ') and title in line:
                    found_title = True
                    continue
                elif found_title and line and not line.startswith('#') and not line.startswith('## '):
                    # 300자 이내로 강제 제한 (초과 시 297자 + 말줄임표, 최종 <= 300)
                    if len(line) > 300:
                        summary = (line[:297]).rstrip() + "..."
                    else:
                        summary = line
                    break
            
            logger.info(f"제목/요약 추출 완료: {title}")
            return title, summary
            
        except Exception as e:
            logger.error(f"제목/요약 추출 실패: {str(e)}")
            # Fallback: 기본값 반환
            return "정치 컬럼", "정치 이슈에 대한 균형잡힌 분석입니다."