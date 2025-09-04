"""
요약 길이 제한(<=300자) 가드 테스트
"""

import pytest
from unittest.mock import patch, MagicMock

from services.content_generation_service import ContentGenerationService
from services.prompts import PromptGenerator


@pytest.mark.unit
@pytest.mark.asyncio
async def test_extract_title_and_summary_clamps_to_300_chars():
    """extract_title_and_summary가 300자 이내로 요약을 제한하는지 검증"""
    long_paragraph = "가" * 800
    content = f"""
## 제목입니다

{long_paragraph}

## 다음 섹션
""".strip()

    svc = ContentGenerationService(api_key="test")
    title, summary = await svc.extract_title_and_summary(content)

    assert isinstance(summary, str)
    assert len(summary) <= 300
    assert len(title) > 0


@pytest.mark.unit
def test_api_response_summary_is_clamped(client):
    """API 응답 조립 단계에서도 요약이 300자 이내로 보장되는지 검증"""
    overlong_summary = "나" * 1200

    with patch("main.gemini_service.generate_column", return_value=MagicMock(
        title="테스트 제목",
        summary=overlong_summary,
        content=("본문" * 200),
        sources=[]
    )):
        resp = client.post("/api/generate-column", json={
            "topic": "요약 길이 제한 테스트",
            "maxRevisionAttempts": 2
        })

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["article"]["summary"]) <= 300


@pytest.mark.unit
def test_prompt_includes_summary_300_rule():
    pg = PromptGenerator()
    prompt = pg.get_draft_prompt_with_news("테스트 주제", news_summary="요약", news_sources=[])
    assert "최대 300자" in prompt or "300자 이내" in prompt


