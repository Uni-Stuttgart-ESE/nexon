from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
    AsyncIOMotorGridFSBucket,
)
from bson import ObjectId


class ModelMetadata:
    def __init__(
        self,
        file_id: str = None,
        name: str = None,
        upload: str = None,
        version: int = None,
        deploy: str = None,
        size: str = None,
        status: str = None,
        mlflow_uri: str = None,
        mlflow_source_selectors: list = [],
    ):
        self.file_id = file_id
        self.name = name
        self.upload = upload
        self.version = version
        self.deploy = deploy
        self.size = size
        self.status = status
        self.mlflow_uri = mlflow_uri
        self.mlflow_source_selectors = mlflow_source_selectors

    def to_dict(self):
        return {
            "file_id": self.file_id,
            "name": self.name,
            "upload": self.upload,
            "version": self.version,
            "deploy": self.deploy,
            "size": self.size,
            "status": self.status,
            "mlflow_uri": self.mlflow_uri,
            "mlflow_source_selectors": self.mlflow_source_selectors,
        }


class MLflowDeployment:
    def __init__(self, timestamp: int, versions: list[str]):
        self.timestamp = timestamp
        self.versions = versions


class ModelRepository:
    """
    Database controller for managing model metadata.
    """

    def __init__(
        self,
        client: AsyncIOMotorClient,
        database: AsyncIOMotorDatabase,
        fs_bucket: AsyncIOMotorGridFSBucket,
    ):
        self.db_client = client
        self.database = database
        self.fs = fs_bucket
        self.models_collection = self.database["models"]
        self.mlflow_deployments_collection = self.database["mlflow_deployments"]

    def debug(self):
        return "Live DB Controller"

    async def find(self, *args: any):
        return await self.models_collection.find(*args).to_list(None)

    async def find_and_sort(self, query, sort):
        return await self.models_collection.find(query).sort(sort).to_list(None)

    async def find_one(self, query, sort=None):
        return await self.models_collection.find_one(query, sort=sort)

    async def delete_one(self, query):
        return await self.models_collection.delete_one(query)

    async def upload_file(self, filename: str, file: any):
        return await self.fs.upload_from_stream(filename, file)

    async def download_file(self, file_id: ObjectId):
        return await self.fs.open_download_stream(file_id=file_id)

    async def delete_file(self, file_id: ObjectId):
        return await self.fs.delete(file_id)

    async def insert_model(self, model_metadata: ModelMetadata):
        """
        Inserts a model metadata into the database.
        """
        model_dict = model_metadata.to_dict()
        result = await self.models_collection.insert_one(model_dict)
        return str(result.inserted_id)  # Return the inserted ID as a string

    async def update_one(self, query, update):
        """
        Updates a model metadata in the database.
        """
        return await self.models_collection.update_one(query, update)

    async def get_latest_mlflow_deployment(self) -> MLflowDeployment | None:
        doc = await self.mlflow_deployments_collection.find_one(
            {}, sort=[("timestamp", -1)]
        )
        if doc:
            return MLflowDeployment(
                timestamp=doc["timestamp"], versions=doc["versions"]
            )
        return None

    async def insert_mlflow_deployment(self, timestamp: int, versions: list[str]):
        doc = MLflowDeployment(timestamp=timestamp, versions=versions).__dict__
        await self.mlflow_deployments_collection.insert_one(doc)
