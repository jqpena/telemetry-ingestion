"""add: enums to enforce integrity in events

Revision ID: 15c4edd02068
Revises: da22c7d80dc8
Create Date: 2026-03-20 04:20:06.823672+00:00

"""

from collections.abc import Sequence

from alembic import op
from api.models import EventTypes
from sqlalchemy.dialects.postgresql import VARCHAR

# revision identifiers, used by Alembic.
revision: str = "15c4edd02068"
down_revision: str | Sequence[str] | None = "da22c7d80dc8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    EventTypes.create(op.get_bind())
    op.alter_column(
        "events",
        "event_type",
        type_=EventTypes,
        schema="raw",
        postgresql_using="event_type::raw.event_types",
    )


def downgrade() -> None:
    """Downgrade schema."""
    EventTypes.drop(op.get_bind())
    op.alter_column("events", "event_type", type_=VARCHAR(100), schema="raw")
