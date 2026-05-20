from __future__ import annotations

from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class LLMCompletionRequest:
    endpoint: str
    model: str
    api_key: str
    prompt: str
    timeout_seconds: int = 20


class LLMClientError(RuntimeError):
    pass


def generate_text(request: LLMCompletionRequest) -> str:
    payload = {
        "model": request.model,
        "messages": [
            {"role": "system", "content": "You are an operations assistant for predictive maintenance."},
            {"role": "user", "content": request.prompt},
        ],
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {request.api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            request.endpoint,
            json=payload,
            headers=headers,
            timeout=request.timeout_seconds,
        )
    except requests.RequestException as exc:
        raise LLMClientError(f"LLM request failed: {exc}") from exc

    if response.status_code >= 400:
        raise LLMClientError(f"LLM request failed with status {response.status_code}: {response.text[:300]}")

    try:
        completion = response.json()
        return completion["choices"][0]["message"]["content"].strip()
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LLMClientError("LLM response payload was not in expected format.") from exc
