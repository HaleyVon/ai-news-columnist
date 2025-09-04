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
    ErrorResponse
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
        
        # 컬럼 생성
        article_content = await gemini_service.generate_column(
            topic=column_request.topic,
            max_revision_attempts=column_request.maxRevisionAttempts
        )
        
        # 메타데이터 생성
        word_count = len(article_content.content.replace(" ", ""))
        created_date = datetime.utcnow().isoformat() + "Z"
        
        # 응답 데이터 구성
        response = ColumnResponse(
            success=True,
            article=ArticleData(
                title=article_content.title,
                summary=article_content.summary,
                content=article_content.content,
                metadata=MetaData(
                    wordCount=word_count,
                    category="정치",
                    createdDate=created_date,
                    sources=article_content.sources
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