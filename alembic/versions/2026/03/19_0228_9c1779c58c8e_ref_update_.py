"""ref: update timestamp index

Revision ID: 9c1779c58c8e
Revises: 23d231f6f782
Create Date: 2026-03-19 02:28:13.008016+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9c1779c58c8e"
down_revision: str | Sequence[str] | None = "23d231f6f782"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index("idx_events_timestamp", table_name="events", schema="raw")
    op.create_index(
        "idx_events_timestamp_service",
        "events",
        ("timestamp", "service"),
        postgresql_include=["host", "event_type"],
        schema="raw",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.create_index(
        "idx_events_timestamp_service",
        "events",
        ("timestamp",),
        postgresql_include=["host", "service", "event_type"],
        schema="raw",
    )
