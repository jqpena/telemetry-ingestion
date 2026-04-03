import base64
import binascii
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

    next_: UUID7 | str | None = Field(default="Un processable next query", repr=True)
    timestamp: AwareDatetime | None = Field(default=None, repr=True)
    has_more: bool = Field(default=False, repr=False)
    limit: PositiveInt = Field(lt=5000, default=1000, repr=False)


def bs64_encode(value):
    """Encode base64 url safe trimming equals '='"""
    return base64.urlsafe_b64encode(value).decode().strip("=")


def bs64_decode(value):
    """Decode base64 url safe string into its bytes, it add equal sign pad"""
    pad = len(value) % 4
    decoded = None
    try:
        if pad == 2:
            decoded = base64.urlsafe_b64decode(value + "==")
        elif pad == 3:
            decoded = base64.urlsafe_b64decode(value + "=")
        else:
            decoded = base64.urlsafe_b64decode(value)
    except binascii.Error:
        pass
    return decoded


def sha256_signature(secret_key, message):
    """Generate a SAH256 signature"""
    if isinstance(secret_key, str):
        secret_key = secret_key.encode()
    if isinstance(message, str):
        message = message.encode()
    return hmac.new(secret_key, message, "sha256").digest()


def floats_bytes(values):
    """Convert ints to bytes Big Endian"""
    return struct.pack(">" + "d" * len(values), *values)


def bytes_float(value):
    """Unpack bytes to int big Endian"""
    return struct.unpack(">d", value)[0]


def urlsafe_cursor_encode(cursor: Cursor):
    """Encode a cursor as an URL-sage string"""
    if cursor.next_ is None or cursor.timestamp is None:
        return None
    if isinstance(cursor.next_, str):
        return None
    payload = floats_bytes((cursor.timestamp.timestamp(),)) + cursor.next_.bytes
    signature = sha256_signature(Config["SECRET_KEY"], payload)[:8]
    return bs64_encode(payload + signature)


def cursor_decode(cursor: QueryCursor):
    """Decode a cursor from a URL query parameter"""
    if cursor.next_ is None:
        return Cursor(next_=None, timestamp=None, has_more=False, limit=cursor.limit)
    if not (raw_bytes := bs64_decode(cursor.next_)):
        return Cursor()
    payload = raw_bytes[:-8]
    signature = raw_bytes[-8:]
    expected_sig = sha256_signature(Config["SECRET_KEY"], payload)[:8]

    if not hmac.compare_digest(signature, expected_sig):
        return Cursor(
            next_="Invalid cursor signature",
            timestamp=None,
            has_more=False,
            limit=cursor.limit,
        )

    return Cursor(
        next_=UUID(bytes=raw_bytes[8:24], version=7),
        timestamp=datetime.fromtimestamp(
            bytes_float(raw_bytes[:8]),
        ).astimezone(Config["TIMEZONE"]),
        has_more=False,
        limit=cursor.limit,
    )


def encode_id(_id: UUID | None):
    if not _id:
        return ""
    return bs64_encode(_id.bytes)


def decode_id(cursor: Id) -> UUID | None:
    if not (raw := bs64_decode(cursor)):
        return None
    id_ = None
    try:
        id_ = UUID(bytes=raw, version=7)
    except ValueError:
        pass
    return id_
