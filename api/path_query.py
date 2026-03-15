from typing import Annotated

from fastapi import Path, Query
from pydantic import AliasGenerator, BaseModel, ConfigDict, Field, PositiveInt
from pydantic.alias_generators import to_camel, to_snake

Id = Annotated[str, Path(alias="id")]


class CursorPageQuery(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        serialize_by_alias=True,
        str_strip_whitespace=True,
        alias_generator=AliasGenerator(validation_alias=to_snake, serialization_alias=to_camel),
    )
    model_config = {"title": "CursorQuery"}
    next_: Annotated[
        str | None,
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


QueryCursor = Annotated[CursorPageQuery, Query()]
