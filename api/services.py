from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import func, lambda_stmt, select, text, tuple_
from sqlalchemy.exc import MultipleResultsFound, NoResultFound, SQLAlchemyError

from .exc import ClientError, InternalError
from .models import RawEvent
from .schemas import Cursor

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from .database import DBBase
    from .schemas import EventCreate


def _count(session: "Session", model: type["DBBase"], estimate=True) -> int:
    """Estimate the total of records in the a given mapped entity table"""
    stmt = select(func.count().label("total")).select_from(model)
    if estimate:
        stmt = text("""
            SELECT reltuples::BIGINT AS total
            FROM pg_class
                JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
            WHERE relname = :table
                AND nspname = :schema""").bindparams(
            table=model.__tablename__,
            schema=model.metadata.schema,
        )
    return int(session.execute(stmt).scalar_one())


def count(session: "Session", model: type["DBBase"]) -> int:
    """Count the exact amount of records stored by the table mapped by the model"""
    return _count(session, model, estimate=False)


def estimate_count(session: "Session", model: type["DBBase"]) -> int:
    """Estimate the total of records in the given table mapped by model"""
    return _count(session, model)


def get_event(session: "Session", _id: UUID | str) -> RawEvent | None:
    """Get a single event by its id"""
    _id = _id if isinstance(_id, UUID) else UUID(_id, version=7)
    result = None
    try:
        stmt = select(RawEvent).where(RawEvent.id_ == _id)
        result = session.execute(stmt).one()[0]
    except NoResultFound:
        raise ClientError(f"Event with id {_id} not found") from None
    except MultipleResultsFound as e_multiple:
        raise InternalError(f"Multiple events found with the same id {_id}", e_multiple) from None
    return result


def get_events(session: "Session", cursor: Cursor | None = None) -> tuple[list[RawEvent], Cursor]:
    """
    fetch the next section of :class:.models.RawEvent stored in the underlying
    database connected with `session`

    :param:

    """
    if not cursor:
        cursor = Cursor()
    page = []
    try:
        sorter = tuple_(RawEvent.timestamp, RawEvent.id_)
        limit = cursor.limit + 1
        stmt = lambda_stmt(lambda: select(RawEvent))
        if cursor.next_ and cursor.timestamp:
            id_ = cursor.next_
            timestamp = cursor.timestamp
            stmt += lambda s: s.where(sorter > (timestamp, id_))
        stmt += lambda s: s.order_by(sorter)
        stmt += lambda s: s.limit(limit)
        page = [record[0] for record in session.execute(stmt).all()]
        if len(page) == limit:
            ahead = page.pop()
            cursor.next_ = ahead.id_
            cursor.timestamp = ahead.retrieved_at
            cursor.has_more = True
    except SQLAlchemyError as e_sql:
        raise InternalError(f"Cannot fetch next page from {cursor}", e_sql) from None
    except IndexError as e_idx:
        raise InternalError("Un expected small size", e_idx) from None
    return page, cursor


def save_event(
    session: "Session",
    event: "EventCreate",
    flush=True,
    commit=True,
) -> RawEvent | None:
    """Add a new event to the database"""
    new_event = None
    try:
        new_event = RawEvent(**event.model_dump(by_alias=False))
        session.add(new_event)
        if flush:
            session.flush()
        if commit:
            session.commit()
        session.refresh(new_event, attribute_names=["id_", "retrieved_at"])
    except SQLAlchemyError as e_sql:
        session.rollback()
        raise InternalError(f"Cannot save new event entry {event}", e_sql) from None
    except ValidationError as e_pydantic:
        session.rollback()
        raise InternalError(
            "Failed to validate model returned when creating new event", e_pydantic
        ) from None
    return new_event
