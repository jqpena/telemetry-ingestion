"""add: retrieved_at index

Revision ID: 23d231f6f782
Revises: 12b375124112
Create Date: 2026-03-04 01:19:18.265848+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "23d231f6f782"
down_revision: str | Sequence[str] | None = "12b375124112"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "idx_events_retrieved_at",
        "events",
        ("retrieved_at",),
        unique=False,
        schema="raw",
        postgresql_include=["host", "service", "event_type"],
    )
    op.create_index(
        "idx_events_type_service",
        "events",
        ("event_type", "service"),
        postgresql_include=["host"],
        schema="raw",
    )
    op.create_index(
        "idx_events_timestamp",
        "events",
        ("timestamp",),
        postgresql_include=["host", "service", "event_type"],
        schema="raw",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_events_retrieved_at", "events", schema="raw")
    op.drop_index("idx_events_type_service", "events", schema="raw")
    op.drop_index("idx_events_timestamp", "events", schema="raw")
