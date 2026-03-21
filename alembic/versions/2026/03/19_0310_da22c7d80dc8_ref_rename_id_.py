"""ref: rename id column to a verbose one

Revision ID: da22c7d80dc8
Revises: 9c1779c58c8e
Create Date: 2026-03-19 03:10:43.366380+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "da22c7d80dc8"
down_revision: str | Sequence[str] | None = "9c1779c58c8e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("events", "id", new_column_name="event_id", schema="raw")


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("events", "event_id", new_column_name="id", schema="raw")
