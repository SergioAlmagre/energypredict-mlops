from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import RiskThresholdAudit, RiskThresholdPolicy


@dataclass(frozen=True)
class RiskThresholds:
    low_max: float
    medium_max: float


def validate_thresholds(low_max: float, medium_max: float) -> None:
    if low_max < 0 or medium_max < 0:
        raise ValueError("Thresholds must be >= 0.")
    if low_max >= medium_max:
        raise ValueError("low_max must be lower than medium_max.")
    if medium_max > 1:
        raise ValueError("medium_max must be <= 1.")


def get_or_create_active_policy(db: Session) -> RiskThresholdPolicy:
    policy = (
        db.query(RiskThresholdPolicy)
        .filter(RiskThresholdPolicy.is_active.is_(True))
        .order_by(RiskThresholdPolicy.updated_at.desc())
        .first()
    )
    if policy:
        return policy

    settings = get_settings()
    validate_thresholds(settings.risk_threshold_low_max_default, settings.risk_threshold_medium_max_default)
    policy = RiskThresholdPolicy(
        low_max=settings.risk_threshold_low_max_default,
        medium_max=settings.risk_threshold_medium_max_default,
        is_active=True,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def get_active_thresholds(db: Session) -> RiskThresholds:
    policy = get_or_create_active_policy(db)
    return RiskThresholds(low_max=policy.low_max, medium_max=policy.medium_max)


def update_active_thresholds(db: Session, changed_by_user_id: str, low_max: float, medium_max: float) -> RiskThresholdPolicy:
    validate_thresholds(low_max, medium_max)
    policy = get_or_create_active_policy(db)

    audit = RiskThresholdAudit(
        policy_id=policy.id,
        previous_low_max=policy.low_max,
        previous_medium_max=policy.medium_max,
        new_low_max=low_max,
        new_medium_max=medium_max,
        changed_by_user_id=changed_by_user_id,
    )
    db.add(audit)

    policy.low_max = low_max
    policy.medium_max = medium_max
    policy.updated_by_user_id = changed_by_user_id
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy
