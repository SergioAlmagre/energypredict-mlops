import pytest

from app.integrations.llm_client import LLMClientError, LLMCompletionRequest, generate_text


def test_generate_text_success(monkeypatch):
    class _Response:
        status_code = 200

        @staticmethod
        def json():
            return {"choices": [{"message": {"content": "Action recommendation"}}]}

    monkeypatch.setattr("app.integrations.llm_client.requests.post", lambda *args, **kwargs: _Response())
    text = generate_text(
        LLMCompletionRequest(
            endpoint="https://llm.example.com/v1/chat/completions",
            model="test-model",
            api_key="secret",
            prompt="prompt",
        )
    )
    assert text == "Action recommendation"


def test_generate_text_http_error(monkeypatch):
    class _Response:
        status_code = 500
        text = "server error"

    monkeypatch.setattr("app.integrations.llm_client.requests.post", lambda *args, **kwargs: _Response())
    with pytest.raises(LLMClientError):
        generate_text(
            LLMCompletionRequest(
                endpoint="https://llm.example.com/v1/chat/completions",
                model="test-model",
                api_key="secret",
                prompt="prompt",
            )
        )


def test_generate_text_bad_payload(monkeypatch):
    class _Response:
        status_code = 200

        @staticmethod
        def json():
            return {"unexpected": "payload"}

    monkeypatch.setattr("app.integrations.llm_client.requests.post", lambda *args, **kwargs: _Response())
    with pytest.raises(LLMClientError):
        generate_text(
            LLMCompletionRequest(
                endpoint="https://llm.example.com/v1/chat/completions",
                model="test-model",
                api_key="secret",
                prompt="prompt",
            )
        )
