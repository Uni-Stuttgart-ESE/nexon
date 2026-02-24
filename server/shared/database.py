"""Centralized MongoDB/Motor configuration shared between REST and gRPC surfaces."""

from __future__ import annotations

import logging
import os
from os import environ

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorGridFSBucket,
)

# Load .env for local development (no effect in Docker unless env vars are missing).
try:
    from dotenv import find_dotenv, load_dotenv  # pip install python-dotenv

    # Do not override variables already provided by the shell or docker-compose.
    load_dotenv(find_dotenv(usecwd=True), override=False)
except Exception:
    pass  # python-dotenv is optional

log = logging.getLogger("database")


MONGO_URI = f"mongodb://{environ['NEXON_MONGO_USER']}:{environ['NEXON_MONGO_PASS']}@{environ['NEXON_MONGO_HOST']}:{environ['NEXON_MONGO_PORT']}"
DB_NAME = environ["NEXON_MONGO_DB"]

# Tunables with sane defaults
SERVER_SELECTION_TIMEOUT_MS = int(
    os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "10000")
)
UUID_REPRESENTATION = os.getenv(
    "MONGO_UUID_REPRESENTATION", "standard"
)  # Motor/PyMongo option


# Redact credentials in logs.
def _redact(uri: str) -> str:
    """Mask credentials in a MongoDB URI."""
    try:
        if "@" in uri and "://" in uri:
            scheme, rest = uri.split("://", 1)
            auth_and_host = rest.split("@", 1)
            if len(auth_and_host) == 2:
                _, host = auth_and_host
                return f"{scheme}://***:***@{host}"
        return uri
    except Exception:
        return "<redacted>"


# Single global client for the process
client: AsyncIOMotorClient = AsyncIOMotorClient(
    MONGO_URI,
    serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT_MS,
    uuidRepresentation=UUID_REPRESENTATION,
)
db = client[DB_NAME]

# Collections / buckets
models_collection = db["models"]
fs: AsyncIOMotorGridFSBucket = AsyncIOMotorGridFSBucket(db)

log.info("MongoDB connected (uri=%s, db=%s)", _redact(MONGO_URI), DB_NAME)


# Small helper reused by readiness probes.
async def ping() -> bool:
    """Return True when MongoDB responds to ping command; False otherwise."""
    try:
        await db.command("ping")
        return True
    except Exception as e:
        log.warning("Mongo ping failed: %s", e)
        return False


async def create_indices(self):
    await self.mlflow_deployments_collection.create_index("timestamp")
    await self.models_collection.create_index(
        "mlflow_uri",
        unique=True,
        partialFilterExpression={"mlflow_uri": {"$type": "string"}},
    )


__all__ = [
    "MONGO_URI",
    "DB_NAME",
    "client",
    "db",
    "models_collection",
    "fs",
    "ping",
]
