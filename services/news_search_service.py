"""
네이버 뉴스 검색 API 서비스
정치 관련 최신 뉴스를 검색하고 데이터를 정제하여 제공
"""

import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
import html
import re

from schemas import Source
from core.exceptions import NewsSearchException

logger = logging.getLogger(__name__)


class NaverNewsSearchService:
    """네이버 뉴스 검색 API 서비스 클래스"""
    
    def __init__(self, client_id: str, client_secret: str):
        """
        네이버 뉴스 검색 서비스 초기화
        
        Args:
            client_id: 네이버 API 클라이언트 ID
            client_secret: 네이버 API 클라이언트 Secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/news.json"
        
        # API 헤더 설정
        self.headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "User-Agent": "AI-Political-Columnist/1.0"
        }
    
    async def search_recent_news(
        self, 
        topic: str, 
        max_results: int = 20,
        days_back: int = 7,
        sort_by: str = "date"
    ) -> List[Dict[str, Any]]:
        """
        주제와 관련된 최신 뉴스를 검색
        
        Args:
            topic: 검색할 주제 키워드
            max_results: 최대 결과 개수 (기본 20개, 최대 100개)
            days_back: 검색 기간 (일 단위, 기본 7일)
            sort_by: 정렬 방식 ('date' 또는 'sim')
            
        Returns:
            List[Dict[str, Any]]: 검색된 뉴스 목록
        """
        try:
            logger.info(f"네이버 뉴스 검색 시작: '{topic}' (최근 {days_back}일)")
            
            # 검색 쿼리 최적화 - 정치 관련 키워드 추가
            optimized_query = self._optimize_political_query(topic)
            
            # API 요청 파라미터 설정
            params = {
                "query": optimized_query,
                "display": min(max_results, 100),  # 최대 100개로 제한
                "start": 1,
                "sort": sort_by  # 'date' (최신순) 또는 'sim' (관련도순)
            }
            
            # 네이버 API 호출
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"네이버 API 호출 실패: {response.status_code}")
                    raise NewsSearchException(f"뉴스 검색 API 오류: {response.status_code}")
                
                data = response.json()
                
                # 뉴스 데이터 정제 및 필터링
                news_items = self._process_news_items(data.get("items", []), days_back)
                
                logger.info(f"뉴스 검색 완료: {len(news_items)}개 뉴스 발견")
                return news_items
                
        except httpx.TimeoutException:
            logger.error("네이버 API 호출 타임아웃")
            raise NewsSearchException("뉴스 검색 타임아웃")
        except Exception as e:
            logger.error(f"뉴스 검색 중 오류: {str(e)}")
            raise NewsSearchException(f"뉴스 검색 실패: {str(e)}")
    
    def _optimize_political_query(self, topic: str) -> str:
        """
        정치 관련 검색 쿼리를 최적화
        
        Args:
            topic: 원본 주제
            
        Returns:
            str: 최적화된 검색 쿼리
        """
        # 정치 관련 키워드 매핑
        political_keywords = {
            "윤석열": "윤석열 대통령",
            "이재명": "이재명 민주당",
            "탄핵": "탄핵 정치",
            "국정감사": "국정감사 정치",
            "선거": "선거 정치",
            "여당": "여당 국민의힘",
            "야당": "야당 민주당"
        }
        
        # 기본 정치 키워드 추가
        optimized = topic
        for keyword, enhanced in political_keywords.items():
            if keyword in topic:
                optimized = optimized.replace(keyword, enhanced)
        
        # 정치 관련 키워드가 없으면 정치 키워드 추가
        if not any(keyword in optimized.lower() for keyword in ["정치", "대통령", "국회", "의원", "당"]):
            optimized += " 정치"
        
        logger.debug(f"검색 쿼리 최적화: '{topic}' → '{optimized}'")
        return optimized
    
    def _process_news_items(self, items: List[Dict], days_back: int) -> List[Dict[str, Any]]:
        """
        네이버 API 응답 데이터를 처리하고 정제
        
        Args:
            items: 네이버 API 응답의 뉴스 아이템들
            days_back: 필터링할 기간 (일 단위)
            
        Returns:
            List[Dict[str, Any]]: 정제된 뉴스 목록
        """
        processed_items = []
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        for item in items:
            try:
                # HTML 태그 제거 및 텍스트 정제
                title = html.unescape(re.sub(r'<[^>]+>', '', item.get("title", "")))
                description = html.unescape(re.sub(r'<[^>]+>', '', item.get("description", "")))
                
                # 발행일 파싱 (네이버 형식: "Tue, 03 Sep 2024 10:30:00 +0900")
                pub_date_str = item.get("pubDate", "")
                pub_date = self._parse_naver_date(pub_date_str)
                
                # 기간 필터링 - 설정된 기간 내의 뉴스만 포함
                if pub_date and pub_date < cutoff_date:
                    continue
                
                # 정치 관련성 검증
                if not self._is_political_news(title, description):
                    continue
                
                processed_item = {
                    "title": title,
                    "description": description,
                    "link": item.get("originallink", item.get("link", "")),
                    "pubDate": pub_date.isoformat() if pub_date else pub_date_str,
                    "originalLink": item.get("originallink", ""),
                    "naverLink": item.get("link", "")
                }
                
                processed_items.append(processed_item)
                
            except Exception as e:
                logger.warning(f"뉴스 아이템 처리 중 오류: {str(e)}")
                continue
        
        # 발행일 순으로 정렬 (최신순)
        processed_items.sort(key=lambda x: x["pubDate"], reverse=True)
        
        logger.debug(f"뉴스 정제 완료: {len(items)}개 → {len(processed_items)}개")
        return processed_items
    
    def _parse_naver_date(self, date_str: str) -> Optional[datetime]:
        """
        네이버 API의 날짜 형식을 파싱
        
        Args:
            date_str: 네이버 API 날짜 문자열
            
        Returns:
            Optional[datetime]: 파싱된 datetime 객체
        """
        try:
            # 네이버 형식: "Tue, 03 Sep 2024 10:30:00 +0900"
            # strptime으로 파싱
            return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        except Exception as e:
            logger.warning(f"날짜 파싱 실패: {date_str} - {str(e)}")
            return None
    
    def _is_political_news(self, title: str, description: str) -> bool:
        """
        뉴스가 정치 관련인지 판단
        
        Args:
            title: 뉴스 제목
            description: 뉴스 설명
            
        Returns:
            bool: 정치 뉴스 여부
        """
        political_keywords = [
            # 정부 관련
            "대통령", "정부", "청와대", "국무총리", "장관", "정부", "행정부",
            # 국회 관련  
            "국회", "의원", "국정감사", "국정조사", "법안", "입법", "의정",
            # 정당 관련
            "민주당", "국민의힘", "정의당", "여당", "야당", "정치인", "정당",
            # 정치 이슈
            "선거", "투표", "공약", "정책", "개헌", "탄핵", "사퇴", "임명",
            # 정치적 사건
            "정치", "외교", "국정", "정무", "내각", "권력", "정치권"
        ]
        
        text = (title + " " + description).lower()
        
        # 정치 키워드가 포함되어 있는지 확인
        return any(keyword in text for keyword in political_keywords)
    
    def convert_to_sources(self, news_items: List[Dict[str, Any]]) -> List[Source]:
        """
        뉴스 데이터를 Source 스키마로 변환
        
        Args:
            news_items: 검색된 뉴스 아이템들
            
        Returns:
            List[Source]: Source 스키마로 변환된 목록
        """
        sources = []
        
        for item in news_items:
            try:
                source = Source(
                    title=item["title"],
                    uri=item.get("link", "")
                )
                sources.append(source)
                
            except Exception as e:
                logger.warning(f"Source 변환 중 오류: {str(e)}")
                continue
        
        logger.info(f"Source 변환 완료: {len(sources)}개")
        return sources
    
    def format_news_for_prompt(self, news_items: List[Dict[str, Any]]) -> str:
        """
        뉴스 데이터를 프롬프트에 사용할 수 있는 형식으로 포맷
        
        Args:
            news_items: 검색된 뉴스 아이템들
            
        Returns:
            str: 프롬프트용으로 포맷된 뉴스 텍스트
        """
        if not news_items:
            return "관련 뉴스를 찾을 수 없습니다."
        
        formatted_news = []
        
        for i, item in enumerate(news_items[:10], 1):  # 최대 10개만 사용
            news_text = f"""
[뉴스 {i}]
제목: {item['title']}
내용: {item['description']}
발행일: {item['pubDate']}
링크: {item.get('originalLink', item.get('link', ''))}
"""
            formatted_news.append(news_text.strip())
        
        return "\n\n".join(formatted_news)