from datetime import UTC, datetime
from typing import Annotated, Generic, TypeVar

from pydantic import (
    UUID7,
    AliasGenerator,
    AwareDatetime,
    Base64UrlBytes,
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeFloat,
)
from pydantic.alias_generators import to_camel, to_snake

_TModel = TypeVar("_TModel", bound="BaseSchema")


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        serialize_by_alias=True,
        str_strip_whitespace=True,
        alias_generator=AliasGenerator(validation_alias=to_snake, serialization_alias=to_camel),
    )


class CursorPage(BaseModel):
    _next: Annotated[Base64UrlBytes | None, Field(description="The cursor for the next page")] = (
        Field(alias="next", validation_alias="next", default=None)
    )
    has_more: bool


class ResponsePage(BaseModel, Generic[_TModel]):
    data: list[_TModel]
    paging: CursorPage


# TODO: Enhance the information that is returned when an error occurs
class ErrorResponse(BaseModel):
    detail: str


class EventCreate(BaseModel):
    event_type: str
    service: str
    value: NonNegativeFloat
    host: str
    timestamp: Annotated[AwareDatetime, Field(validate_default=False)] = Field(
        default_factory=lambda: datetime.now(UTC)
    )


class EventDB(EventCreate):
    _id: UUID7 = Field(alias="id")
    retrieved_at: AwareDatetime


class EventReadPage(ResponsePage):
    data: list[EventDB]
