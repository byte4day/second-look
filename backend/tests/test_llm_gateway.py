import json
from unittest.mock import MagicMock, patch

from pydantic import BaseModel

from app.schemas.analyze import AnalyzeResult
from app.services import llm_gateway


class Tiny(BaseModel):
    ok: bool


def test_demo_fixture_path():
    out = llm_gateway.chat_structured(
        [{"role": "user", "content": "x"}],
        AnalyzeResult,
        demo_fixture_name="analyze_text.json",
    )
    assert out.risk_level == "likely_scam"


@patch("app.services.llm_gateway._client")
def test_retry_then_success(mock_client_factory):
    mock_client = MagicMock()
    mock_client_factory.return_value = mock_client
    err = Exception("rate")
    err.status_code = 429

    good = MagicMock()
    good.choices = [MagicMock(message=MagicMock(content=json.dumps({"ok": True})))]
    good.usage = MagicMock(completion_tokens=1)

    mock_client.chat.completions.create.side_effect = [err, good]

    with patch("app.services.llm_gateway.get_settings") as gs:
        settings = gs.return_value
        settings.demo_mode = False
        settings.llm_provider = "groq"
        settings.groq_api_key = "k"
        settings.groq_chat_model = "primary"
        settings.groq_fast_model = "fast"
        settings.rate_limit_llm_per_minute = 5

        with patch("time.sleep"):
            result = llm_gateway.chat_structured([{"role": "user", "content": "hi"}], Tiny)
    assert result.ok is True


@patch("app.services.llm_gateway._client")
def test_fallback_model(mock_client_factory):
    mock_client = MagicMock()
    mock_client_factory.return_value = mock_client

    fail = Exception("server")
    fail.status_code = 500
    good = MagicMock()
    good.choices = [MagicMock(message=MagicMock(content='{"ok": true}'))]
    good.usage = MagicMock(completion_tokens=1)

    mock_client.chat.completions.create.side_effect = [fail, fail, fail, fail, good]

    with patch("app.services.llm_gateway.get_settings") as gs:
        settings = gs.return_value
        settings.demo_mode = False
        settings.llm_provider = "groq"
        settings.groq_api_key = "k"
        settings.groq_chat_model = "primary"
        settings.groq_fast_model = "fast"
        settings.rate_limit_llm_per_minute = 5
        with patch("time.sleep"):
            result = llm_gateway.chat_structured(
                [{"role": "user", "content": "hi"}], Tiny, role="fast"
            )
    assert result.ok is True


@patch("app.services.llm_gateway._client")
def test_json_repair_path(mock_client_factory):
    mock_client = MagicMock()
    mock_client_factory.return_value = mock_client

    bad = MagicMock()
    bad.choices = [MagicMock(message=MagicMock(content="not-json"))]
    bad.usage = MagicMock(completion_tokens=1)
    good = MagicMock()
    good.choices = [MagicMock(message=MagicMock(content='{"ok": true}'))]
    good.usage = MagicMock(completion_tokens=1)

    mock_client.chat.completions.create.side_effect = [bad, good]

    with patch("app.services.llm_gateway.get_settings") as gs:
        settings = gs.return_value
        settings.demo_mode = False
        settings.llm_provider = "groq"
        settings.groq_api_key = "k"
        settings.groq_chat_model = "m"
        settings.groq_fast_model = ""
        settings.rate_limit_llm_per_minute = 5
        result = llm_gateway.chat_structured([{"role": "user", "content": "hi"}], Tiny)
    assert result.ok is True


def test_startup_demo_skips():
    from app.config import Settings

    assert llm_gateway.check_models_on_startup(Settings(demo_mode=True))["demo"] is True