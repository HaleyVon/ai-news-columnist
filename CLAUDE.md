# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# 제공하는 코드나 설명은 항상 한국어로 명확하고 간결하며 이해하기 쉬운 언어로 설명합니다.
# 모든 코드에 개발 인수인계가 가능하도록 한국어 주석을 꼼꼼하게 추가합니다.

## Project Overview

This is an AI-powered political columnist service built with FastAPI + Python, designed to generate balanced political columns using OpenAI GPT-4o-mini API. The service is optimized for AWS Lambda deployment and follows serverless architecture patterns.

## Core Architecture

### Application Structure
- **main.py**: FastAPI application entry point with Mangum ASGI adapter for AWS Lambda
- **schemas.py**: Pydantic models defining API request/response schemas with strict validation
- **core/**: Configuration management and custom exception handling
  - `config.py`: Centralized settings using pydantic-settings with environment variable validation
  - `exceptions.py`: Custom HTTP exceptions with structured error responses
- **services/**: Business logic layer
  - `gemini_service.py`: OpenAI API integration with retry logic and content generation pipeline (파일명 유지)
  - `prompts.py`: AI prompt management and template generation
- **middleware/**: Request processing middleware
  - `security.py`: Security headers, request size limits, input sanitization, and logging

### Key Design Patterns
- **Service Layer Pattern**: Business logic separated into service classes (GeminiService)
- **Settings Pattern**: Environment-based configuration with validation using pydantic-settings
- **Middleware Chain**: Security, CORS, rate limiting, and request logging middleware stack
- **Exception Handling**: Custom exceptions with consistent error response format

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
make install
# or directly: pip install -r requirements.txt

# Environment configuration
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
```

### Development Server
```bash
make dev                    # Start development server with reload
make dev-debug             # Start with debug logging
uvicorn main:app --reload  # Direct uvicorn command
```

### Code Quality and Testing
```bash
make format      # Format code with Black + isort
make lint        # Run flake8 + mypy type checking
make validate    # Run format + lint + tests
make test        # Run all tests
make test-unit   # Run unit tests only
make test-cov    # Run tests with coverage report
```

### Single Test Execution
```bash
pytest tests/test_main.py::TestHealthEndpoint::test_health_check_success -v
pytest tests/ -k "test_generate_column" -v
```

### Build and Deployment
```bash
make build-check        # Pre-deployment validation
make deploy-dev         # Deploy to development (Serverless)
make deploy-prod        # Deploy to production (Serverless)
make sam-deploy-dev     # Alternative SAM deployment
```

## API Architecture

### Core Endpoint
- **POST /api/generate-column**: Main column generation endpoint
  - Input: `ColumnRequest` with topic and revision attempts
  - Output: `ColumnResponse` with nested article structure using camelCase
  - Process: Draft generation → Iterative evaluation/revision → Final content extraction

### Content Generation Pipeline
1. **Draft Generation**: Uses Naver News API integration for current information
2. **Quality Evaluation**: Automated scoring across 5 dimensions (format, balance, readability, completeness, objectivity)
3. **Iterative Revision**: Up to configurable attempts to meet quality thresholds
4. **Content Structuring**: Extracts title, summary, and sources for final response

### Response Structure
```json
{
  "success": boolean,
  "article": {
    "title": string,
    "summary": string, 
    "content": string,
    "metadata": {
      "wordCount": number,
      "category": string,
      "createdDate": string,
      "sources": [{"title": string, "uri": string}]
    }
  },
  "processedDate": string
}
```

## Configuration and Environment

### Required Environment Variables
- `OPENAI_API_KEY`: OpenAI API key (required)
- `ENVIRONMENT`: development/staging/production (affects logging, docs availability)

### Optional Configuration
- `RATE_LIMIT_PER_MINUTE`: API rate limiting (default: 5)
- `MAX_REQUEST_SIZE`: Request size limit in bytes (default: 1MB)
- `LAMBDA_TIMEOUT`: Function timeout for AWS Lambda (default: 300s)
- `MAX_COLUMN_LENGTH`: Maximum generated content length (default: 5000 chars)

### Security Features
- Rate limiting via slowapi
- Request size validation
- Input sanitization and validation via Pydantic
- CORS configuration for allowed origins
- Security headers (XSS protection, content sniffing prevention)
- Error message sanitization to prevent information leakage

## AWS Lambda Optimization

- **Mangum Adapter**: ASGI-to-AWS Lambda event handler
- **Cold Start Mitigation**: Optimized imports and service initialization
- **Memory Configuration**: 1GB default for AI API processing
- **Layer Support**: Python requirements packaged as Lambda layer
- **Serverless Framework**: Infrastructure as code with environment-specific deployments

## Testing Strategy

- **Unit Tests**: Fast, isolated tests for individual components
- **Integration Tests**: API endpoint testing with mocked external services
- **Test Fixtures**: Reusable test data and mock services in conftest.py
- **Coverage Targets**: 80% minimum code coverage requirement
- **Async Testing**: pytest-asyncio for testing async service methods