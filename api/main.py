from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from uvicorn import run

from .config import Server
from .routes import v1_router

__version__ = "0.1.0"
version = __version__  # Expose version for use in API metadata and elsewhere
app = FastAPI(
    title="Host events telemetry ingestion",
    version=version,
    description=(
        "API for ingesting and querying events from host in an architecture, "
        "where we can identify the host by its fqdn and the event by its name, "
        "storing the timestamp and additional metadata for the service that trigger the event"
    ),
)

app.add_middleware(GZipMiddleware, minimum_size=1024)  # Compress responses larger than 1KB


@app.get("/health", tags=["health"])
@app.head("/health", tags=["health"])
def health():
    return {"status": "ok"}


app.include_router(v1_router, prefix="/api", tags=["api", "v1"])


if __name__ == "__main__":
    run(app, **Server, server_header=False)
