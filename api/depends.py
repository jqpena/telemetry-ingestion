from typing import Annotated
from uuid import UUID

from fastapi import Body, Depends
from sqlalchemy.orm import Session as SQLSession

from .database import get_session
from .schemas import Cursor as CursorSchema
from .schemas import EventCreate
from .security import cursor_decode, decode_id

Session = Annotated[SQLSession, Depends(get_session)]
EmbeddedEvent = Annotated[
    EventCreate,
    Body(
        title="NewEvent",
        embed=True,
        description="Event schema object",
    ),
]
Cursor = Annotated[CursorSchema, Depends(cursor_decode)]
IdPath = Annotated[UUID, Depends(decode_id)]
