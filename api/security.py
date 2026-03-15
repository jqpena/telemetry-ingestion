import base64
import hmac
import struct
from datetime import datetime
from uuid import UUID

from pydantic import UUID7, AliasGenerator, AwareDatetime, BaseModel, ConfigDict, Field, PositiveInt
from pydantic.alias_generators import to_camel, to_snake

from .config import Config
from .path_query import Id, QueryCursor


class Cursor(BaseModel):
    """:class:`Cursor`, internal schema to map opaque page query parameters
        of pagination requests.

    .. note:: This class can be extended to store a robust cursor with information
                 as direction, expiration, etc. For now, it only stores the timestamp
                 and the id of the next batch
    """

    model_config = ConfigDict(
        extra="forbid",
        serialize_by_alias=True,
        str_strip_whitespace=True,
        alias_generator=AliasGenerator(validation_alias=to_snake, serialization_alias=to_camel),
    )

    next_: UUID7 | None = Field(default=None, repr=True)
    timestamp: AwareDatetime | None = Field(default=None, repr=True)
    has_more: bool = Field(default=False, repr=False)
    limit: PositiveInt = Field(lt=5000, default=1000, repr=False)


def sha256_signature(secret_key, message):
    """Generate a SAH256 signature"""
    if isinstance(secret_key, str):
        secret_key = secret_key.encode()
    if isinstance(message, str):
        message = message.encode()
    return hmac.new(secret_key, message, "sha256").digest()


def ints_bytes(values):
    """Convert ints to bytes Big Endian"""
    return struct.pack(">" + "Q" * len(values), *values)


def bytes_int(value):
    """Unpack bytes to int big Endian"""
    return struct.unpack(">Q", value)[0]


def urlsafe_cursor_encode(cursor: Cursor):
    """Encode a cursor as an URL-sage string"""
    if cursor.next_ is None or cursor.timestamp is None:
        return None
    payload = ints_bytes((cursor.timestamp.timestamp(),)) + cursor.next_.bytes
    signature = sha256_signature(Config["SECRET_KEY"], payload)[:8]
    return base64.urlsafe_b64encode(payload + signature).decode()


def cursor_decode(cursor: QueryCursor):
    """Decode a cursor from a URL query parameter"""
    if cursor.next_ is None:
        return Cursor(next_=None, timestamp=None, has_more=False, limit=cursor.limit)
    raw_bytes = base64.urlsafe_b64decode(cursor.next_)
    payload = raw_bytes[:-8]
    signature = raw_bytes[-8:]
    expected_sig = sha256_signature(Config["SECRET_KEY"], payload)[:8]
    assert hmac.compare_digest(signature, expected_sig), "Invalid cursor signature"
    return Cursor(
        next_=UUID(bytes=raw_bytes[8:24], version=7),
        timestamp=datetime.fromtimestamp(
            bytes_int(raw_bytes[:8]),
        ),
        has_more=False,
        limit=cursor.limit,
    )


def encode_id(_id: UUID | None):
    if not _id:
        return ""
    return base64.urlsafe_b64encode(_id.bytes).decode()


def decode_id(cursor: Id) -> UUID:
    print(cursor)
    raw = base64.urlsafe_b64decode(cursor)
    return UUID(bytes=raw, version=7)
