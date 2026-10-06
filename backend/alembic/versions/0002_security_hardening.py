"""login lockout, server-side sessions, audit log

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-06

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("admins", sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("admins", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "admin_sessions",
        sa.Column("jti", sa.String(64), primary_key=True),
        sa.Column("admin_id", sa.Integer(), sa.ForeignKey("admins.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_admin_sessions_admin_id", "admin_sessions", ["admin_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("username", sa.String(100), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("resource", sa.String(200), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("admin_sessions")
    op.drop_column("admins", "locked_until")
    op.drop_column("admins", "failed_attempts")
