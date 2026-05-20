from app.services.llm_explainer_service import build_operations_recommendation


def test_llm_explainer_uses_fallback_when_disabled():
    payload = {"asset_code": "ASSET-001", "temperature": 92}
    text = build_operations_recommendation(payload=payload, failure_probability=0.83, risk_level="high")
    assert "inspection" in text.lower()


def test_llm_explainer_calls_llm_when_enabled(monkeypatch):
    from app.services import llm_explainer_service as svc

    class _Settings:
        llm_provider = "openai-compatible"
        llm_endpoint = "https://llm.example.com/v1/chat/completions"
        llm_api_key = "test-key"
        llm_model = "test-model"
        llm_timeout_seconds = 10
        llm_retry_attempts = 1
        llm_retry_backoff_seconds = 0
        llm_circuit_breaker_enabled = True
        llm_circuit_breaker_failures = 5
        llm_circuit_breaker_reset_seconds = 60

    monkeypatch.setattr(svc, "get_settings", lambda: _Settings())
    monkeypatch.setattr(svc, "generate_text", lambda req: f"LLM:{req.model}")

    text = svc.build_operations_recommendation(
        payload={"asset_code": "ASSET-001"},
        failure_probability=0.42,
        risk_level="medium",
    )
    assert text == "LLM:test-model"


def test_llm_explainer_fallback_on_llm_error(monkeypatch):
    from app.integrations.llm_client import LLMClientError
    from app.services import llm_explainer_service as svc

    class _Settings:
        llm_provider = "openai-compatible"
        llm_endpoint = "https://llm.example.com/v1/chat/completions"
        llm_api_key = "test-key"
        llm_model = "test-model"
        llm_timeout_seconds = 10
        llm_retry_attempts = 1
        llm_retry_backoff_seconds = 0
        llm_circuit_breaker_enabled = True
        llm_circuit_breaker_failures = 5
        llm_circuit_breaker_reset_seconds = 60

    monkeypatch.setattr(svc, "get_settings", lambda: _Settings())

    def _raise(_req):
        raise LLMClientError("boom")

    monkeypatch.setattr(svc, "generate_text", _raise)

    text = svc.build_operations_recommendation(
        payload={"asset_code": "ASSET-001"},
        failure_probability=0.91,
        risk_level="high",
    )
    assert "inspection" in text.lower()


def test_llm_explainer_retries_then_succeeds(monkeypatch):
    from app.integrations.llm_client import LLMClientError
    from app.services import llm_explainer_service as svc

    class _Settings:
        llm_provider = "openai-compatible"
        llm_endpoint = "https://llm.example.com/v1/chat/completions"
        llm_api_key = "test-key"
        llm_model = "test-model"
        llm_timeout_seconds = 10
        llm_retry_attempts = 3
        llm_retry_backoff_seconds = 0
        llm_circuit_breaker_enabled = True
        llm_circuit_breaker_failures = 5
        llm_circuit_breaker_reset_seconds = 60

    monkeypatch.setattr(svc, "get_settings", lambda: _Settings())
    monkeypatch.setattr(svc, "_llm_failures", 0)
    monkeypatch.setattr(svc, "_llm_circuit_open_until", 0.0)
    calls = {"n": 0}

    def _flaky(_req):
        calls["n"] += 1
        if calls["n"] < 3:
            raise LLMClientError("temporary error")
        return "Recovered recommendation"

    monkeypatch.setattr(svc, "generate_text", _flaky)

    text = svc.build_operations_recommendation(
        payload={"asset_code": "ASSET-010"},
        failure_probability=0.66,
        risk_level="medium",
    )
    assert text == "Recovered recommendation"
    assert calls["n"] == 3


def test_llm_explainer_circuit_breaker_opens_after_repeated_failures(monkeypatch):
    from app.integrations.llm_client import LLMClientError
    from app.services import llm_explainer_service as svc

    class _Settings:
        llm_provider = "openai-compatible"
        llm_endpoint = "https://llm.example.com/v1/chat/completions"
        llm_api_key = "test-key"
        llm_model = "test-model"
        llm_timeout_seconds = 10
        llm_retry_attempts = 1
        llm_retry_backoff_seconds = 0
        llm_circuit_breaker_enabled = True
        llm_circuit_breaker_failures = 2
        llm_circuit_breaker_reset_seconds = 60

    monkeypatch.setattr(svc, "get_settings", lambda: _Settings())
    monkeypatch.setattr(svc, "_llm_failures", 0)
    monkeypatch.setattr(svc, "_llm_circuit_open_until", 0.0)
    calls = {"n": 0}

    def _always_fail(_req):
        calls["n"] += 1
        raise LLMClientError("down")

    monkeypatch.setattr(svc, "generate_text", _always_fail)
    svc.build_operations_recommendation({"asset_code": "ASSET-011"}, 0.8, "high")
    svc.build_operations_recommendation({"asset_code": "ASSET-011"}, 0.8, "high")
    _ = svc.build_operations_recommendation({"asset_code": "ASSET-011"}, 0.8, "high")
    assert calls["n"] == 2
