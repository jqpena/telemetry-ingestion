from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid7

import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import ENUM, FLOAT, TIMESTAMP, VARCHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .database import DBBase

_EVENT_TYPES = ["cpu_usage", "memory_usage", "disk_io", "network_latency"]

EventTypes = ENUM(
    *_EVENT_TYPES, name="event_types", schema=DBBase.metadata.schema, create_type=False
)

EventTypesEnum = StrEnum("EventTypesEnum", EventTypes.enums)


class RawEvent(DBBase):
    __tablename__ = "events"

    id_: Mapped[UUID | None] = mapped_column(
        "event_id",
        server_default=func.uuidv7(),
        default=uuid7,
        type_=PG_UUID,
    )
    event_type: Mapped[EventTypesEnum] = mapped_column(EventTypes, nullable=False)
    service: Mapped[str] = mapped_column(nullable=False, type_=VARCHAR(100))
    value: Mapped[float] = mapped_column(nullable=False, type_=FLOAT(18))
    host: Mapped[str] = mapped_column(nullable=False, type_=VARCHAR(256))
    timestamp: Mapped[datetime] = mapped_column(
        nullable=False,
        type_=TIMESTAMP(timezone=True),
    )
    received_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
        type_=TIMESTAMP(timezone=True),
    )

    __table_args__ = (
        sa.PrimaryKeyConstraint("event_id", "timestamp", name="pk_raw_events"),
        sa.CheckConstraint("value >= 0", name="chk_value_non_negative"),
    )
