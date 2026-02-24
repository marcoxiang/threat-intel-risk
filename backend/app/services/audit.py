from sqlalchemy.orm import Session

from app.models.entities import AuditEvent


def record_audit(
    db: Session,
    actor: str,
    action: str,
    target_type: str,
    target_id: str,
    before_json: dict | None = None,
    after_json: dict | None = None,
) -> None:
    db.add(
        AuditEvent(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            before_json=before_json,
            after_json=after_json,
        )
    )
