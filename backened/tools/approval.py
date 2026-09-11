import json
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from database.database import SessionLocal
from database.models import ApprovalRequest


# Approval validity period
APPROVAL_EXPIRY_MINUTES = 10


def create_approval(
    project_id: int,
    action_name: str,
    description: str,
    tool_name: str,
    arguments: dict | None = None,
):
    """
    Create a pending approval request associated
    with a specific project.
    """

    approval_id = str(uuid.uuid4())

    now = datetime.utcnow()

    expires_at = (
        now
        + timedelta(
            minutes=APPROVAL_EXPIRY_MINUTES
        )
    )

    db: Session = SessionLocal()

    try:

        approval = ApprovalRequest(
            id=approval_id,
            project_id=project_id,
            action=action_name,
            description=description,
            tool=tool_name,
            arguments=json.dumps(
                arguments or {},
                ensure_ascii=False,
            ),
            status="pending",
            created_at=now,
            approved_at=None,
            executed_at=None,
            expires_at=expires_at,
        )

        db.add(approval)
        db.commit()
        db.refresh(approval)

        return approval_to_dict(
            approval
        )

    finally:
        db.close()


def get_approval(
    approval_id: str
):
    """
    Get an approval by ID.

    Expired pending approvals are automatically
    marked as expired.
    """

    db: Session = SessionLocal()

    try:

        approval = (
            db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.id
                == approval_id
            )
            .first()
        )

        if not approval:
            return None

        # Automatically expire pending approvals
        if (
            approval.status == "pending"
            and approval.expires_at
            and datetime.utcnow()
            >= approval.expires_at
        ):

            approval.status = "expired"

            db.commit()
            db.refresh(approval)

        return approval_to_dict(
            approval
        )

    finally:
        db.close()


def approve_action(
    approval_id: str
):
    """
    Approve a pending action if it has not expired.
    """

    db: Session = SessionLocal()

    try:

        approval = (
            db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.id
                == approval_id
            )
            .first()
        )

        if not approval:
            return None

        # Do not modify processed approvals
        if approval.status != "pending":
            return approval_to_dict(
                approval
            )

        # Check expiration
        if (
            approval.expires_at
            and datetime.utcnow()
            >= approval.expires_at
        ):

            approval.status = "expired"

            db.commit()
            db.refresh(approval)

            return approval_to_dict(
                approval
            )

        approval.status = "approved"

        approval.approved_at = (
            datetime.utcnow()
        )

        db.commit()
        db.refresh(approval)

        return approval_to_dict(
            approval
        )

    finally:
        db.close()


def reject_action(
    approval_id: str
):
    """
    Reject a pending approval.
    """

    db: Session = SessionLocal()

    try:

        approval = (
            db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.id
                == approval_id
            )
            .first()
        )

        if not approval:
            return None

        # Do not modify processed approvals
        if approval.status != "pending":
            return approval_to_dict(
                approval
            )

        approval.status = "rejected"

        db.commit()
        db.refresh(approval)

        return approval_to_dict(
            approval
        )

    finally:
        db.close()


def can_execute_approval(
    approval_id: str,
    project_id: int | None = None,
):
    """
    Verify that an approval can be executed.

    Optional project_id prevents an approval from
    being executed against a different project.
    """

    db: Session = SessionLocal()

    try:

        approval = (
            db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.id
                == approval_id
            )
            .first()
        )

        if not approval:

            return (
                False,
                "Approval request not found."
            )

        # ----------------------------------------------------
        # Project binding
        # ----------------------------------------------------

        if (
            project_id is not None
            and approval.project_id
            != project_id
        ):

            return (
                False,
                "This approval does not belong "
                "to the specified project."
            )

        # ----------------------------------------------------
        # Replay protection
        # ----------------------------------------------------

        if approval.status == "executed":

            return (
                False,
                "This approval has already been executed."
            )

        # ----------------------------------------------------
        # Rejected
        # ----------------------------------------------------

        if approval.status == "rejected":

            return (
                False,
                "This approval was rejected."
            )

        # ----------------------------------------------------
        # Expired
        # ----------------------------------------------------

        if approval.status == "expired":

            return (
                False,
                "This approval has expired."
            )

        # ----------------------------------------------------
        # Must be approved
        # ----------------------------------------------------

        if approval.status != "approved":

            return (
                False,
                "Approval is required before execution."
            )

        # ----------------------------------------------------
        # Check expiration again
        # ----------------------------------------------------

        if (
            approval.expires_at
            and datetime.utcnow()
            >= approval.expires_at
        ):

            approval.status = "expired"

            db.commit()

            return (
                False,
                "This approval has expired."
            )

        return True, None

    finally:
        db.close()


def mark_executed(
    approval_id: str
):
    """
    Mark an approved action as executed.

    This prevents approval replay.
    """

    db: Session = SessionLocal()

    try:

        approval = (
            db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.id
                == approval_id
            )
            .first()
        )

        if not approval:
            return None

        # Only approved requests can become executed
        if approval.status != "approved":
            return approval_to_dict(
                approval
            )

        approval.status = "executed"

        approval.executed_at = (
            datetime.utcnow()
        )

        db.commit()
        db.refresh(approval)

        return approval_to_dict(
            approval
        )

    finally:
        db.close()


def delete_approval(
    approval_id: str
):
    """
    Delete an approval.

    Normally approvals should be retained for
    audit history, so deletion is not recommended.
    """

    db: Session = SessionLocal()

    try:

        approval = (
            db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.id
                == approval_id
            )
            .first()
        )

        if not approval:
            return None

        result = approval_to_dict(
            approval
        )

        db.delete(approval)
        db.commit()

        return result

    finally:
        db.close()


def approval_to_dict(
    approval
):
    """
    Convert ApprovalRequest into a JSON-safe dict.
    """

    try:

        arguments = json.loads(
            approval.arguments or "{}"
        )

    except Exception:

        arguments = {}

    return {
        "id": approval.id,

        "project_id": approval.project_id,

        "action": approval.action,

        "description": approval.description,

        "tool": approval.tool,

        "arguments": arguments,

        "status": approval.status,

        "created_at": (
            approval.created_at.isoformat()
            if approval.created_at
            else None
        ),

        "approved_at": (
            approval.approved_at.isoformat()
            if approval.approved_at
            else None
        ),

        "executed_at": (
            approval.executed_at.isoformat()
            if approval.executed_at
            else None
        ),

        "expires_at": (
            approval.expires_at.isoformat()
            if approval.expires_at
            else None
        ),
    }