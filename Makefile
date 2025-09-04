# AI 정치 컬럼니스트 프로젝트 Makefile
# 개발 및 배포 자동화 스크립트

.PHONY: help install dev test lint format check clean deploy

# 기본 타겟
help: ## 도움말 표시
	@echo "AI 정치 컬럼니스트 프로젝트 명령어:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# 환경 설정
install: ## 패키지 의존성 설치
	pip install --upgrade pip
	pip install -r requirements.txt

install-prod: ## 프로덕션 의존성만 설치
	pip install --upgrade pip
	pip install -r requirements.txt --no-dev

# 개발 서버
dev: ## 개발 서버 실행
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-debug: ## 디버그 모드로 개발 서버 실행
	uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# 코드 품질
format: ## 코드 포맷팅 (Black + isort)
	black .
	isort .

lint: ## 코드 린트 검사 (flake8 + mypy)
	flake8 .
	mypy .

check: format lint ## 포맷팅 + 린트 검사 실행

# 테스트
test: ## 단위 테스트 실행
	pytest tests/ -v

test-cov: ## 커버리지 포함 테스트 실행
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

test-unit: ## 단위 테스트만 실행
	pytest tests/ -v -m "unit"

test-integration: ## 통합 테스트만 실행
	pytest tests/ -v -m "integration"

# 빌드 및 검증
validate: check test ## 전체 코드 검증 (포맷팅 + 린트 + 테스트)

build-check: ## 빌드 전 검증
	@echo "빌드 전 검증 시작..."
	@echo "1. 코드 포맷팅 검사"
	black --check .
	@echo "2. Import 정렬 검사"
	isort --check-only .
	@echo "3. 린트 검사"
	flake8 .
	@echo "4. 타입 체크"
	mypy .
	@echo "5. 테스트 실행"
	pytest tests/ -q
	@echo "빌드 전 검증 완료 ✓"

# 환경 변수 검사
check-env: ## 필수 환경 변수 검사
	@echo "환경 변수 검사 중..."
	@if [ -z "$(OPENAI_API_KEY)" ]; then \
		echo "❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다."; \
		exit 1; \
	else \
		echo "✅ OPENAI_API_KEY 설정됨"; \
	fi
	@echo "환경 변수 검사 완료"

# 배포 준비
deploy-check: build-check check-env ## 배포 전 전체 검증

# Serverless 배포
deploy-dev: deploy-check ## 개발 환경 배포
	serverless deploy --stage dev

deploy-prod: deploy-check ## 프로덕션 환경 배포
	serverless deploy --stage prod

# AWS SAM 배포 (대안)
sam-build: ## SAM 빌드
	sam build

sam-deploy-dev: sam-build ## SAM 개발 환경 배포
	sam deploy --parameter-overrides Environment=dev

sam-deploy-prod: sam-build ## SAM 프로덕션 환경 배포
	sam deploy --parameter-overrides Environment=prod

# 정리
clean: ## 임시 파일 정리
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/

clean-all: clean ## 모든 임시 파일 및 환경 정리
	rm -rf .venv/
	rm -rf venv/
	rm -rf node_modules/

# 문서 생성
docs: ## API 문서 생성 (개발 서버 실행 필요)
	@echo "API 문서는 http://localhost:8000/docs 에서 확인 가능합니다"
	@echo "개발 서버 실행: make dev"

# 로그 확인
logs-dev: ## 개발 환경 로그 확인
	serverless logs -f api --stage dev -t

logs-prod: ## 프로덕션 환경 로그 확인
	serverless logs -f api --stage prod -t

# 데이터베이스 관리 (향후 확장용)
db-migrate: ## 데이터베이스 마이그레이션
	@echo "현재 데이터베이스를 사용하지 않습니다"

db-reset: ## 데이터베이스 리셋
	@echo "현재 데이터베이스를 사용하지 않습니다"

# 보안 검사
security-check: ## 보안 취약점 검사
	pip install safety bandit
	safety check
	bandit -r . -x tests/

# 성능 테스트
perf-test: ## 성능 테스트 (locust 필요)
	@echo "성능 테스트를 위해서는 locust 설치가 필요합니다: pip install locust"
	@echo "테스트 스크립트: locustfile.py"

# 상태 확인
status: ## 서비스 상태 확인
	@echo "서비스 상태 확인 중..."
	curl -s http://localhost:8000/health || echo "서비스가 실행되지 않고 있습니다"

# 컨테이너 관리 (향후 Docker 지원용)
docker-build: ## Docker 이미지 빌드
	@echo "Docker 지원은 향후 추가될 예정입니다"

docker-run: ## Docker 컨테이너 실행
	@echo "Docker 지원은 향후 추가될 예정입니다"