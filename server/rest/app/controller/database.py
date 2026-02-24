import logging
from typing import Annotated

from fastapi import Depends
from shared.database import DB_NAME, MONGO_URI, client, create_indices, db, fs
from shared.model_repository import ModelRepository

logger = logging.getLogger("database")


async def connect_to_mongo():
    """Initializes the MongoDB client, database, and GridFS bucket."""
    await create_indices()
    logger.info(
        f"Successfully connected to MongoDB at {MONGO_URI} and initialized GridFS for '{DB_NAME}'."
    )


async def close_mongo_connection():
    """Closes the MongoDB connection."""
    global db_client
    if db_client:
        db_client.close()
        logger.info("MongoDB connection closed.")


def get_model_repository() -> ModelRepository:
    """Dependency for FastAPI to inject the model repository."""
    return ModelRepository(client, db, fs)


ModelRepositoryDep = Annotated[ModelRepository, Depends(get_model_repository)]
