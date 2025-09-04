"""
프롬프트 생성 및 관리
"""

from datetime import datetime
from typing import Dict, Any


class PromptGenerator:
    """프롬프트 생성 클래스"""
    
    def __init__(self):
        """프롬프트 생성기 초기화"""
        
        # 작성 규칙 정의
        self.writing_rules = """
- 정치 초보자도 이해할 수 있는 쉬운 용어와 설명으로 작성.
- 종결어미는 반드시 "~~이다."와 같은 보도문체를 사용해주세요.
- 본문 중 중요한 키워드들은 **단어** 형식으로 볼드 처리하여 가독성을 높여주세요.
- 마크다운 형식으로 작성해주세요: ## 대제목, ### 소제목, **강조**
- 진영별 입장 섹션에는 💬, 진보 진영에는 🔵, 보수 진영에는 🔴, 내용 섹션에는 🧨, 결론 섹션에는 📌 이모지를 사용해주세요.
- 진보 진영 입장과 보수 진영 입장은 반드시 각각 3개의 bullet point로 구성해야 합니다. 각 bullet point는 '- '로 시작해야 하며, 반드시 줄바꿈으로 구분되어야 합니다.
- 논리적 흐름이 자연스럽고, 주제를 이해하기에 정보가 충분해야 합니다.
- 반드시 검색된 보도자료에 기반하여 편향되지 않은 서술을 유지하세요.
- 컬럼 작성 시 참고한 뉴스 자료의 링크를 맨 마지막에 반드시 포함해야 합니다.
- 진영 분류 시 다음 키워드를 참고하세요:
  * 진보: 민주당, 더불어민주당, 조국혁신당, 정청래, 정의당, 조국, 여당, 이재명 등
  * 보수: 국민의힘, 야당, 국힘, 이준석, 한동훈, 안철수, 개혁신당, 전한길, 장동혁, 나경원, 김문수, 윤석열 등
 - 요약(첫 번째 요약 단락)은 최대 300자 이내로 작성하세요. 300자를 초과하지 마세요.
        """.strip()
        
        # 템플릿 정의 (마크다운 형식)
        self.template = """
## 주제를 잘 드러내며 흥미를 유발하는 중립적인 제목

핵심 내용을 요약하여 최대 300자 이내로 간결하게 작성

## 💬 ((핵심 주제))에 대한 진영별 입장

### 🔵 진보 진영 입장
- (첫 번째 핵심 입장)
- (두 번째 핵심 입장)
- (세 번째 핵심 입장)

### 🔴 보수 진영 입장
- (첫 번째 핵심 입장)
- (두 번째 핵심 입장)
- (세 번째 핵심 입장)

## 🧨 흥미를 유발하는 중립적인 대제목
### 주제의 핵심 쟁점을 다루는 소제목

해당 주제에서 핵심이 되는 내용을 정리. 핵심 내용들을 각각 넘버링하고 하위 불릿포인트로 정리하여 요약과 이해가 쉽도록 구성

## 📌 결론: ((핵심 주제))의 핵심과 전망

300~400자 내외

---

## 참고 자료

### 📰 전체 내용 참고 뉴스
- [뉴스 제목](뉴스 URL)
- [뉴스 제목](뉴스 URL)

### 🎯 진영별 입장 참고 뉴스
- [뉴스 제목](뉴스 URL)
- [뉴스 제목](뉴스 URL)
        """.strip()
        
        # 평가 기준 정의
        self.evaluation_criteria = """
1. 양식 준수 (Format Compliance):
    - 정해진 템플릿 구조(제목, 요약, 진영별 입장, 내용, 결론)를 모두 포함하고 있는가?
    - <진보 진영 입장>과 <보수 진영 입장>에 각각 정확히 3개의 bullet point가 포함되었는가?
    - 글자 수, 단락 구성 등 기술적 규칙을 준수하였는가?
2. 콘텐츠 품질 (Content Quality):
    - 균형성 (Balance): 진보와 보수, 양측 진영의 입장이 편향 없이 공정하게 제시되었는가?
    - 가독성 (Readability): 정치 초보자도 이해할 수 있는 쉬운 용어와 설명으로 작성되었는가?
    - 완성도 (Completeness): 논리적 흐름이 자연스럽고, 주제를 이해하기에 정보가 충분한가?
    - 객관성 (Objectivity): 사실에 기반하여 편향되지 않은 서술을 유지하고 있는가?
        """.strip()
    

    def get_draft_prompt_with_news(self, topic: str, news_summary: str, news_sources=None) -> str:
        """
        뉴스 정보를 포함한 초안 생성 프롬프트
        
        Args:
            topic: 컬럼 주제
            news_summary: 수집된 뉴스 정보 요약
            
        Returns:
            str: 뉴스 기반 초안 생성 프롬프트
        """
        # 현재 날짜 정보 가져오기 (사용하지 않지만 향후 확장 가능)
        
        # 템플릿에 주제 적용
        formatted_template = self.template.format(topic=topic)
        
        # 뉴스 소스 정보 포맷팅
        sources_text = ""
        if news_sources:
            sources_text = "\n\n[참고 뉴스 소스]\n"
            for i, source in enumerate(news_sources, 1):
                sources_text += f"{i}. [{source.get('title', 'N/A')}]({source.get('link', source.get('url', '#'))})\n"
        
        return f"""
다음 최신 뉴스 정보를 바탕으로 '{topic}'에 대한 컬럼 콘텐츠를 작성해주세요.

[최신 뉴스 정보]
{news_summary}{news_sources}{sources_text}

[작성 규칙]
{self.writing_rules}

[템플릿]
{formatted_template}

**중요**: 위 뉴스 정보를 활용하여 최신 동향과 구체적인 사실을 반영한 컬럼을 작성해주세요.
반드시 진보와 보수 진영의 입장은 실제 뉴스에서 언급된 내용을 바탕으로 작성해주세요.

**뉴스 링크 참조 요구사항**:
- 컬럼의 맨 마지막에 "## 참고 자료" 섹션을 반드시 추가하세요.
- "### 📰 전체 내용 참고 뉴스"와 "### 🎯 진영별 입장 참고 뉴스"로 구분하여 링크를 표기하세요.
- 각 링크는 [뉴스 제목](뉴스 URL) 형식으로 작성하세요.
- 전체 내용에 사용된 뉴스와 특정 진영 입장에 사용된 뉴스를 구분해서 표기하세요.
        """.strip()

    def get_revision_prompt(self, content: str) -> str:
        """
        평가 및 수정을 위한 프롬프트
        
        Args:
            content: 평가할 컨텐츠
            
        Returns:
            str: 평가 및 수정 프롬프트
        """
        return f"""
당신은 콘텐츠 품질 관리 AI입니다. 주어진 컬럼 원고가 아래 [평가 기준]을 충족하는지 검토하고, 지정된 JSON 형식으로 응답해주세요.

[평가 기준]
{self.evaluation_criteria}

[평가 프로세스]
1. 각 항목을 0점에서 100점 사이로 채점합니다.
2. 모든 항목의 점수가 85점 이상이면 'pass'를 true로 설정합니다. 하나라도 85점 미만이면 'pass'를 false로 설정합니다.
3. 'pass'가 false일 경우, 가장 점수가 낮은 항목을 중심으로 구체적인 개선 방향을 'feedback'에 작성합니다. 'pass'가 true일 경우, 칭찬의 말을 'feedback'에 작성합니다.
4. 'feedback'을 바탕으로 원고를 수정하여 'revisedContent'에 담아주세요. 만약 'pass'가 true라면, 원본 원고를 그대로 'revisedContent'에 담아주세요.

[컬럼 원고]
{content}
        """.strip()

    def get_title_summary_prompt(self, content: str) -> str:
        """
        제목과 요약 추출을 위한 프롬프트
        
        Args:
            content: 컨텐츠
            
        Returns:
            str: 제목/요약 추출 프롬프트
        """
        return f"""
다음 정치 컬럼에서 적절한 제목과 요약을 추출해주세요.

컨텐츠:
{content}

요구사항:
- 제목: 흥미롭고 내용을 잘 표현
- 요약: 핵심 내용을 간결하게 정리

JSON 형식으로 응답해주세요:
{{
    "title": "<제목>",
    "summary": "<요약>"
}}
        """.strip()

    def get_evaluation_schema(self) -> Dict[str, Any]:
        """
        평가 결과를 위한 JSON 스키마
        
        Returns:
            Dict[str, Any]: JSON 스키마
        """
        return {
            "type": "object",
            "properties": {
                "scores": {
                    "type": "object",
                    "properties": {
                        "format": {"type": "number", "description": "양식 준수 점수 (0-100)"},
                        "balance": {"type": "number", "description": "균형성 점수 (0-100)"},
                        "readability": {"type": "number", "description": "가독성 점수 (0-100)"},
                        "completeness": {"type": "number", "description": "완성도 점수 (0-100)"},
                        "objectivity": {"type": "number", "description": "객관성 점수 (0-100)"}
                    },
                    "required": ["format", "balance", "readability", "completeness", "objectivity"]
                },
                "pass": {"type": "boolean", "description": "모든 점수가 85점 이상이면 true"},
                "feedback": {"type": "string", "description": "개선이 필요한 경우 구체적인 피드백, 통과 시 칭찬"},
                "revisedContent": {"type": "string", "description": "피드백을 바탕으로 수정된 최종 원고"}
            },
            "required": ["scores", "pass", "feedback", "revisedContent"]
        }