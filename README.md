# 🏛️ AI 정치 컬럼니스트

> OpenAI gpt-4.1-mini API를 활용한 균형잡힌 정치 컬럼 생성 서비스  
> FastAPI + Python 기반, AWS Lambda 서버리스 아키텍처

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-00a393.svg)](https://fastapi.tiangolo.com)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991.svg)](https://platform.openai.com)

</div>

## 📋 목차

- [프로젝트 개요](#-프로젝트-개요)
- [아키텍처 개요](#-아키텍처-개요)
- [주요 기능](#-주요-기능)
- [시스템 요구사항](#-시스템-요구사항)
- [개발 환경 설정](#-개발-환경-설정)
- [로컬 실행 방법](#-로컬-실행-방법)
- [API 사용법](#-api-사용법)
- [개발 가이드](#-개발-가이드)
- [배포 가이드](#-배포-가이드)
- [문제 해결](#-문제-해결)
- [프로젝트 구조](#-프로젝트-구조)

---

## 🎯 프로젝트 개요

AI 정치 컬럼니스트는 **OpenAI gpt-4.1-mini API**를 활용하여 정치적 주제에 대해 균형잡힌 시각의 고품질 컬럼을 자동 생성하는 서비스입니다.

### 🔥 핵심 특징
- **균형잡힌 관점**: 진보/보수 양측 시각을 공정하게 반영
- **품질 보증 시스템**: AI 기반 자동 평가 및 반복 개선 프로세스
- **최신 정보 활용**: 네이버 뉴스 API 연동으로 실시간 정보 반영
- **서버리스 아키텍처**: AWS Lambda 최적화로 비용 효율적 운영

---

## 🏗 아키텍처 개요

- 시스템 플로우차트와 데이터 구조 다이어그램은 다음 문서에서 확인하세요:
  - [시스템 개요 및 데이터 구조](docs/architecture/system_overview.md)

---

## ✨ 주요 기능

### 🤖 AI 기반 컬럼 생성
- OpenAI gpt-4.1-mini 모델 활용
- 다단계 품질 검증 프로세스
- 자동 제목/요약 생성

### 📊 다중 관점 분석
- 진보적 관점과 보수적 관점 균형 반영
- 객관적 분석과 논증 구조 제공
- 최신 뉴스 데이터 기반 정보 제공

### 🛡️ 강력한 보안
- Rate Limiting (분당 5회 제한)
- 입력 데이터 검증 및 정화
- CORS 설정 및 보안 헤더
- 요청 크기 제한 (1MB)

### ⚡ 고성능 아키텍처
- AWS Lambda 최적화
- Cold Start 최소화
- 비동기 처리 지원
- 자동 스케일링

---

## 💻 시스템 요구사항

### 필수 요구사항
- **Python 3.11** 이상
- **OpenAI API 키** ([발급받기](https://platform.openai.com))
- **pip** (Python 패키지 관리자)

### 배포용 추가 요구사항
- **AWS CLI** ([설치 가이드](https://docs.aws.amazon.com/ko_kr/cli/latest/userguide/install-cliv2.html))
- **Node.js 18+** (Serverless Framework 사용시)
- **AWS 계정** 및 적절한 IAM 권한

---

## 🔧 개발 환경 설정

### 1️⃣ 저장소 클론
```bash
git clone https://github.com/your-username/ai-news-columnist.git
cd ai-news-columnist
```

### 2️⃣ Python 가상환경 생성
```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate  # macOS/Linux
# 또는
.\\venv\\Scripts\\activate  # Windows
```

### 3️⃣ 패키지 설치
```bash
# 방법 1: Makefile 사용 (권장)
make install

# 방법 2: pip 직접 사용
pip install --upgrade pip
pip install -r requirements.txt
```

### 4️⃣ 환경 변수 설정
```bash
# 환경 변수 템플릿 복사
cp .env.example .env

# .env 파일 편집 (필수!)
vim .env
# 또는
nano .env
```

**⚠️ 중요: .env 파일에 반드시 다음 설정 추가**
```bash
# .env 파일 내용
OPENAI_API_KEY=your_actual_openai_api_key_here
ENVIRONMENT=development
```

### 5️⃣ 설치 확인
```bash
# Python 및 패키지 버전 확인
python --version  # Python 3.11+ 확인
pip list | grep fastapi  # FastAPI 설치 확인

# 환경 변수 확인
python -c "from core.config import settings; print('설정 로드 성공:', settings.openai_api_key[:10] + '...' if settings.openai_api_key else '❌ API 키 누락')"
```

---

## 🚀 로컬 실행 방법

### 개발 서버 시작
```bash
# 방법 1: Makefile 사용 (권장)
make dev

# 방법 2: uvicorn 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 방법 3: Python 모듈로 실행
python main.py
```

### 서버 실행 확인
서버가 성공적으로 시작되면 다음과 같은 출력을 볼 수 있습니다:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
```

### 접근 가능한 URL
- **API 문서**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc (대안 문서)
- **헬스 체크**: http://localhost:8000/health

---

## 📡 API 사용법

### 기본 헬스 체크
```bash
curl http://localhost:8000/health
```

**응답 예시:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### 정치 컬럼 생성 요청
```bash
curl -X POST "http://localhost:8000/api/generate-column" \\
  -H "Content-Type: application/json" \\
  -d '{
    "topic": "최근 대선 여론조사 결과에 대한 분석",
    "maxRevisionAttempts": 3
  }'
```

### 응답 구조
```json
{
  "success": true,
  "article": {
    "title": "2024 대선 여론조사가 보여주는 민심의 변화",
    "summary": "최근 여론조사 결과를 통해 본 유권자 동향과 정치적 함의를 균형있게 분석",
    "content": "...전체 컬럼 내용...",
    "metadata": {
      "wordCount": 1547,
      "category": "정치",
      "createdDate": "2024-01-15T10:35:20.456Z",
      "sources": [
        {
          "title": "중앙선거여론조사심의위원회 공식 발표",
          "uri": "https://example.com/poll-results"
        }
      ]
    }
  },
  "processedDate": "2024-01-15T10:35:20.456Z"
}
```

### 요청 파라미터 상세
| 필드 | 타입 | 필수 | 설명 | 예시 |
|------|------|------|------|------|
| `topic` | string | ✅ | 컬럼 주제 (2-200자) | "부동산 정책 변화 분석" |
| `maxRevisionAttempts` | number | ❌ | 최대 수정 횟수 (1-5) | 3 (기본값) |

---

## 🛠 개발 가이드

### 코드 품질 관리
```bash
# 코드 포맷팅 (Black + isort)
make format

# 린트 검사 (flake8 + mypy)
make lint

# 전체 코드 검증 (포맷팅 + 린트 + 테스트)
make validate
```

### 테스트 실행
```bash
# 전체 테스트 실행
make test

# 커버리지 포함 테스트
make test-cov

# 단위 테스트만 실행
make test-unit

# 특정 테스트 파일 실행
pytest tests/test_main.py -v

# 특정 테스트 케이스 실행
pytest tests/test_main.py::TestHealthEndpoint::test_health_check_success -v
```

### 개발 시 주의사항

**✅ DO (권장사항)**
- 모든 함수/클래스에 한국어 docstring 작성
- 타입 힌트 필수 사용 (`typing` 모듈)
- Pydantic 모델로 데이터 검증
- 환경변수로 민감정보 관리
- 로깅 활용 (`logger.info()`, `logger.error()`)

**❌ DON'T (금지사항)**
- API 키 등 민감정보 코드에 하드코딩 금지
- `print()` 사용 지양 (로깅 사용)
- 예외 처리 없는 외부 API 호출 금지
- 테스트 코드 없는 새 기능 추가 금지

### 새로운 기능 추가 절차
1. **브랜치 생성**: `git checkout -b feature/새기능명`
2. **개발**: 기능 구현 + 테스트 코드 작성
3. **코드 검증**: `make validate` 통과 확인
4. **문서 업데이트**: API 스키마/README 수정
5. **PR 생성**: 코드 리뷰 요청

---

## 🚀 배포 가이드

### Serverless Framework 배포

#### 1️⃣ Serverless 설치
```bash
npm install -g serverless
npm install --save-dev serverless-python-requirements
```

#### 2️⃣ AWS 인증 설정
```bash
# AWS CLI 설정
aws configure
# Access Key, Secret Key, Region(ap-northeast-2) 입력

# 또는 환경변수로 설정
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=ap-northeast-2
```

#### 3️⃣ 배포 전 검증
```bash
# 배포 전 전체 검증 (필수!)
make deploy-check
```

#### 4️⃣ 환경별 배포
```bash
# 개발 환경 배포
make deploy-dev

# 프로덕션 환경 배포  
make deploy-prod

# 수동 배포 (환경 지정)
serverless deploy --stage dev
serverless deploy --stage prod
```

### 배포 후 확인
```bash
# API Gateway URL 확인
serverless info --stage dev

# 로그 확인
make logs-dev
# 또는
serverless logs -f api --stage dev -t

# 헬스 체크
curl https://your-api-gateway-url/health
```

### AWS SAM 배포 (대안)
```bash
# SAM 빌드
make sam-build

# 개발 환경 배포
make sam-deploy-dev

# 프로덕션 환경 배포
make sam-deploy-prod
```

---

## 🔍 문제 해결

### 자주 발생하는 문제들

#### 1️⃣ OpenAI API 키 오류
**증상**: `ValueError: OpenAI API 키가 제공되지 않았습니다`

**해결방법**:
```bash
# .env 파일 확인
cat .env | grep OPENAI_API_KEY

# 환경변수 직접 설정
export OPENAI_API_KEY=your_api_key_here

# 설정 확인
python -c "import os; print('API Key:', os.getenv('OPENAI_API_KEY', 'NOT_SET'))"
```

#### 2️⃣ 포트 충돌 오류
**증상**: `OSError: [Errno 48] Address already in use`

**해결방법**:
```bash
# 8000 포트 사용 프로세스 확인
lsof -i :8000

# 프로세스 종료
kill -9 <PID>

# 다른 포트로 실행
uvicorn main:app --port 8001
```

#### 3️⃣ 패키지 설치 오류
**증상**: `pip install` 실패

**해결방법**:
```bash
# 가상환경 재생성
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# pip 업그레이드
pip install --upgrade pip setuptools wheel

# 패키지 재설치
pip install -r requirements.txt
```

#### 4️⃣ AWS 배포 오류
**증상**: `AccessDenied` 또는 권한 오류

**해결방법**:
```bash
# AWS 인증 정보 확인
aws sts get-caller-identity

# 필요한 IAM 권한:
# - AWSLambdaFullAccess
# - IAMFullAccess  
# - AmazonAPIGatewayAdministrator
# - CloudFormationFullAccess
```

#### 5️⃣ 테스트 실패
**증상**: `pytest` 실행 시 오류

**해결방법**:
```bash
# 테스트 환경 변수 설정 확인
export OPENAI_API_KEY=test_key_for_testing

# 테스트 의존성 설치
pip install pytest pytest-asyncio pytest-cov

# 개별 테스트 실행으로 문제 파악
pytest tests/test_main.py::TestHealthEndpoint -v
```

### 로그 및 디버깅
```bash
# 애플리케이션 로그 (개발 모드)
# 콘솔에 실시간 출력됨

# 상세 로그 활성화
export LOG_LEVEL=DEBUG
make dev-debug

# AWS CloudWatch 로그 (배포된 환경)
make logs-dev
make logs-prod
```

---

## 📁 프로젝트 구조

```
ai-news-columnist/
├── 📄 main.py                  # FastAPI 메인 애플리케이션
├── 📄 schemas.py               # Pydantic 데이터 모델 정의
├── 📄 requirements.txt         # Python 패키지 의존성
├── 📄 pyproject.toml          # Python 프로젝트 설정
├── 📄 serverless.yml          # Serverless Framework 설정
├── 📄 Makefile                # 개발/배포 자동화 스크립트
├── 📄 .env.example            # 환경변수 템플릿
├── 📄 .flake8                 # Linting 설정
├── 📄 README.md               # 프로젝트 문서 (이 파일)
├── 📄 CLAUDE.md               # Claude Code 가이드
│
├── 📁 core/                   # 핵심 설정 및 유틸리티
│   ├── 📄 __init__.py
│   ├── 📄 config.py           # 환경설정 관리 (pydantic-settings)
│   └── 📄 exceptions.py       # 커스텀 예외 클래스
│
├── 📁 services/               # 비즈니스 로직 서비스
│   ├── 📄 __init__.py
│   ├── 📄 gemini_service.py   # OpenAI API 연동 (파일명 유지)
│   └── 📄 prompts.py          # AI 프롬프트 관리
│
├── 📁 middleware/             # 미들웨어
│   ├── 📄 __init__.py
│   └── 📄 security.py         # 보안, 로깅, 검증 미들웨어
│
├── 📁 tests/                  # 테스트 코드
│   ├── 📄 __init__.py
│   ├── 📄 conftest.py         # pytest 설정 및 픽스처
│   └── 📄 test_main.py        # 메인 API 테스트
│
└── 📁 venv/                   # Python 가상환경 (gitignore)
```

### 주요 파일별 역할

| 파일/디렉토리 | 역할 | 수정 빈도 |
|---------------|------|-----------|
| `main.py` | FastAPI 앱 설정, 라우터, 미들웨어 | 🟡 보통 |
| `schemas.py` | API 요청/응답 데이터 모델 | 🟡 보통 |
| `services/gemini_service.py` | AI 컬럼 생성 핵심 로직 (OpenAI 사용) | 🔴 높음 |
| `services/prompts.py` | AI 프롬프트 템플릿 | 🔴 높음 |
| `core/config.py` | 환경설정 관리 | 🟢 낮음 |
| `tests/` | 자동화된 테스트 코드 | 🟡 보통 |
| `serverless.yml` | AWS 배포 설정 | 🟢 낮음 |

---

## 🤝 개발팀 협업 가이드

### Git 브랜치 전략
```bash
# 메인 브랜치
main          # 프로덕션 배포용
develop       # 개발 통합 브랜치

# 기능 개발
feature/컬럼생성개선    # 새 기능 개발
feature/api최적화      # 성능 개선
bugfix/오류수정        # 버그 수정
```

### 코드 리뷰 체크리스트
- [ ] 한국어 주석 및 docstring 작성
- [ ] 타입 힌트 추가
- [ ] 테스트 코드 포함
- [ ] `make validate` 통과
- [ ] 환경변수 사용 (하드코딩 금지)
- [ ] API 스키마 문서 업데이트

### 커밋 메시지 규칙
```bash
feat: 새로운 컬럼 평가 기준 추가
fix: OpenAI API 응답 파싱 오류 수정  
docs: API 사용법 문서 업데이트
test: 컬럼 생성 통합 테스트 추가
refactor: 프롬프트 생성 로직 개선
```

---

## 📞 지원 및 연락처

### 문서 및 참고자료
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [OpenAI API 문서](https://platform.openai.com/docs)
- [Pydantic 가이드](https://docs.pydantic.dev/)
- [AWS Lambda Python 가이드](https://docs.aws.amazon.com/lambda/latest/dg/python-programming-model.html)

### 문제 보고 및 기여
- **GitHub Issues**: 버그 리포트, 기능 요청
- **GitHub Discussions**: 일반적인 질문, 아이디어 공유
- **Pull Requests**: 코드 기여, 문서 개선

---

<div align="center">

**⭐ 이 프로젝트가 도움이 되었다면 스타를 눌러주세요! ⭐**

---

*Made with ❤️ by AI Political Columnist Team*  
*© 2024 AI Political Columnist. MIT License.*

</div>