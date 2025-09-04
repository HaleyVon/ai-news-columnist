"""
메인 애플리케이션 테스트
API 엔드포인트 및 전체적인 애플리케이션 동작을 테스트
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status


class TestHealthEndpoint:
    """헬스 체크 엔드포인트 테스트"""
    
    @pytest.mark.unit
    def test_health_check_success(self, client):
        """헬스 체크 성공 테스트"""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    @pytest.mark.unit
    def test_health_check_response_format(self, client):
        """헬스 체크 응답 형식 테스트"""
        response = client.get("/health")
        data = response.json()
        
        # 응답 구조 검증
        assert isinstance(data, dict)
        assert len(data) == 2
        assert isinstance(data["timestamp"], str)


class TestGenerateColumnEndpoint:
    """컬럼 생성 엔드포인트 테스트"""
    
    @pytest.mark.unit
    @patch('main.gemini_service.generate_column')
    def test_generate_column_success(self, mock_generate, client, sample_column_request, mock_gemini_service):
        """컬럼 생성 성공 테스트"""
        # Mock 설정
        mock_generate.return_value = mock_gemini_service.generate_column.return_value
        
        response = client.post("/api/generate-column", json=sample_column_request)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # 응답 구조 검증
        assert data["success"] is True
        assert "article" in data
        assert "processedDate" in data
        
        # 아티클 구조 검증
        article = data["article"]
        assert "title" in article
        assert "summary" in article
        assert "content" in article
        assert "metadata" in article
        
        # 메타데이터 구조 검증
        metadata = article["metadata"]
        assert "wordCount" in metadata
        assert "category" in metadata
        assert "createdDate" in metadata
    
    @pytest.mark.unit
    def test_generate_column_invalid_requests(self, client, invalid_column_requests):
        """유효하지 않은 요청 테스트"""
        for invalid_request in invalid_column_requests:
            response = client.post("/api/generate-column", json=invalid_request)
            
            # 400 (Bad Request) 또는 422 (Validation Error) 상태 코드 예상
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
    
    @pytest.mark.unit
    def test_generate_column_missing_content_type(self, client, sample_column_request):
        """Content-Type 헤더 누락 테스트"""
        response = client.post(
            "/api/generate-column",
            data=str(sample_column_request),  # JSON이 아닌 문자열로 전송
            headers={"Content-Type": "text/plain"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.unit
    def test_generate_column_empty_body(self, client):
        """빈 요청 본문 테스트"""
        response = client.post("/api/generate-column", json={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.unit
    @patch('main.gemini_service.generate_column')
    def test_generate_column_service_error(self, mock_generate, client, sample_column_request):
        """서비스 에러 처리 테스트"""
        # Mock에서 예외 발생시키기
        mock_generate.side_effect = Exception("OpenAI API 오류")
        
        response = client.post("/api/generate-column", json=sample_column_request)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["success"] is False
        assert "error" in data
    
    @pytest.mark.unit
    def test_generate_column_camelcase_response(self, client, mock_gemini_service):
        """응답이 camelCase 형식인지 테스트"""
        with patch('main.gemini_service.generate_column', return_value=mock_gemini_service.generate_column.return_value):
            response = client.post("/api/generate-column", json={
                "topic": "테스트 주제",
                "maxRevisionAttempts": 2
            })
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            # camelCase 필드명 확인
            assert "processedDate" in data
            article = data["article"]
            metadata = article["metadata"]
            assert "wordCount" in metadata
            assert "createdDate" in metadata


class TestCORSAndSecurity:
    """CORS 및 보안 테스트"""
    
    @pytest.mark.unit
    def test_cors_headers_present(self, client, sample_column_request):
        """CORS 헤더 존재 확인"""
        response = client.options("/api/generate-column", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        })
        
        # CORS 헤더 확인
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
    
    @pytest.mark.unit
    def test_security_headers_present(self, client):
        """보안 헤더 존재 확인"""
        response = client.get("/health")
        
        # 보안 헤더 확인
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers
        assert "x-xss-protection" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"


class TestRateLimiting:
    """Rate Limiting 테스트"""
    
    @pytest.mark.unit
    def test_rate_limit_headers(self, client):
        """Rate Limit 관련 헤더 확인"""
        response = client.get("/health")
        
        # 응답에 처리 시간 헤더 확인
        assert "x-process-time" in response.headers
    
    @pytest.mark.slow
    def test_rate_limit_enforcement(self, client, sample_column_request):
        """Rate Limit 적용 테스트 (실제 환경에서는 스킵)"""
        # 이 테스트는 실제 rate limiting 설정에 따라 조정 필요
        pytest.skip("Rate limiting test requires specific configuration")


class TestErrorHandling:
    """에러 처리 테스트"""
    
    @pytest.mark.unit
    def test_404_not_found(self, client):
        """존재하지 않는 엔드포인트 테스트"""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.unit  
    def test_405_method_not_allowed(self, client):
        """허용되지 않은 HTTP 메서드 테스트"""
        response = client.put("/api/generate-column")
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    @pytest.mark.unit
    def test_413_request_entity_too_large(self, client):
        """요청 크기 제한 테스트"""
        # 매우 큰 요청 데이터
        large_topic = "A" * 10000  # 10KB 텍스트
        response = client.post("/api/generate-column", json={
            "topic": large_topic,
            "maxRevisionAttempts": 3
        })
        
        # 요청 크기에 따라 413 또는 422 응답 가능
        assert response.status_code in [
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


class TestAPIDocumentation:
    """API 문서 테스트"""
    
    @pytest.mark.unit
    def test_openapi_schema_available(self, client):
        """OpenAPI 스키마 접근 테스트"""
        response = client.get("/openapi.json")
        
        # 개발 환경에서만 접근 가능
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND  # 프로덕션에서는 비활성화
        ]
    
    @pytest.mark.unit
    def test_docs_endpoint(self, client):
        """문서 엔드포인트 접근 테스트"""
        response = client.get("/docs")
        
        # 개발 환경에서만 접근 가능
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND  # 프로덕션에서는 비활성화
        ]