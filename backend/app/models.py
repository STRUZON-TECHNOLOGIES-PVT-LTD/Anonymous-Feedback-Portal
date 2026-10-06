import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False, default="single_choice")
    options: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    active: Mapped[bool] = mapped_column(default=True)

    answers: Mapped[list["Answer"]] = relationship(back_populates="question")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    confession_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Device / request metadata captured for the admin log view.
    # NOTE: browsers do not expose OS username, machine name, or MAC address to web
    # pages under any circumstances - only IP (from the request) and browser-reported
    # signals below are actually obtainable. See README "Anonymity & device data" section.
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(100), nullable=True)
    screen_resolution: Mapped[str | None] = mapped_column(String(30), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str | None] = mapped_column(String(30), nullable=True)
    device_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    answers: Mapped[list["Answer"]] = relationship(back_populates="submission", cascade="all, delete-orphan")
    extracted_names: Mapped[list["ExtractedName"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE")
    )
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id"))
    selected_option: Mapped[str] = mapped_column(String(200), nullable=False)

    submission: Mapped[Submission] = relationship(back_populates="answers")
    question: Mapped[Question] = relationship(back_populates="answers")


class ExtractedName(Base):
    """Candidate person-name mentions found in confession_text, used to surface
    names that recur across many independent submissions (see name_extraction.py).
    This is a heuristic, not a guarantee - see README for its known limitations.
    """

    __tablename__ = "extracted_names"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    submission: Mapped[Submission] = relationship(back_populates="extracted_names")


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AdminSession(Base):
    """Server-side session record keyed by the JWT `jti`, so logout (and
    lockout/admin removal) actually invalidates a stolen token."""

    __tablename__ = "admin_sessions"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    admin_id: Mapped[int] = mapped_column(Integer, ForeignKey("admins.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")


class AuditLog(Base):
    """Who did what to which record. Logins and every read of submission data."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
