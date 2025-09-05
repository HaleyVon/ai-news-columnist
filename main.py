"""
AI 정치 컬럼니스트 FastAPI 애플리케이션
AI API를 활용한 정치 컬럼 생성 서비스
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum
import google.generativeai as genai
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from schemas import (
    ColumnRequest,
    ColumnResponse,
    ArticleData,
    MetaData,
    ErrorResponse,
    NewsPreviewResponse,
    NewsSearchResult,
    ColumnGenerationConfirmRequest
)
from services.gemini_service import GeminiService
from core.config import settings
from core.exceptions import CustomHTTPException

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title="AI 정치 컬럼니스트 API",
    description="AI API를 활용한 정치 컬럼 생성 서비스",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None
)

# Rate Limiter 설정
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    max_age=600  # 10분 동안 preflight 캐시
)

# 보안 미들웨어 추가
from middleware.security import SecurityMiddleware, InputSanitizationMiddleware, RequestLoggingMiddleware

app.add_middleware(SecurityMiddleware)
app.add_middleware(InputSanitizationMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# AI 서비스 인스턴스 생성 (OpenAI + 네이버 API 키 포함)
gemini_service = GeminiService(
    openai_api_key=settings.openai_api_key,  # OpenAI API 키
    naver_client_id=settings.naver_client_id if settings.naver_client_id else None,
    naver_client_secret=settings.naver_client_secret if settings.naver_client_secret else None
)

# 뉴스 데이터 임시 캐시 (메모리 기반)
# 키: "topic_daysBack_searchMode", 값: {"news_data": List[dict], "sources": List[Source], "timestamp": datetime}
news_cache: Dict[str, Dict[str, Any]] = {}


@app.exception_handler(CustomHTTPException)
async def custom_exception_handler(request: Request, exc: CustomHTTPException):
    """커스텀 예외 처리기"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=exc.detail,
            processedDate=datetime.utcnow().isoformat() + "Z"
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리기"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error="서버 내부 오류가 발생했습니다.",
            processedDate=datetime.utcnow().isoformat() + "Z"
        ).model_dump()
    )


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/generate-column", response_model=ColumnResponse)
@limiter.limit("5/minute")  # 분당 5회 요청 제한
async def generate_column(request: Request, column_request: ColumnRequest):
    """
    정치 컬럼 생성 API 엔드포인트
    
    Args:
        column_request: 컬럼 생성 요청 데이터
        
    Returns:
        ColumnResponse: 생성된 컬럼 데이터
        
    Raises:
        HTTPException: 컬럼 생성 실패 시
    """
    try:
        logger.info(f"컬럼 생성 요청: {column_request.topic}")
        
        # 컬럼 생성 (뉴스 검색 기간 및 검색 모드 파라미터 추가)
        article_content = await gemini_service.generate_column(
            topic=column_request.topic,
            max_revision_attempts=column_request.maxRevisionAttempts,
            days_back=column_request.daysBack,
            search_mode=column_request.searchMode
        )
        
        # 메타데이터 생성
        word_count = len(article_content.content.replace(" ", ""))
        created_date = datetime.utcnow().isoformat() + "Z"
        
        # 요약 길이 가드(<=300자). 초과 시 말줄임표 추가
        safe_summary = article_content.summary
        if isinstance(safe_summary, str) and len(safe_summary) > 300:
            safe_summary = (safe_summary[:297]).rstrip() + "..."

        # Source 모델 입력 정규화 (테스트에서 MagicMock을 반환해도 dict로 변환)
        normalized_sources = None
        if getattr(article_content, "sources", None):
            normalized_sources = []
            for s in article_content.sources:
                try:
                    if isinstance(s, dict):
                        normalized_sources.append({
                            "title": s.get("title", ""),
                            "uri": s.get("uri", "")
                        })
                    else:
                        title = getattr(s, "title", "")
                        uri = getattr(s, "uri", "")
                        normalized_sources.append({"title": title, "uri": uri})
                except Exception:
                    continue

        # 응답 데이터 구성
        response = ColumnResponse(
            success=True,
            article=ArticleData(
                title=article_content.title,
                summary=safe_summary,
                content=article_content.content,
                metadata=MetaData(
                    wordCount=word_count,
                    category="정치",
                    createdDate=created_date,
                    sources=normalized_sources
                )
            ),
            processedDate=created_date
        )
        
        logger.info(f"컬럼 생성 완료: {article_content.title}")
        return response
        
    except ValueError as e:
        logger.error(f"입력 검증 오류: {str(e)}")
        raise CustomHTTPException(
            status_code=400,
            detail=f"입력 데이터가 올바르지 않습니다: {str(e)}"
        )
    except Exception as e:
        logger.error(f"컬럼 생성 중 오류: {str(e)}")
        raise CustomHTTPException(
            status_code=500,
            detail="컬럼 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


# 새로운 엔드포인트 추가: 뉴스 미리보기
@app.post("/api/preview-news", response_model=NewsPreviewResponse)
@limiter.limit("10/minute")  # 미리보기는 더 자주 허용
async def preview_news(request: Request, column_request: ColumnRequest):
    """
    뉴스 검색 결과 미리보기 API 엔드포인트
    사용자가 컬럼 생성 전에 검색될 뉴스를 확인할 수 있습니다.
    
    Args:
        column_request: 컬럼 생성 요청 데이터
        
    Returns:
        NewsPreviewResponse: 뉴스 검색 결과 미리보기
    """
    try:
        logger.info(f"뉴스 미리보기 요청: {column_request.topic}")
        
        # 뉴스 검색만 실행 (컬럼 생성은 하지 않음, 검색 모드 포함)
        news_data, sources = await gemini_service._search_latest_news(
            topic=column_request.topic, 
            days_back=column_request.daysBack,
            search_mode=column_request.searchMode
        )
        
        # 뉴스 데이터를 캐시에 저장 (확정 API에서 재사용하기 위해)
        cache_key = f"{column_request.topic}_{column_request.daysBack}_{column_request.searchMode}"
        news_cache[cache_key] = {
            "news_data": news_data,
            "sources": sources,
            "timestamp": datetime.utcnow()
        }
        logger.info(f"뉴스 데이터 캐시 저장: {cache_key} (뉴스 {len(news_data)}개)")
        
        # 검색 품질 평가
        news_count = len(news_data)
        if news_count >= 10:
            quality = "excellent"
            recommendation = f"충분한 뉴스 데이터({news_count}개)로 고품질 컬럼 생성이 가능합니다. 바로 진행하세요!"
        elif news_count >= 5:
            quality = "good"
            recommendation = f"양호한 뉴스 데이터({news_count}개)입니다. 컬럼 생성을 진행할 수 있습니다."
        elif news_count >= 2:
            quality = "fair"
            recommendation = f"제한적인 뉴스 데이터({news_count}개)입니다. 검색 기간을 늘리거나 키워드를 조정해보세요."
        else:
            quality = "poor"
            recommendation = "뉴스 데이터가 부족합니다. 다른 주제나 검색 기간으로 다시 시도해보세요."
        
        # 미리보기용 뉴스 목록 (최대 5개)
        preview_news = []
        for item in news_data[:5]:
            preview_news.append(NewsSearchResult(
                title=item.get('title', '제목 없음'),
                description=item.get('description', '설명 없음'),
                pubDate=item.get('pubDate', '날짜 없음'),
                originalLink=item.get('originalLink')
            ))
        
        return NewsPreviewResponse(
            success=True,
            topic=column_request.topic,
            searchPeriod=column_request.daysBack,
            newsCount=len(preview_news),
            newsItems=preview_news,
            totalAvailable=news_count,
            searchQuality=quality,
            recommendation=recommendation,
            processedDate=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"뉴스 미리보기 실패: {str(e)}")
        raise CustomHTTPException(
            status_code=500, 
            detail=f"뉴스 미리보기 중 오류: {str(e)}"
        )


@app.post("/api/generate-column-confirmed", response_model=ColumnResponse)
@limiter.limit("3/minute")  # 실제 컬럼 생성은 더 엄격한 제한
async def generate_column_confirmed(request: Request, confirm_request: ColumnGenerationConfirmRequest):
    """
    사용자 확인 후 컬럼 생성 API 엔드포인트
    뉴스 미리보기를 확인한 후 컬럼 생성을 진행합니다.
    
    Args:
        confirm_request: 컬럼 생성 확인 요청
        
    Returns:
        ColumnResponse: 생성된 컬럼 데이터 또는 중단 메시지
    """
    try:
        if not confirm_request.proceed:
            logger.info(f"사용자가 컬럼 생성을 취소: {confirm_request.topic}")
            raise CustomHTTPException(
                status_code=400, 
                detail="사용자가 컬럼 생성을 취소했습니다."
            )
        
        logger.info(f"사용자 승인 후 컬럼 생성 시작: {confirm_request.topic}")
        
        # 캐시에서 기존 뉴스 데이터 확인 (재검색 방지)
        cache_key = f"{confirm_request.topic}_{confirm_request.daysBack}_{confirm_request.searchMode}"
        cached_data = news_cache.get(cache_key)
        
        if cached_data:
            # 캐시된 뉴스 데이터로 컬럼 생성 (재검색 없음)
            logger.info(f"캐시된 뉴스 데이터 사용: {cache_key} (뉴스 {len(cached_data['news_data'])}개)")
            article_content = await gemini_service.generate_column_with_news(
                topic=confirm_request.topic,
                news_data=cached_data["news_data"],
                sources=cached_data["sources"], 
                max_revision_attempts=confirm_request.maxRevisionAttempts
            )
            # 사용된 캐시 데이터는 정리
            del news_cache[cache_key]
        else:
            # 캐시 데이터가 없으면 일반 컬럼 생성 (재검색 수행)
            logger.warning(f"캐시 데이터가 없어 재검색 수행: {cache_key}")
            article_content = await gemini_service.generate_column(
                topic=confirm_request.topic,
                max_revision_attempts=confirm_request.maxRevisionAttempts,
                days_back=confirm_request.daysBack,
                search_mode=confirm_request.searchMode
            )
        
        # 메타데이터 생성 (기존 로직과 동일)
        word_count = len(article_content.content.replace(" ", ""))
        created_date = datetime.utcnow().isoformat() + "Z"
        
        # 요약 길이 가드(<=300자). 초과 시 말줄임표 추가
        safe_summary = article_content.summary
        if isinstance(safe_summary, str) and len(safe_summary) > 300:
            safe_summary = (safe_summary[:297]).rstrip() + "..."

        # Source 모델 입력 정규화
        normalized_sources = None
        if getattr(article_content, "sources", None):
            normalized_sources = []
            for s in article_content.sources:
                try:
                    if isinstance(s, dict):
                        normalized_sources.append({
                            "title": s.get("title", ""),
                            "uri": s.get("uri", "")
                        })
                    else:
                        title = getattr(s, "title", "")
                        uri = getattr(s, "uri", "")
                        normalized_sources.append({"title": title, "uri": uri})
                except Exception as e:
                    logger.warning(f"Source 정규화 중 오류: {str(e)}")
                    continue

        # 응답 생성
        response = ColumnResponse(
            success=True,
            article=ArticleData(
                title=article_content.title,
                summary=safe_summary,
                content=article_content.content,
                metadata=MetaData(
                    wordCount=word_count,
                    category="정치 컬럼",
                    createdDate=created_date,
                    sources=normalized_sources
                )
            ),
            processedDate=created_date
        )
        
        logger.info(f"사용자 승인 후 컬럼 생성 완료: {confirm_request.topic}")
        return response
        
    except CustomHTTPException:
        raise  # CustomHTTPException은 그대로 re-raise
    except Exception as e:
        logger.error(f"확인된 컬럼 생성 실패: {str(e)}")
        raise CustomHTTPException(
            status_code=500, 
            detail=f"컬럼 생성 중 오류: {str(e)}"
        )


# AWS Lambda용 핸들러 (Mangum 어댑터)
handler = Mangum(app, lifespan="off")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True if not settings.is_production else False
    )