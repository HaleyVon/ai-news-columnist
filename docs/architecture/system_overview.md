## 시스템 개요 및 데이터 구조

이 문서는 AI 정치 컬럼니스트 시스템의 요청 흐름과 핵심 데이터 모델을 시각화합니다.

### 시스템 플로우 (Request → Response)

```mermaid
flowchart TD
    A[Client] --> B[FastAPI /api/generate-column]
    B --> C[GeminiService.generate_column]
    C --> D[NaverNewsSearchService.search_recent_news]
    D --> E[convert_to_sources]
    C --> F[ContentGenerationService.generate_column_from_news]
    F --> G[ContentEvaluationService.evaluate_and_revise]
    G --> H{pass?}
    H -- 아니오 --> G
    H -- 예 --> I[ContentGenerationService.extract_title_and_summary]
    I --> J[Assemble ColumnResponse]
    J --> K[HTTP 200 Response]

    %% 주석: main.py → GeminiService → (News, Generation, Evaluation) → Response
```

핵심 흐름 요약
- 뉴스 수집: `NaverNewsSearchService.search_recent_news(topic)` → 관련성/최신성 필터
- 컬럼 생성: `ContentGenerationService.generate_column_from_news(topic, news_data)`
- 품질 평가/수정 반복: `ContentEvaluationService.evaluate_and_revise(content)` 루프
- 제목/요약 추출: `extract_title_and_summary(content)` (요약 ≤ 300자 가드)
- 응답 조립: `ColumnResponse`로 변환(CamelCase), `MetaData.sources` 정규화

### 데이터 모델 (schemas.py)

```mermaid
classDiagram
    class ColumnRequest {
      +string topic
      +int maxRevisionAttempts
    }

    class Source {
      +string title
      +string uri
    }

    class MetaData {
      +int wordCount
      +string category
      +string createdDate
      +List~Source~ sources
    }

    class ArticleData {
      +string title
      +string summary~<=300 chars~
      +string content
      +MetaData metadata
    }

    class ColumnResponse {
      +bool success
      +ArticleData article
      +string processedDate
    }

    class ErrorResponse {
      +bool success=false
      +string error
      +string processedDate
    }

    class EvaluationResult {
      +map~string,float~ scores
      +bool pass_
      +string feedback
      +string revisedContent
    }

    class GeneratedContent {
      +string title
      +string summary
      +string content
      +List~Source~ sources
    }

    ColumnResponse --> ArticleData
    ArticleData --> MetaData
    MetaData --> Source
```

### 다이어그램 보기 방법
- GitHub: 이 Markdown 파일은 GitHub에서 Mermaid를 자동 렌더링합니다.
- VS Code: "Markdown Preview Enhanced" 또는 "Mermaid Markdown Syntax Highlighting" 확장 설치 후 미리보기(⌘K V).
- CLI(선택): `@mermaid-js/mermaid-cli`(mmdc)로 PNG/SVG 내보내기.

### 변경 시 주의사항
- 요약(summary)은 300자 이내를 유지해야 합니다. 시스템은 로직/프롬프트/API 레이어에서 모두 가드합니다.
- `MetaData.sources`는 `{ title, uri }` 구조의 리스트를 유지하세요.

