"""
보안 관련 미들웨어
요청 크기 제한, 입력 검증, 보안 헤더 등을 처리
"""

import time
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import settings
from core.exceptions import ValidationException
from schemas import ErrorResponse


class SecurityMiddleware(BaseHTTPMiddleware):
    """보안 미들웨어"""
    
    def __init__(self, app, max_request_size: int = None):
        super().__init__(app)
        self.max_request_size = max_request_size or settings.max_request_size
    
    async def dispatch(self, request: Request, call_next: Callable):
        """요청 처리 및 보안 검사"""
        
        # 1. 요청 크기 제한 검사
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            return JSONResponse(
                status_code=413,
                content=ErrorResponse(
                    success=False,
                    error=f"요청 크기가 너무 큽니다. 최대 {self.max_request_size // 1024}KB까지 허용됩니다.",
                    processedDate=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                ).model_dump()
            )
        
        # 2. User-Agent 검사 (봇 차단)
        user_agent = request.headers.get("user-agent", "").lower()
        suspicious_agents = ["bot", "crawler", "spider", "scraper"]
        if any(agent in user_agent for agent in suspicious_agents):
            # 로깅만 하고 차단하지는 않음 (검색엔진 봇도 필요할 수 있음)
            pass
        
        # 3. 요청 처리
        response = await call_next(request)
        
        # 4. 보안 헤더 추가
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 프로덕션 환경에서만 HSTS 헤더 추가
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """입력 데이터 정화 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        """요청 데이터 정화"""
        
        # POST 요청에 대한 추가 검증
        if request.method == "POST":
            # Content-Type 검사
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                return JSONResponse(
                    status_code=400,
                    content=ErrorResponse(
                        success=False,
                        error="Content-Type은 application/json이어야 합니다.",
                        processedDate=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    ).model_dump()
                )
        
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """요청 로깅 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        """요청/응답 로깅"""
        start_time = time.time()
        
        # 요청 정보 수집 (민감정보 제외)
        request_info = {
            "method": request.method,
            "url": str(request.url.path),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "")[:200]  # 길이 제한
        }
        
        # 응답 처리
        response = await call_next(request)
        
        # 처리 시간 계산
        process_time = time.time() - start_time
        
        # 로그 출력 (프로덕션에서는 구조화된 로깅 사용 권장)
        if settings.log_level == "DEBUG" or response.status_code >= 400:
            print(f"{request_info['method']} {request_info['url']} - "
                  f"Status: {response.status_code} - Time: {process_time:.3f}s")
        
        # 응답 헤더에 처리 시간 추가
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 주소 추출"""
        # 프록시 뒤에 있을 경우를 고려하여 헤더에서 IP 추출
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"