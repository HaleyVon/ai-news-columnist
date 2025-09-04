# AI 정치 컬럼니스트 FastAPI 서비스

OpenAI GPT-4o-mini API를 활용한 정치 컬럼 생성 서비스입니다. FastAPI + Python으로 구현되었으며, AWS Lambda에 최적화되어 있습니다.

## 🚀 주요 기능

- **AI 기반 정치 컬럼 생성**: OpenAI GPT-4o-mini API를 활용한 고품질 컬럼 생성
- **다중 관점 분석**: 진보/보수 관점을 균형있게 반영
- **품질 보증 시스템**: 자동 평가 및 반복 개선 프로세스
- **RESTful API**: JSON 기반 API 엔드포인트 제공
- **AWS Lambda 최적화**: 서버리스 환경에 최적화된 구조
- **보안 강화**: Rate limiting, 입력 검증, CORS 설정

## 📋 요구사항

- Python 3.11+
- OpenAI API 키
- AWS CLI (배포시)
- Node.js 18+ (Serverless Framework 사용시)

## 🛠 설치 및 설정

### 1. 저장소 클론
```bash
git clone <repository-url>
cd ai-political-columnist
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\\Scripts\\activate  # Windows
```

### 3. 패키지 설치
```bash
# 프로덕션 의존성 설치
pip install -r requirements.txt

# 또는 개발 의존성 포함 설치
make install
```

### 4. 환경 변수 설정
```bash
# 환경 변수 파일 생성
cp .env.example .env

# .env 파일에 API 키 설정
OPENAI_API_KEY=your_openai_api_key_here
```

## 🏃‍♂️ 실행 방법

### 개발 서버 실행
```bash
# 방법 1: Make 명령어 사용
make dev

# 방법 2: 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 방법 3: Python 모듈로 실행
python main.py
```

서버가 실행되면 다음 URL에서 접근 가능합니다:
- API 문서: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 헬스 체크: http://localhost:8000/health

## 📡 API 사용법

### 컬럼 생성 요청
```bash
curl -X POST \"http://localhost:8000/api/generate-column\" \\
  -H \"Content-Type: application/json\" \\
  -d '{
    \"topic\": \"최근 대선 여론조사 결과 분석\",
    \"maxRevisionAttempts\": 3
  }'
```

### 응답 예시
```json
{
  \"success\": true,
  \"article\": {
    \"title\": \"2024 대선 여론조사, 무엇을 말하는가?\",
    \"summary\": \"최근 여론조사 결과를 통해 본 유권자 동향과 정치적 함의\",
    \"content\": \"...전체 컬럼 내용...\",
    \"metadata\": {
      \"wordCount\": 1250,
      \"category\": \"정치\",
      \"createdDate\": \"2024-01-01T00:00:00Z\",
      \"sources\": [
        {
          \"title\": \"중앙선거여론조사심의위원회 결과\",
          \"uri\": \"https://example.com/poll-results\"
        }
      ]
    }
  },
  \"processedDate\": \"2024-01-01T00:00:00Z\"
}
```

## 🧪 테스트

### 모든 테스트 실행
```bash
make test
```

### 코드 커버리지 포함 테스트
```bash
make test-cov
```

### 단위 테스트만 실행
```bash
make test-unit
```

## 🔍 코드 품질 관리

### 코드 포맷팅
```bash
make format
```

### 린트 검사
```bash
make lint
```

### 전체 검증 (포맷팅 + 린트 + 테스트)
```bash
make validate
```

## 🚀 배포

### Serverless Framework 배포

1. **Serverless Framework 설치**
```bash
npm install -g serverless
npm install --save-dev serverless-python-requirements
```

2. **AWS 인증 설정**
```bash
aws configure
```

3. **개발 환경 배포**
```bash
make deploy-dev
```

4. **프로덕션 환경 배포**
```bash
make deploy-prod
```

### AWS SAM 배포 (대안)

1. **SAM CLI 설치**
```bash
# macOS
brew install aws/tap/aws-sam-cli

# 다른 OS는 공식 문서 참조
```

2. **빌드 및 배포**
```bash
make sam-deploy-dev  # 개발 환경
make sam-deploy-prod # 프로덕션 환경
```

## 📊 모니터링

### 로그 확인
```bash
# 개발 환경 로그
make logs-dev

# 프로덕션 환경 로그
make logs-prod
```

### 서비스 상태 확인
```bash
make status
```

## 🗂 프로젝트 구조

```
ai-political-columnist/
├── main.py                 # FastAPI 애플리케이션 메인 파일
├── schemas.py              # Pydantic 스키마 정의
├── requirements.txt        # Python 패키지 의존성
├── serverless.yml         # Serverless Framework 설정
├── pyproject.toml         # Python 프로젝트 설정
├── Makefile               # 자동화 스크립트
├── .env.example           # 환경 변수 예제
├──
├── core/                  # 핵심 설정 및 예외 처리
│   ├── __init__.py
│   ├── config.py          # 애플리케이션 설정
│   └── exceptions.py      # 커스텀 예외 클래스
├──
├── services/              # 비즈니스 로직 서비스
│   ├── __init__.py
│   ├── gemini_service.py  # OpenAI API 서비스 (파일명 유지)
│   └── prompts.py         # AI 프롬프트 관리
├──
├── middleware/            # 미들웨어
│   ├── __init__.py
│   └── security.py        # 보안 미들웨어
├──
└── tests/                 # 테스트 코드
    ├── __init__.py
    ├── test_main.py
    ├── test_services.py
    └── conftest.py
```

## ⚙️ 환경 변수

| 변수명 | 필수 | 기본값 | 설명 |
|--------|------|--------|------|
| `OPENAI_API_KEY` | ✅ | - | OpenAI API 키 |
| `ENVIRONMENT` | ❌ | development | 환경 설정 |
| `RATE_LIMIT_PER_MINUTE` | ❌ | 5 | 분당 요청 제한 |
| `MAX_REQUEST_SIZE` | ❌ | 1048576 | 최대 요청 크기 (바이트) |
| `LAMBDA_TIMEOUT` | ❌ | 300 | Lambda 타임아웃 (초) |
| `LAMBDA_MEMORY_SIZE` | ❌ | 1024 | Lambda 메모리 크기 (MB) |

## 🛡 보안 기능

- **Rate Limiting**: 분당 요청 수 제한
- **입력 검증**: Pydantic을 활용한 엄격한 데이터 검증
- **CORS 설정**: 허용된 도메인만 접근 가능
- **요청 크기 제한**: 대용량 요청 차단
- **보안 헤더**: XSS, CSRF 등 공격 방어
- **에러 메시지 정화**: 민감정보 노출 방지

## 📈 성능 최적화

- **Cold Start 최소화**: Mangum ASGI 어댑터 사용
- **메모리 최적화**: Lambda 메모리 크기 조정
- **응답 캐싱**: 정적 리소스 캐싱
- **비동기 처리**: async/await 패턴 활용

## 🔧 문제 해결

### 일반적인 문제들

1. **OpenAI API 키 오류**
   ```
   해결방법: .env 파일에 올바른 API 키 설정 확인
   ```

2. **포트 충돌**
   ```bash
   # 다른 포트로 실행
   uvicorn main:app --port 8001
   ```

3. **패키지 설치 오류**
   ```bash
   # 가상환경 재생성
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### 로그 확인
```bash
# 개발 서버 로그는 콘솔에 출력됩니다
# Lambda 환경에서는 CloudWatch Logs 확인
```

## 🤝 기여 방법

1. Fork 저장소
2. Feature 브랜치 생성 (`git checkout -b feature/새기능`)
3. 변경사항 커밋 (`git commit -am '새기능 추가'`)
4. 브랜치 Push (`git push origin feature/새기능`)
5. Pull Request 생성

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 있습니다. 자세한 내용은 LICENSE 파일을 참조하세요.

## 🙋‍♂️ 지원

- **Issues**: GitHub Issues를 통해 버그 리포트나 기능 요청
- **Discussions**: 일반적인 질문이나 토론
- **Documentation**: 추가 문서는 `/docs` 폴더 참조

---

**참고**: 이 서비스는 교육 및 데모 목적으로 제작되었습니다. 실제 운영 환경에서 사용하기 전에 보안 검토를 받으시기 바랍니다.