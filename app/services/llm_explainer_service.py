from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass

from app.core.config import get_settings
from app.integrations.llm_client import LLMClientError, LLMCompletionRequest, generate_text

logger = logging.getLogger("energypredict.llm")
_llm_failures = 0
_llm_circuit_open_until = 0.0


@dataclass(frozen=True)
class LLMExplanationResult:
    recommendation: str
    provider: str
    model: str
    prompt_version: str
    notes: str | None = None


def build_operations_recommendation(payload: dict, failure_probability: float, risk_level: str, trace_id: str = "n/a") -> str:
    result = build_operations_explanation(payload, failure_probability, risk_level, trace_id)
    return result.recommendation


def build_operations_explanation(payload: dict, failure_probability: float, risk_level: str, trace_id: str = "n/a") -> LLMExplanationResult:
    global _llm_failures, _llm_circuit_open_until
    settings = get_settings()
    fallback = LLMExplanationResult(
        recommendation=_fallback_recommendation(risk_level),
        provider=settings.llm_provider,
        model=settings.llm_model,
        prompt_version="v1",
        notes="fallback",
    )

    if settings.llm_provider == "disabled":
        return fallback

    if not settings.llm_endpoint or not settings.llm_api_key:
        logger.warning(json.dumps({"trace_id": trace_id, "event": "llm_skipped_missing_config"}))
        return fallback

    now = time.time()
    if settings.llm_circuit_breaker_enabled and now < _llm_circuit_open_until:
        logger.warning(json.dumps({"trace_id": trace_id, "event": "llm_circuit_open", "until": _llm_circuit_open_until}))
        return fallback

    prompt = _build_prompt(payload, failure_probability, risk_level)
    attempts = max(1, int(settings.llm_retry_attempts))
    last_error: LLMClientError | None = None

    for attempt in range(1, attempts + 1):
        try:
            recommendation = generate_text(
                LLMCompletionRequest(
                    endpoint=settings.llm_endpoint,
                    model=settings.llm_model,
                    api_key=settings.llm_api_key,
                    prompt=prompt,
                    timeout_seconds=settings.llm_timeout_seconds,
                )
            )
            _llm_failures = 0
            _llm_circuit_open_until = 0.0
            logger.info(
                json.dumps(
                    {
                        "trace_id": trace_id,
                        "event": "llm_success",
                        "risk_level": risk_level,
                        "attempt": attempt,
                    }
                )
            )
            return LLMExplanationResult(
                recommendation=recommendation,
                provider=settings.llm_provider,
                model=settings.llm_model,
                prompt_version="v1",
                notes=None,
            )
        except LLMClientError as exc:
            last_error = exc
            _llm_failures += 1
            logger.warning(
                json.dumps(
                    {
                        "trace_id": trace_id,
                        "event": "llm_attempt_failed",
                        "attempt": attempt,
                        "error": str(exc)[:200],
                    }
                )
            )
            if attempt < attempts and settings.llm_retry_backoff_seconds > 0:
                time.sleep(settings.llm_retry_backoff_seconds * attempt)

    if settings.llm_circuit_breaker_enabled and _llm_failures >= int(settings.llm_circuit_breaker_failures):
        _llm_circuit_open_until = time.time() + max(1, int(settings.llm_circuit_breaker_reset_seconds))
        logger.warning(
            json.dumps(
                {
                    "trace_id": trace_id,
                    "event": "llm_circuit_opened",
                    "failures": _llm_failures,
                    "until": _llm_circuit_open_until,
                }
            )
        )

    logger.warning(
        json.dumps(
            {
                "trace_id": trace_id,
                "event": "llm_fallback",
                "error": str(last_error)[:200] if last_error else "unknown",
            }
        )
    )
    return fallback


def _build_prompt(payload: dict, failure_probability: float, risk_level: str) -> str:
    return (
        "Given the telemetry and model outcome, provide a short operations recommendation (max 2 sentences). "
        "Focus on concrete maintenance actions and urgency.\n"
        f"Asset: {payload.get('asset_code', 'unknown')}\n"
        f"Failure probability: {failure_probability:.4f}\n"
        f"Risk level: {risk_level}\n"
        f"Telemetry: {json.dumps(payload, ensure_ascii=True)}"
    )


def _fallback_recommendation(risk_level: str) -> str:
    if risk_level == "low":
        return "Keep normal maintenance schedule and continue routine monitoring."
    if risk_level == "medium":
        return "Plan a preventive inspection within 7 days and monitor trend changes."
    return "Execute inspection within 24 hours and prioritize vibration/temperature diagnostics."
