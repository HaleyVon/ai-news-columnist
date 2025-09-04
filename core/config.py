"""
애플리케이션 설정 관리
환경변수와 설정값들을 중앙에서 관리
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # API 키 설정
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    naver_client_id: str = os.getenv("NAVER_CLIENT_ID", "")
    naver_client_secret: str = os.getenv("NAVER_CLIENT_SECRET", "")
    
    # 환경 설정
    environment: str = os.getenv("ENVIRONMENT", "development")
    is_production: bool = os.getenv("ENVIRONMENT") == "production"
    
    # CORS 설정
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:8000",
        "https://localhost:3000",
        "https://ai.studio"  # AI Studio 도메인
    ]
    
    # API 설정
    api_title: str = "AI 정치 컬럼니스트 API"
    api_version: str = "1.0.0"
    
    # Rate Limiting 설정
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "5"))
    
    # 요청 크기 제한 (바이트)
    max_request_size: int = int(os.getenv("MAX_REQUEST_SIZE", "1048576"))  # 1MB
    
    # Lambda 설정
    lambda_timeout: int = int(os.getenv("LAMBDA_TIMEOUT", "300"))  # 5분
    lambda_memory_size: int = int(os.getenv("LAMBDA_MEMORY_SIZE", "1024"))  # 1GB
    
    # 컬럼 생성 설정
    max_column_length: int = int(os.getenv("MAX_COLUMN_LENGTH", "5000"))
    min_column_length: int = int(os.getenv("MIN_COLUMN_LENGTH", "500"))
    default_revision_attempts: int = int(os.getenv("DEFAULT_REVISION_ATTEMPTS", "3"))
    
    # 로깅 설정
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 필수 환경변수 검증
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        
        # 프로덕션 환경에서 추가 검증
        if self.is_production:
            if self.environment != "production":
                raise ValueError("프로덕션 환경에서는 ENVIRONMENT=production 이어야 합니다.")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 추가 필드 허용


# 전역 설정 인스턴스
settings = Settings()