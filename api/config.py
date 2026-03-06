# type: ignore
from typing import TypedDict

from decouple import config
from typing_extensions import Sentinel

MandatoryEnv = Sentinel("MandatoryEnv")


class _config(TypedDict):
    DB_URL: str
    DB_POOL_SIZE: int
    TIMEZONE: str
    SECRET_KEY: str


Config: _config = {
    "DB_URL": config("DB_URL", default=MandatoryEnv),
    "DB_POOL_SIZE": config("DB_POOL_SIZE", default=15, cast=int),
    "TIMEZONE": config("TIMEZONE", default="UTC"),
    "SECRET_KEY": config("SECRET_KEY", default=MandatoryEnv),
}

if Config["SECRET_KEY"] is MandatoryEnv:
    raise RuntimeError("Security breach, unset environment variable SECRET_KEY")
if Config["DB_URL"] is MandatoryEnv:
    raise RuntimeError("Database URL is not set, will not connect to any database")
