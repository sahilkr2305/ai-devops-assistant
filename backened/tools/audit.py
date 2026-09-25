import json
from datetime import datetime

from database.database import SessionLocal
from database.models import AuditLog


def create_audit_log(
    action: str,
    tool: str,
    arguments: dict | None = None,
    status: str = "unknown",
    result: str | None = None,
    project_id: int | None = None,
    approval_id: str | None = None,
):
    """
    Create a permanent audit record for a DevOps action.
    """

    db = SessionLocal()

    try:
        audit_log = AuditLog(
            project_id=project_id,
            approval_id=approval_id,
            action=action,
            tool=tool,
            arguments=json.dumps(
                arguments or {},
                ensure_ascii=False,
            ),
            status=status,
            result=result,
            created_at=datetime.utcnow(),
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        return {
            "id": audit_log.id,
            "project_id": audit_log.project_id,
            "approval_id": audit_log.approval_id,
            "action": audit_log.action,
            "tool": audit_log.tool,
            "arguments": arguments or {},
            "status": audit_log.status,
            "result": audit_log.result,
            "created_at": (
                audit_log.created_at.isoformat()
                if audit_log.created_at
                else None
            ),
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def get_audit_logs(
    project_id: int | None = None,
    limit: int = 100,
):
    """
    Retrieve recent audit logs.

    If project_id is supplied, only logs for that
    project are returned.
    """

    db = SessionLocal()

    try:
        # Prevent unnecessarily large queries
        limit = min(max(limit, 1), 500)

        query = (
            db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
        )

        if project_id is not None:
            query = query.filter(
                AuditLog.project_id == project_id
            )

        logs = query.limit(limit).all()

        result = []

        for log in logs:
            try:
                arguments = json.loads(
                    log.arguments or "{}"
                )
            except (json.JSONDecodeError, TypeError):
                arguments = {}

            result.append({
                "id": log.id,
                "project_id": log.project_id,
                "approval_id": log.approval_id,
                "action": log.action,
                "tool": log.tool,
                "arguments": arguments,
                "status": log.status,
                "result": log.result,
                "created_at": (
                    log.created_at.isoformat()
                    if log.created_at
                    else None
                ),
            })

        return result

    finally:
        db.close()
