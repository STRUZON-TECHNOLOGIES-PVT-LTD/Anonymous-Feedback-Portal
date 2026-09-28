"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("text", sa.String(500), nullable=False),
        sa.Column("type", sa.String(30), nullable=False, server_default="single_choice"),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("confession_text", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("platform", sa.String(100), nullable=True),
        sa.Column("screen_resolution", sa.String(30), nullable=True),
        sa.Column("timezone", sa.String(100), nullable=True),
        sa.Column("language", sa.String(30), nullable=True),
        sa.Column("device_fingerprint", sa.String(64), nullable=True),
    )
    op.create_index("ix_submissions_device_fingerprint", "submissions", ["device_fingerprint"])

    op.create_table(
        "answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "submission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("selected_option", sa.String(200), nullable=False),
    )

    op.create_table(
        "extracted_names",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "submission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("normalized_name", sa.String(200), nullable=False),
    )
    op.create_index("ix_extracted_names_normalized_name", "extracted_names", ["normalized_name"])


def downgrade() -> None:
    op.drop_table("extracted_names")
    op.drop_table("answers")
    op.drop_table("submissions")
    op.drop_table("admins")
    op.drop_table("questions")
