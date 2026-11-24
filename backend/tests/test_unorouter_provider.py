from app.config import Settings
from app.services import llm_gateway


def _s(**kw) -> Settings:
    base = dict(demo_mode=False, unorouter_api_key="", groq_api_key="", llm_provider="auto")
    base.update(kw)
    return Settings(_env_file=None, **base)


def test_auto_prefers_unorouter_when_key_set():
    s = _s(unorouter_api_key="u", groq_api_key="g")
    assert llm_gateway.active_provider(s) == "unorouter"
    assert llm_gateway.provider_key(s) == "u"


def test_auto_falls_back_to_groq():
    s = _s(groq_api_key="g", groq_chat_model="llama")
    assert llm_gateway.active_provider(s) == "groq"
    assert llm_gateway._models_chain(s, "chat") == ["llama"]


def test_unorouter_client_uses_base_url():
    s = _s(unorouter_api_key="u", unorouter_base_url="https://api.unorouter.com/v1")
    client = llm_gateway._client(s)
    assert str(client.base_url).rstrip("/") == "https://api.unorouter.com/v1"


def test_unorouter_model_chain_dedupes_and_vision_has_no_text_fallback():
    s = _s(
        unorouter_api_key="u",
        unorouter_chat_model="m1",
        unorouter_fast_model="m1",
        unorouter_vision_model="",
    )
    assert llm_gateway._models_chain(s, "chat") == ["m1"]
    assert llm_gateway._models_chain(s, "vision") == []
    assert llm_gateway.vision_available(s) is False


def test_missing_key_reports_provider():
    s = _s(llm_provider="unorouter")
    out = llm_gateway.check_models_on_startup(s)
    assert out == {"ok": False, "provider": "unorouter", "error": "missing_api_key"}
