"""
네이버 뉴스 검색 API 서비스
정치 관련 최신 뉴스를 검색하고 데이터를 정제하여 제공
"""

import httpx
import logging
import json
import os
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
            "User-Agent": "ai-news-columnist/1.0"
        }
    
    async def search_recent_news(
        self, 
        topic: str, 
        max_results: int = 20,
        days_back: int = 7,
        sort_by: str = "date",
        search_mode: str = "title"
    ) -> List[Dict[str, Any]]:
        """
        주제와 관련된 최신 뉴스를 검색
        
        Args:
            topic: 검색할 주제 키워드
            max_results: 최대 결과 개수 (기본 20개, 최대 100개)
            days_back: 검색 기간 (일 단위, 기본 7일)
            sort_by: 정렬 방식 ('date' 또는 'sim')
            search_mode: 검색 범위 ('title': 제목만, 'all': 제목+내용)
            
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
                
                # 뉴스 데이터 정제 및 필터링 (검색 모드 적용)
                news_items = self._process_news_items(data.get("items", []), days_back, search_mode, topic)
                
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
    
    def _process_news_items(
        self, 
        items: List[Dict], 
        days_back: int, 
        search_mode: str = "title", 
        topic: str = ""
    ) -> List[Dict[str, Any]]:
        """
        네이버 API 응답 데이터를 처리하고 정제
        
        Args:
            items: 네이버 API 응답의 뉴스 아이템들
            days_back: 필터링할 기간 (일 단위)
            search_mode: 검색 범위 ("title": 제목만, "all": 제목+내용)
            topic: 검색할 키워드 (search_mode가 "title"일 때 제목 필터링용)
            
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
                
                # 검색 모드에 따른 키워드 필터링
                if search_mode == "title" and topic:
                    # "title" 모드: 제목에서만 키워드 검색
                    topic_keywords = topic.lower().split()
                    title_lower = title.lower()
                    
                    # 모든 키워드가 제목에 포함되어야 함
                    if not all(keyword in title_lower for keyword in topic_keywords):
                        continue
                # "all" 모드 또는 topic이 없는 경우: 기존대로 모든 뉴스 허용
                
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
    
    def save_news_data_to_json(
        self, 
        news_items: List[Dict[str, Any]], 
        topic: str, 
        save_analysis: bool = True
    ) -> str:
        """
        뉴스 데이터를 JSON 파일로 저장하고 분석 정보도 포함
        
        Args:
            news_items: 저장할 뉴스 데이터
            topic: 검색 주제
            save_analysis: 분석 정보 포함 여부
            
        Returns:
            str: 저장된 파일 경로
        """
        try:
            # 타임스탬프 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_topic = safe_topic.replace(' ', '_')
            
            # 파일 경로 생성
            filename = f"news_{safe_topic}_{timestamp}.json"
            filepath = os.path.join("data", "collected_news", filename)
            
            # 디렉토리 확인 및 생성
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # 저장할 데이터 구조 생성
            save_data = {
                "metadata": {
                    "search_topic": topic,
                    "search_timestamp": datetime.now().isoformat(),
                    "total_results": len(news_items),
                    "data_source": "naver_news_api"
                },
                "news_items": news_items
            }
            
            # 분석 정보 추가
            if save_analysis:
                save_data["analysis"] = self._analyze_news_quality(news_items)
            
            # JSON 파일로 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"뉴스 데이터 저장 완료: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"뉴스 데이터 저장 실패: {str(e)}")
            raise NewsSearchException(f"JSON 저장 실패: {str(e)}")
    
    def _analyze_news_quality(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        뉴스 데이터의 품질을 분석
        
        Args:
            news_items: 분석할 뉴스 데이터
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        if not news_items:
            return {"error": "분석할 뉴스 데이터가 없습니다"}
        
        # description 길이 통계
        desc_lengths = []
        empty_desc_count = 0
        has_original_link_count = 0
        
        for item in news_items:
            desc = item.get('description', '')
            desc_lengths.append(len(desc))
            
            if not desc.strip():
                empty_desc_count += 1
            
            if item.get('originalLink'):
                has_original_link_count += 1
        
        # 통계 계산
        avg_desc_length = sum(desc_lengths) / len(desc_lengths) if desc_lengths else 0
        min_desc_length = min(desc_lengths) if desc_lengths else 0
        max_desc_length = max(desc_lengths) if desc_lengths else 0
        
        # 샘플 뉴스 선택 (가장 긴 description과 가장 짧은 것)
        longest_desc_item = max(news_items, key=lambda x: len(x.get('description', '')))
        shortest_desc_item = min(news_items, key=lambda x: len(x.get('description', '')))
        
        analysis = {
            "quality_metrics": {
                "total_items": len(news_items),
                "empty_description_count": empty_desc_count,
                "empty_description_ratio": empty_desc_count / len(news_items),
                "has_original_link_count": has_original_link_count,
                "original_link_ratio": has_original_link_count / len(news_items)
            },
            "description_statistics": {
                "average_length": round(avg_desc_length, 2),
                "min_length": min_desc_length,
                "max_length": max_desc_length,
                "length_distribution": {
                    "very_short_0_50": sum(1 for l in desc_lengths if 0 <= l <= 50),
                    "short_51_100": sum(1 for l in desc_lengths if 51 <= l <= 100),
                    "medium_101_200": sum(1 for l in desc_lengths if 101 <= l <= 200),
                    "long_201_plus": sum(1 for l in desc_lengths if l > 200)
                }
            },
            "sample_items": {
                "longest_description": {
                    "title": longest_desc_item.get('title', ''),
                    "description": longest_desc_item.get('description', ''),
                    "length": len(longest_desc_item.get('description', '')),
                    "link": longest_desc_item.get('originalLink', '')
                },
                "shortest_description": {
                    "title": shortest_desc_item.get('title', ''),
                    "description": shortest_desc_item.get('description', ''),
                    "length": len(shortest_desc_item.get('description', '')),
                    "link": shortest_desc_item.get('originalLink', '')
                }
            }
        }
        
        return analysis
    
    def print_analysis_summary(self, analysis: Dict[str, Any]) -> None:
        """
        분석 결과를 콘솔에 출력
        
        Args:
            analysis: 분석 결과 데이터
        """
        print("\n" + "="*60)
        print("📊 뉴스 데이터 품질 분석 결과")
        print("="*60)
        
        if "error" in analysis:
            print(f"❌ 분석 오류: {analysis['error']}")
            return
        
        metrics = analysis.get('quality_metrics', {})
        desc_stats = analysis.get('description_statistics', {})
        samples = analysis.get('sample_items', {})
        
        # 기본 통계
        print(f"📝 전체 뉴스 개수: {metrics.get('total_items', 0)}개")
        print(f"🔗 원본 링크 보유: {metrics.get('has_original_link_count', 0)}개 ({metrics.get('original_link_ratio', 0)*100:.1f}%)")
        print(f"❌ 빈 설명 뉴스: {metrics.get('empty_description_count', 0)}개 ({metrics.get('empty_description_ratio', 0)*100:.1f}%)")
        
        # Description 길이 통계
        print(f"\n📏 Description 길이 통계:")
        print(f"   평균 길이: {desc_stats.get('average_length', 0):.1f}자")
        print(f"   최소 길이: {desc_stats.get('min_length', 0)}자")
        print(f"   최대 길이: {desc_stats.get('max_length', 0)}자")
        
        # 길이별 분포
        dist = desc_stats.get('length_distribution', {})
        print(f"\n📊 길이별 분포:")
        print(f"   매우 짧음 (0-50자): {dist.get('very_short_0_50', 0)}개")
        print(f"   짧음 (51-100자): {dist.get('short_51_100', 0)}개") 
        print(f"   보통 (101-200자): {dist.get('medium_101_200', 0)}개")
        print(f"   김 (201자+): {dist.get('long_201_plus', 0)}개")
        
        # 샘플 뉴스
        if 'longest_description' in samples:
            longest = samples['longest_description']
            print(f"\n🏆 가장 긴 Description ({longest.get('length', 0)}자):")
            print(f"   제목: {longest.get('title', '')[:100]}...")
            print(f"   내용: {longest.get('description', '')[:200]}...")
        
        if 'shortest_description' in samples:
            shortest = samples['shortest_description']
            print(f"\n🏁 가장 짧은 Description ({shortest.get('length', 0)}자):")
            print(f"   제목: {shortest.get('title', '')[:100]}...")
            print(f"   내용: '{shortest.get('description', '')}'")
        
        print("\n" + "="*60)
    
    async def search_recent_news_enhanced(
        self,
        topic: str,
        max_results: int = 50,
        days_back: int = 7,
        use_keyword_expansion: bool = True
    ) -> List[Dict[str, Any]]:
        """
        확장된 뉴스 검색: 키워드 다양화 및 다중 검색으로 더 많은 데이터 수집
        
        Args:
            topic: 기본 검색 주제
            max_results: 최대 결과 개수 (기본 50개)
            days_back: 검색 기간 (일 단위, 기본 7일)
            use_keyword_expansion: 키워드 확장 사용 여부
            
        Returns:
            List[Dict[str, Any]]: 확장된 뉴스 목록 (중복 제거됨)
        """
        try:
            logger.info(f"확장 뉴스 검색 시작: '{topic}' (키워드 확장: {use_keyword_expansion})")
            
            all_news = []
            seen_urls = set()  # 중복 제거용
            
            # 1. 기본 키워드로 검색 (최신순)
            logger.info("1단계: 기본 키워드 검색 (최신순)")
            news_date = await self.search_recent_news(
                topic=topic,
                max_results=min(max_results, 40),
                days_back=days_back,
                sort_by="date"
            )
            
            for news in news_date:
                url = news.get('originalLink') or news.get('link')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_news.append(news)
            
            # 2. 기본 키워드로 검색 (관련도순)
            logger.info("2단계: 기본 키워드 검색 (관련도순)")
            news_sim = await self.search_recent_news(
                topic=topic,
                max_results=min(max_results, 40),
                days_back=days_back,
                sort_by="sim"
            )
            
            for news in news_sim:
                url = news.get('originalLink') or news.get('link')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_news.append(news)
            
            # 3. 키워드 확장 검색
            if use_keyword_expansion:
                expanded_keywords = self._generate_expanded_keywords(topic)
                
                for i, keyword in enumerate(expanded_keywords[:3], 1):  # 최대 3개까지
                    logger.info(f"{i+2}단계: 확장 키워드 '{keyword}' 검색")
                    
                    try:
                        expanded_news = await self.search_recent_news(
                            topic=keyword,
                            max_results=30,
                            days_back=days_back,
                            sort_by="date"
                        )
                        
                        for news in expanded_news:
                            url = news.get('originalLink') or news.get('link')
                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                all_news.append(news)
                                
                    except Exception as e:
                        logger.warning(f"확장 키워드 '{keyword}' 검색 실패: {str(e)}")
                        continue
            
            # 4. 결과 정렬 (최신순)
            all_news.sort(key=lambda x: x.get("pubDate", ""), reverse=True)
            
            # 5. 최대 결과 수로 제한
            final_news = all_news[:max_results]
            
            logger.info(f"확장 검색 완료: {len(final_news)}개 뉴스 (중복 제거됨)")
            return final_news
            
        except Exception as e:
            logger.error(f"확장 뉴스 검색 실패: {str(e)}")
            # 실패시 기본 검색으로 폴백
            return await self.search_recent_news(topic, max_results//2, days_back)
    
    def _generate_expanded_keywords(self, topic: str) -> List[str]:
        """
        기본 주제를 바탕으로 확장 키워드 생성
        
        Args:
            topic: 기본 주제
            
        Returns:
            List[str]: 확장된 키워드 목록
        """
        expanded_keywords = []
        
        # 정치인/정당별 확장 패턴
        political_expansions = {
            "조국": ["조국혁신당", "조국 대표", "조국혁신정책연구원"],
            "조국혁신당": ["조국", "강미정", "조국혁신당 성비위", "조국혁신당 대변인"],
            "윤석열": ["윤석열 대통령", "윤석열 정부", "대통령실"],
            "이재명": ["이재명 대표", "더불어민주당", "민주당"],
            "탄핵": ["탄핵소추", "탄핵 정치", "국정조사"],
            "국정감사": ["국정감사 정치", "국감", "국회 감사"],
            "기자회견": ["브리핑", "기자간담회", "발표"]
        }
        
        # 주제에 포함된 키워드 기반 확장
        for key, expansions in political_expansions.items():
            if key in topic:
                expanded_keywords.extend(expansions)
        
        # 일반적인 정치 키워드 조합
        base_terms = topic.split()
        if len(base_terms) > 1:
            # 개별 단어들로도 검색
            for term in base_terms:
                if len(term) > 1:  # 한 글자 제외
                    expanded_keywords.append(term)
        
        # 중복 제거 및 원본 제외
        expanded_keywords = list(set(expanded_keywords))
        if topic in expanded_keywords:
            expanded_keywords.remove(topic)
        
        logger.debug(f"키워드 확장: '{topic}' → {expanded_keywords}")
        return expanded_keywords