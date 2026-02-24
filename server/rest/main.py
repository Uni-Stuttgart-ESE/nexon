"""FastAPI entrypoint for the NEXON REST surface with health and inventory routes."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Shared DB handles
from ..shared import database
from .app.controller.database import close_mongo_connection, connect_to_mongo
from .app.services import deployment, inference, mlflow, models, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to MongoDB when the app starts
    logging.getLogger("rest").info("REST starting...")
    await connect_to_mongo()

    yield

    # Close MongoDB connection when the app stops
    await close_mongo_connection()
    logging.getLogger("rest").info("REST shutdown complete.")


LOG_HEALTH = os.getenv("LOG_HEALTH", "0").lower() in ("1", "true", "yes", "on")


class _HealthAccessFilter(logging.Filter):
    """Suppress health endpoints from access logs unless explicitly enabled."""

    def filter(self, record: logging.LogRecord) -> bool:
        if LOG_HEALTH:
            return True
        msg = record.getMessage()
        return ("/healthz" not in msg) and ("/readyz" not in msg)


logging.getLogger("uvicorn.access").addFilter(_HealthAccessFilter())

openapi_tags = [
    {"name": "Upload", "description": "Upload ONNX models (status -> Uploaded)."},
    {
        "name": "Deployment",
        "description": "Deploy or undeploy models (Uploaded <-> Deployed).",
    },
    {"name": "Inference", "description": "Run inference on deployed models."},
    {"name": "Inventory", "description": "List or delete models."},
]

app = FastAPI(
    lifespan=lifespan,
    title="NEXON REST API",
    version="1.1",
    description="Upload, deploy, and run inference on ONNX models (MongoDB + GridFS).",
    openapi_tags=openapi_tags,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,  # hide the "Schemas" panel
        "docExpansion": "list",  # collapse endpoints by default (tidier)
    },
)


@app.get("/healthz", include_in_schema=False)
async def healthz():
    """Return service liveness status."""
    return {"status": "ok"}


@app.get("/readyz", include_in_schema=False)
async def readyz():
    """Return readiness status by pinging MongoDB."""
    try:
        await database.ping()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"not ready: {e}")


# Include routers so everything appears in a single OpenAPI document.
app.include_router(upload.router)
app.include_router(deployment.router)
app.include_router(inference.router)
app.include_router(mlflow.router)
app.include_router(models.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Return a welcome banner for the API root."""
    return {"message": "Welcome to the ONNX Inference API!"}
