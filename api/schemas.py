from datetime import UTC, datetime
from typing import Annotated, Any, Generic, TypeVar

from pydantic import (
    AliasGenerator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeFloat,
    PositiveInt,
    field_validator,
    model_validator,
)
from pydantic.alias_generators import to_camel, to_snake

from .security import Cursor, encode_id, urlsafe_cursor_encode

_TModel = TypeVar("_TModel", bound="BaseSchema")


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        serialize_by_alias=True,
        str_strip_whitespace=True,
        alias_generator=AliasGenerator(validation_alias=to_snake, serialization_alias=to_camel),
    )


class CursorResponse(BaseSchema):
    next_: Annotated[
        str | None,
        Field(
            alias="next",
            description="Identifier for the next cursor batch",
            exclude_if=lambda v: v is None,
        ),
    ] = Field(alias="next", default=None, exclude_if=lambda v: v is None)
    has_more: bool = Field(default=False)
    limit: PositiveInt = Field(lt=5000, default=1000)

    @model_validator(mode="before")
    @classmethod
    def coerce_next(cls, data):
        if isinstance(data, Cursor):
            return {
                "next_": urlsafe_cursor_encode(data),
                "has_more": data.has_more,
                "limit": data.limit,
            }
        return data


class ResponsePage(BaseSchema, Generic[_TModel]):
    data: Annotated[
        list[_TModel],
        Field(
            title="Data page",
            description="Page list containing at most the limit of records requested"
            "if there is no more than the size requested",
        ),
    ]
    paging: Annotated[
        CursorResponse,
        Field(
            title="Page description",
            description="Information of the current page and the cursor identifier for the next page batch",
        ),
    ]

    @field_validator("paging", mode="before")
    @classmethod
    def check_paging(cls, value):
        if isinstance(value, CursorResponse):
            return value
        if isinstance(value, Cursor):
            return CursorResponse.model_validate(
                {
                    "next_": urlsafe_cursor_encode(value),
                    "limit": value.limit,
                    "has_more": value.has_more,
                },
                by_name=True,
            )


# TODO: Enhance the information that is returned when an error occurs
class ErrorResponse(BaseSchema):
    model_config = {"title": "Error"}
    detail: Annotated[
        str, Field(title="Error details", description="Verbose information about the error")
    ]
    extra: dict[str, Any] | None = None


class EventCreate(BaseSchema):
    model_config = {"title": "NewEvent"}
    event_type: Annotated[
        str,
        Field(
            title="Event Type",
            description=(
                "The type of the event, used to identify the event and its "
                "meaning in the context of the host and service that trigger it"
            ),
            examples=[
                "cpu_usage",
                "memory_usage",
                "disk_io",
                "network_latency",
            ],  # TODO: convert into a Enum that map a Postgres ENUM
        ),
    ]
    service: Annotated[
        str,
        Field(
            title="Service Name/id",
            description=("The name of the service that trigger the event"),
            examples=["auth", "workers", "orchestrator"],
        ),
    ]
    value: NonNegativeFloat
    host: Annotated[
        str,
        Field(
            title="FQDN host/IP",
            description="FQDN of the host if the server has one, otherwise this value can be the IP",
        ),
    ]
    timestamp: Annotated[
        AwareDatetime,
        Field(
            validate_default=False,
            title="Remote host local time of event",
            description=(
                "Timezone aware timestamp of the event, this timestamp has "
                "be aware of the timezone where the host is located"
            ),
        ),
    ] = Field(default_factory=lambda: datetime.now(UTC))


class EventFullSchema(EventCreate):
    model_config = {"title": "Event"}
    id_: str = Field(alias="id")
    retrieved_at: AwareDatetime

    @field_validator("id_", mode="before")
    @classmethod
    def coerce_id(cls, value):
        if isinstance(value, str):
            return value
        return encode_id(value)
