"""
Pytest 설정 및 공통 픽스처
테스트 환경 설정 및 재사용 가능한 테스트 도구들을 정의
"""

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

# 테스트 환경 변수 설정
os.environ["OPENAI_API_KEY"] = "test_api_key_for_testing"
os.environ["ENVIRONMENT"] = "testing"

from main import app
from services.gemini_service import GeminiService


@pytest.fixture
def client():
    """FastAPI 테스트 클라이언트 픽스처"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_gemini_service():
    """Mock된 Gemini 서비스 픽스처"""
    service = MagicMock(spec=GeminiService)
    
    # generate_column 메서드 모킹
    service.generate_column = AsyncMock()
    service.generate_column.return_value = MagicMock(
        title="테스트 컬럼 제목",
        summary="테스트 컬럼 요약입니다.",
        content="이것은 테스트용 컬럼 내용입니다. " * 50,  # 충분한 길이
        sources=[
            MagicMock(title="테스트 자료 1", uri="https://test1.com"),
            MagicMock(title="테스트 자료 2", uri="https://test2.com")
        ]
    )
    
    return service


@pytest.fixture
def sample_column_request():
    """샘플 컬럼 요청 데이터 픽스처"""
    return {
        "topic": "최근 대선 여론조사 결과에 대한 분석",
        "maxRevisionAttempts": 3
    }


@pytest.fixture
def sample_column_response():
    """샘플 컬럼 응답 데이터 픽스처"""
    return {
        "success": True,
        "article": {
            "title": "2024 대선 여론조사, 무엇을 말하는가?",
            "summary": "최근 여론조사 결과를 통해 본 유권자 동향과 정치적 함의",
            "content": "이것은 샘플 컬럼 내용입니다. " * 100,
            "metadata": {
                "wordCount": 1500,
                "category": "정치",
                "createdDate": "2024-01-01T00:00:00Z",
                "sources": [
                    {
                        "title": "중앙선거여론조사심의위원회 결과",
                        "uri": "https://example.com/poll-results"
                    }
                ]
            }
        },
        "processedDate": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def invalid_column_requests():
    """유효하지 않은 컬럼 요청 데이터들 픽스처"""
    return [
        # 빈 주제
        {"topic": "", "maxRevisionAttempts": 3},
        # 너무 짧은 주제
        {"topic": "A", "maxRevisionAttempts": 3},
        # 너무 긴 주제
        {"topic": "A" * 300, "maxRevisionAttempts": 3},
        # 유효하지 않은 수정 횟수
        {"topic": "테스트 주제", "maxRevisionAttempts": 0},
        {"topic": "테스트 주제", "maxRevisionAttempts": 10},
        # 누락된 필드
        {"maxRevisionAttempts": 3},
        # 부적절한 내용
        {"topic": "욕설이 포함된 주제", "maxRevisionAttempts": 3},
    ]


@pytest.fixture(autouse=True)
def setup_test_environment():
    """테스트 환경 자동 설정"""
    # 테스트 시작 전 설정
    original_env = os.environ.copy()
    
    # 테스트용 환경변수 설정
    os.environ.update({
        "ENVIRONMENT": "testing",
        "RATE_LIMIT_PER_MINUTE": "100",  # 테스트에서는 높은 제한
        "LOG_LEVEL": "WARNING"  # 테스트 로그 최소화
    })
    
    yield
    
    # 테스트 종료 후 원복
    os.environ.clear()
    os.environ.update(original_env)


# 마커 정의
pytest_plugins = []

def pytest_configure(config):
    """pytest 설정"""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests"
    )