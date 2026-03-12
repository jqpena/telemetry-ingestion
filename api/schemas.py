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
    PositiveInt,
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


class CursorPageQuery(BaseSchema):
    model_config = {"title": "CursorQuery"}
    next_: Annotated[
        Base64UrlBytes | None,
        Field(title="Identifier to fetch next page batch", description="Cursor for the next page"),
    ] = Field(alias="next", validation_alias="next", default=None)
    limit: Annotated[
        PositiveInt,
        Field(
            title="Max records",
            description="Maximum number of records to return per page",
            lt=5000,
            default=1000,
        ),
    ] = Field(lt=5000, default=1000)


class Cursor(BaseSchema):
    """:class:`Cursor`, internal schema to map opaque page query parameters
        of pagination requests.

    .. note:: This class can be extended to store a robust cursor with information
                 as direction, expiration, etc. For now, it only stores the timestamp
                 and the id of the next batch
    """

    next_: UUID7 | None
    timestamp: AwareDatetime | None
    has_more: bool
    limit: PositiveInt = Field(lt=5000, default=1000)


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
        CursorPageQuery,
        Field(
            title="Page description",
            description="Information of the current page and the cursor identifier for the next page batch",
        ),
    ]


# TODO: Enhance the information that is returned when an error occurs
class ErrorResponse(BaseSchema):
    model_config = {"title": "Error"}
    detail: Annotated[
        str, Field(title="Error details", description="Verbose information about the error")
    ]


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
