from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, class_mapper, sessionmaker
from sqlalchemy.schema import MetaData

from .config import Config
from .exc import InternalError


class DBBase(DeclarativeBase):
    metadata = MetaData(schema="raw")

    def _asdict(self) -> dict[str, Any]:
        return {
            column.key: getattr(self, column.key) for column in class_mapper(self.__class__).attrs
        }


_engine = create_engine(
    Config["DB_URL"],
    echo=False,
    echo_pool=False,
    isolation_level="READ COMMITTED",
    pool_size=Config["DB_POOL_SIZE"],
    max_overflow=15,
    connect_args={"options": f"-c timezone={Config['TIMEZONE'] or 'UTC'}"},
)

SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False, autoflush=False)

PG_VERSION = _engine.dialect.server_version_info
PG_MINIMUM_VERSION = (18, 0)
if not PG_VERSION:
    try:
        with _engine.connect() as conn:
            version = conn.execute(text("SHOW server_version")).first()
            PG_VERSION = version and tuple(int(x) for x in version[0].split("."))
    except SQLAlchemyError:
        PG_VERSION = (18, 0)  # Assume the minimum supported version if we can't determine it
elif PG_VERSION < PG_MINIMUM_VERSION:
    raise RuntimeError(
        f"PostgreSQL version {PG_VERSION} is not supported. Upgrade to a newer version to use this application."
    )


def get_session():
    try:
        with SessionFactory.begin() as session:
            yield session
    except SQLAlchemyError as e_sql:
        raise InternalError(
            f"Error catch by dependency get_session (Type={type(e_sql).__name__})", e_sql
        ) from None
