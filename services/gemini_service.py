"""
통합 AI 정치 컬럼니스트 서비스
네이버 뉴스 검색, 컨텐츠 생성, 품질 평가를 통합하여 관리하는 메인 서비스
"""

import logging
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime

from schemas import GeneratedContent, EvaluationResult, Source
from core.exceptions import GeminiAPIException, ContentGenerationException, NewsSearchException
from .news_search_service import NaverNewsSearchService
from .content_generation_service import ContentGenerationService
from .content_evaluation_service import ContentEvaluationService

logger = logging.getLogger(__name__)


class GeminiService:
    """
    통합 AI 정치 컬럼니스트 서비스 클래스
    3단계 프로세스로 고품질 정치 컬럼을 생성합니다:
    1단계: 네이버 뉴스 검색으로 최신 뉴스 수집
    2단계: AI로 뉴스 기반 컬럼 생성  
    3단계: 품질 평가 및 반복 수정
    """
    
    def __init__(
        self, 
        openai_api_key: str,
        naver_client_id: Optional[str] = None,
        naver_client_secret: Optional[str] = None
    ):
        """
        통합 서비스 초기화
        
        Args:
            openai_api_key: OpenAI API 키
            naver_client_id: 네이버 API 클라이언트 ID (선택)
            naver_client_secret: 네이버 API 클라이언트 시크릿 (선택)
        """
        self.openai_api_key = openai_api_key
        
        # 서비스 인스턴스 초기화 (OpenAI API 키 사용)
        self.content_generator = ContentGenerationService(openai_api_key)
        self.content_evaluator = ContentEvaluationService(openai_api_key)
        
        # 네이버 뉴스 검색 서비스 (API 키가 있는 경우에만)
        self.news_searcher = None
        if naver_client_id and naver_client_secret:
            self.news_searcher = NaverNewsSearchService(naver_client_id, naver_client_secret)
            logger.info("네이버 뉴스 검색 서비스 활성화")
        else:
            logger.warning("네이버 API 키가 없어 뉴스 검색 기능 비활성화")
    
    async def generate_column(self, topic: str, max_revision_attempts: int = 3) -> GeneratedContent:
        """
        3단계 프로세스로 고품질 정치 컬럼 생성
        
        Args:
            topic: 컬럼 주제
            max_revision_attempts: 최대 수정 시도 횟수
            
        Returns:
            GeneratedContent: 생성된 컬럼 및 메타데이터
        """
        try:
            logger.info(f"3단계 컬럼 생성 시작: {topic} (최대 수정 {max_revision_attempts}회)")
            
            # 🔍 1단계: 네이버 뉴스 검색으로 최신 뉴스 수집
            logger.info("1단계: 네이버 뉴스 검색으로 최신 뉴스 수집 시작")
            news_data, sources = await self._search_latest_news(topic)
            logger.info(f"뉴스 수집 완료: {len(news_data)} 건의 관련 뉴스 발견")
            
            # ✍️ 2단계: 수집된 뉴스를 바탕으로 컬럼 생성
            logger.info("2단계: 수집된 뉴스 기반 컬럼 생성 시작")
            if news_data:
                current_content = await self.content_generator.generate_column_from_news(topic, news_data)
            else:
                # 뉴스 데이터가 없으면 컬럼 생성 불가
                logger.error("뉴스 데이터가 없어 컬럼 생성 불가")
                raise ContentGenerationException(
                    f"'{topic}' 관련 뉴스를 찾을 수 없어 팩트 기반 컬럼을 생성할 수 없습니다. "
                    "네이버 뉴스 API 설정을 확인해주세요."
                )
                
            logger.info("컬럼 초안 생성 완료")
            
            # 📝 3단계: 반복적 품질 평가 및 수정
            logger.info("3단계: 컬럼 품질 평가 및 수정 시작")
            for attempt in range(max_revision_attempts):
                logger.info(f"품질 평가 시도 {attempt + 1}/{max_revision_attempts}")
                
                evaluation = await self.content_evaluator.evaluate_and_revise(current_content)
                
                if evaluation.pass_:
                    logger.info("품질 기준 통과. 컬럼 생성 완료")
                    break
                
                current_content = evaluation.revisedContent
                logger.info(f"수정 완료. 피드백: {evaluation.feedback[:100]}...")
            
            # 📄 4단계: 제목과 요약 추출
            title, summary = await self.content_generator.extract_title_and_summary(current_content)
            
            result = GeneratedContent(
                title=title,
                summary=summary,
                content=current_content,
                sources=sources
            )
            
            logger.info("3단계 컬럼 생성 프로세스 완료")
            return result
            
        except (GeminiAPIException, ContentGenerationException, NewsSearchException):
            raise
        except Exception as e:
            logger.error(f"컬럼 생성 중 예상치 못한 오류: {str(e)}")
            raise ContentGenerationException(f"컬럼 생성 중 오류가 발생했습니다: {str(e)}")
    
    async def _search_latest_news(self, topic: str) -> Tuple[List[dict], List[Source]]:
        """
        1단계: 주제 관련 최신 뉴스 검색
        
        Args:
            topic: 검색할 주제
            
        Returns:
            Tuple[List[dict], List[Source]]: 뉴스 데이터와 소스 목록
        """
        if not self.news_searcher:
            logger.warning("네이버 뉴스 검색 서비스가 비활성화되어 빈 결과 반환")
            return [], []
        
        try:
            logger.info(f"주제 '{topic}'에 대한 네이버 뉴스 검색 시작")
            
            # 네이버 뉴스 검색 실행
            news_data = await self.news_searcher.search_recent_news(
                topic=topic,
                max_results=20,  # 최대 20개 뉴스
                days_back=7,     # 최근 7일
                sort_by="date"   # 최신순 정렬
            )
            
            # Source 객체로 변환
            sources = self.news_searcher.convert_to_sources(news_data)
            
            logger.info(f"뉴스 검색 완료: {len(news_data)}개 뉴스, {len(sources)}개 소스")
            return news_data, sources
            
        except Exception as e:
            logger.error(f"뉴스 검색 실패: {str(e)}")
            # Fallback: 빈 결과 반환
            return [], []
    
    async def generate_draft_ts_style(self, topic: str) -> Tuple[str, List[Source]]:
        """
        TypeScript 스타일 호환성을 위한 간단한 컬럼 생성 메서드
        
        Args:
            topic: 컬럼 주제
            
        Returns:
            Tuple[str, List[Source]]: 생성된 텍스트와 소스 목록
        """
        try:
            logger.info(f"TypeScript 호환 모드로 컬럼 생성: {topic}")
            
            # 간단한 1단계 프로세스로 실행 (평가 없이)
            news_data, sources = await self._search_latest_news(topic)
            
            if news_data:
                content = await self.content_generator.generate_column_from_news(topic, news_data)
            else:
                # 뉴스 데이터가 없으면 컬럼 생성 불가
                logger.error(f"네이버 뉴스 검색 실패로 컬럼 생성 불가: {topic}")
                raise ContentGenerationException(
                    f"'{topic}' 관련 뉴스를 찾을 수 없어 팩트 기반 컬럼을 생성할 수 없습니다."
                )
            
            logger.info(f"TypeScript 호환 컬럼 생성 완료: {len(sources)}개 소스")
            return content, sources
            
        except Exception as e:
            logger.error(f"TypeScript 스타일 생성 실패: {str(e)}")
            # 뉴스 데이터 없이는 컬럼 생성 불가
            logger.error(f"뉴스 검색 실패로 컬럼 생성 불가: {str(e)}")
            raise ContentGenerationException(
                f"'{topic}' 관련 뉴스를 찾을 수 없어 팩트 기반 컬럼을 생성할 수 없습니다. "
                f"오류: {str(e)}"
            )
    
    async def evaluate_and_revise(self, content: str) -> EvaluationResult:
        """
        컨텐츠 평가 및 수정
        
        Args:
            content: 평가할 컨텐츠
            
        Returns:
            EvaluationResult: 평가 결과
        """
        return await self.content_evaluator.evaluate_and_revise(content)
    
    async def get_quality_metrics(self, content: str) -> dict:
        """
        컨텐츠의 품질 지표 조회
        
        Args:
            content: 분석할 컨텐츠
            
        Returns:
            dict: 품질 지표 정보
        """
        try:
            scores = await self.content_evaluator.get_quality_score(content)
            metrics = self.content_evaluator.calculate_overall_quality(scores)
            
            logger.info(f"품질 지표 조회 완료: {metrics['grade']} ({metrics['averageScore']}점)")
            return metrics
            
        except Exception as e:
            logger.error(f"품질 지표 조회 실패: {str(e)}")
            return {
                "error": str(e),
                "averageScore": 0.0,
                "grade": "오류"
            }
    
    def get_service_status(self) -> dict:
        """
        서비스 상태 확인
        
        Returns:
            dict: 서비스 상태 정보
        """
        status = {
            "gemini_service": True,
            "content_generation": True,
            "content_evaluation": True,
            "news_search": self.news_searcher is not None,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"서비스 상태 확인: 뉴스검색={'활성' if status['news_search'] else '비활성'}")
        return status