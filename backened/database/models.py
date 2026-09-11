from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from database.database import Base


# ============================================================
# PROJECT
# ============================================================

class Project(Base):
    __tablename__ = "projects"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        Text,
        nullable=False,
        unique=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    messages = relationship(
        "ChatMessage",
        back_populates="project",
        cascade="all, delete-orphan"
    )


# ============================================================
# CHAT MESSAGE
# ============================================================

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )

    user_message = Column(
        Text,
        nullable=False
    )

    ai_response = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    project = relationship(
        "Project",
        back_populates="messages"
    )


# ============================================================
# APPROVAL REQUEST
# ============================================================

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    # Unique approval ID
    id = Column(
        Text,
        primary_key=True
    )

    # Project that created this approval
    project_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    # Action requested by the AI
    action = Column(
        Text,
        nullable=False
    )

    # Human-readable description
    description = Column(
        Text,
        nullable=False
    )

    # Tool that will be executed
    tool = Column(
        Text,
        nullable=False
    )

    # Arguments passed to the tool
    arguments = Column(
        Text,
        nullable=False,
        default="{}"
    )

    # Approval lifecycle:
    #
    # pending
    #    ↓
    # approved / rejected / expired
    #    ↓
    # executed
    #
    status = Column(
        Text,
        nullable=False,
        default="pending"
    )

    # When approval was created
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # When user approved the action
    approved_at = Column(
        DateTime,
        nullable=True
    )

    # When the approved action was executed
    executed_at = Column(
        DateTime,
        nullable=True
    )

    # When approval becomes invalid
    expires_at = Column(
        DateTime,
        nullable=True
    )


# ============================================================
# AUDIT LOG
# ============================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Project associated with the action
    project_id = Column(
        Integer,
        nullable=True,
        index=True
    )

    # Approval associated with the action
    approval_id = Column(
        Text,
        nullable=True,
        index=True
    )

    # Action name
    action = Column(
        Text,
        nullable=False
    )

    # Tool that was used
    tool = Column(
        Text,
        nullable=False
    )

    # Tool arguments
    arguments = Column(
        Text,
        nullable=False,
        default="{}"
    )

    # Execution status
    #
    # approval_required
    # success
    # failed
    # approved_and_executed
    # execution_failed
    #
    status = Column(
        Text,
        nullable=False
    )

    # Tool output or error
    result = Column(
        Text,
        nullable=True
    )

    # When the action was recorded
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )