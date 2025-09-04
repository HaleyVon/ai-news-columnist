"""
커스텀 예외 클래스 정의
애플리케이션에서 사용하는 커스텀 예외들
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException


class CustomHTTPException(HTTPException):
    """커스텀 HTTP 예외 클래스"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class ValidationException(CustomHTTPException):
    """입력 검증 예외"""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(
            status_code=400,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )
        self.field = field


class OpenAIAPIException(CustomHTTPException):
    """OpenAI API 관련 예외"""
    
    def __init__(self, detail: str = "AI 서비스 오류가 발생했습니다."):
        super().__init__(
            status_code=503,
            detail=detail,
            error_code="OPENAI_API_ERROR"
        )


# 호환성을 위한 alias
GeminiAPIException = OpenAIAPIException


class RateLimitException(CustomHTTPException):
    """Rate Limit 예외"""
    
    def __init__(self, detail: str = "요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요."):
        super().__init__(
            status_code=429,
            detail=detail,
            error_code="RATE_LIMIT_EXCEEDED"
        )


class ContentGenerationException(CustomHTTPException):
    """컨텐츠 생성 예외"""
    
    def __init__(self, detail: str = "컨텐츠 생성 중 오류가 발생했습니다."):
        super().__init__(
            status_code=500,
            detail=detail,
            error_code="CONTENT_GENERATION_ERROR"
        )


class NewsSearchException(CustomHTTPException):
    """뉴스 검색 예외"""
    
    def __init__(self, detail: str = "뉴스 검색 중 오류가 발생했습니다."):
        super().__init__(
            status_code=503,
            detail=detail,
            error_code="NEWS_SEARCH_ERROR"
        )