from typing import TYPE_CHECKING, Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, class_mapper, sessionmaker
from sqlalchemy.schema import MetaData

from .config import Config
from .exc import InternalError

if TYPE_CHECKING:
    from sqlalchemy import Engine


class DBBase(DeclarativeBase):
    metadata = MetaData(schema="raw")

    def _asdict(self) -> dict[str, Any]:
        return {
            column.key: getattr(self, column.key) for column in class_mapper(self.__class__).attrs
        }


_engine: "Engine | None" = None

SessionFactory: "sessionmaker | None" = None

PG_MINIMUM_VERSION = (18, 0)


def create_factories() -> "Engine":
    engine = create_engine(
        Config["DB_URL"],
        echo=True,
        echo_pool=Config["LOG_LEVEL"].lower() if Config["LOG_LEVEL"].lower() == "debug" else True,
        isolation_level="READ COMMITTED",
        pool_size=Config["DB_POOL_SIZE"],
        max_overflow=15,
        connect_args={"options": f"-c timezone={Config['TIMEZONE'].key or 'UTC'}"},
    )
    globals()["_engine"] = engine
    globals()["SessionFactory"] = sessionmaker(
        bind=_engine, expire_on_commit=False, autoflush=False
    )
    pg_version = engine.dialect.server_version_info
    if not pg_version:
        try:
            with engine.connect() as conn:
                version = conn.execute(text("SHOW server_version")).first()
                pg_version = version and tuple(int(x) for x in version[0].split("."))
        except SQLAlchemyError:
            pg_version = (18, 0)  # Assume the minimum supported version if we can't determine it
    elif pg_version < PG_MINIMUM_VERSION:
        raise RuntimeError(
            f"PostgreSQL version {pg_version} is not supported. Upgrade to a newer version to use this application."
        )
    return engine


def get_session():
    if not SessionFactory:
        raise RuntimeError(
            "Unexpected error, the lifespan for the session has not been initialized"
        )
    try:
        with SessionFactory.begin() as session:
            yield session
    except SQLAlchemyError as e_sql:
        raise InternalError(
            f"Error catch by dependency get_session (Type={type(e_sql).__name__})", e_sql
        ) from None
