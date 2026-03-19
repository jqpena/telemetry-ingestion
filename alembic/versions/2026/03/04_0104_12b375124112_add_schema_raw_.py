"""add: schema raw events table

Revision ID: 12b375124112
Revises:
Create Date: 2026-03-04 01:04:50.792483+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "12b375124112"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = ("main",)
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "events",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("event_type", sa.VARCHAR(length=100), nullable=False),
        sa.Column("service", sa.VARCHAR(length=100), nullable=False),
        sa.Column("value", sa.FLOAT(precision=18), nullable=False),
        sa.Column("host", sa.VARCHAR(length=256), nullable=False),
        sa.Column("timestamp", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("received_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.CheckConstraint("value >= 0", name="chk_value_non_negative"),
        sa.PrimaryKeyConstraint("id", "timestamp", name="pk_raw_events"),
        schema="raw",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("events", schema="raw")
