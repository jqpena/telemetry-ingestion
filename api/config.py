# type: ignore
from typing import TypedDict
from zoneinfo import ZoneInfo

from decouple import config
from typing_extensions import Sentinel

MandatoryEnv = Sentinel("MandatoryEnv")


class _server(TypedDict):
    host: str
    port: int
    workers: int | None
    reload: bool
    log_level: str


class _config(TypedDict):
    DB_URL: str
    DB_POOL_SIZE: int
    TIMEZONE: ZoneInfo
    LOG_LEVEL: str
    SECRET_KEY: str


Server: _server = {
    "host": config("HOST", default="127.0.0.1"),
    "port": config("PORT", default=8000, cast=int),
    "reload": config("RELOAD", default=False, cast=bool),
    "workers": config("WORKERS", default=None),
    "log_level": config("LOG_LEVEL", default="info").lower(),
}


Config: _config = {
    "DB_URL": config("DB_URL", default=MandatoryEnv),
    "DB_POOL_SIZE": config("DB_POOL_SIZE", default=15, cast=int),
    "TIMEZONE": ZoneInfo(config("TIMEZONE", default="UTC")),
    "SECRET_KEY": config("SECRET_KEY", default=MandatoryEnv),
    "LOG_LEVEL": config("LOG_LEVEL", default="info").lower(),
}

if Server["reload"] and Server["workers"] is not None:
    Server["workers"] = None

if Config["SECRET_KEY"] is MandatoryEnv:
    raise RuntimeError("Security breach, unset environment variable SECRET_KEY")
if Config["DB_URL"] is MandatoryEnv:
    raise RuntimeError("Database URL is not set, will not connect to any database")
