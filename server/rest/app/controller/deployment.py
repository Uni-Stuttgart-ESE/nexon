from typing import Annotated, Dict
from urllib.parse import urlparse

from bson import ObjectId
from FastAPI import Depends
from pydantic import BaseModel

from ..util.constants import STATUS_DEPLOYED, STATUS_UPLOADED
from ..util.datetime import today
from ..util.errors import BadRequestError, NotFoundError
from .database import ModelRepositoryDep

BASE_URL = "http://localhost:3000"


class DeployRequest(BaseModel):
    model_name: str
    model_id: str


class UndeployRequest(BaseModel):
    model_name: str
    model_version: int


def get_inference_endpoints(
    base_url: str, model_name: str, model_version: int = None
) -> Dict[str, str]:
    base_url = base_url.rstrip("/")  # e.g., http://127.0.0.1:8080
    parsed = urlparse(base_url)

    return {
        "rest_envoy": f"{base_url}/inference/infer/{model_name}{
            f'/{model_version}' if model_version else ''
        }",
        "rest_direct": f"http://127.0.0.1:8000/inference/infer/{model_name}{
            f'/{model_version}' if model_version else ''
        }",
        "grpc_envoy": parsed.netloc or "127.0.0.1:8080",
        "grpc_direct": "127.0.0.1:50051",
        "grpc_fqmn": "nexon.grpc.inference.v1.InferenceService/Predict",
    }


class DeploymentController:
    def __init__(self, db_controller: ModelRepositoryDep):
        self.db_controller = db_controller

    async def deploy_model(self, base_url: str, request: DeployRequest):
        """
        Deploys an already uploaded model
        """
        model_id = ObjectId(request.model_id)
        try:
            models = await self.db_controller.find({"name": request.model_name})
            for model in models:
                if model["status"] == STATUS_DEPLOYED:
                    if model["_id"] == model_id:
                        raise BadRequestError("This version is already deployed!")
                    else:
                        raise BadRequestError(
                            "Another version of this model is already deployed!"
                        )

            date = today()
            endpoints = get_inference_endpoints(base_url, request.model_name)
            updated_result = await self.db_controller.update_one(
                {"_id": model_id},
                {
                    "$set": {
                        "status": STATUS_DEPLOYED,
                        "deploy": date,
                        "endpoint": endpoints.rest_envoy,
                    }
                },
            )
            if updated_result.modified_count > 0:
                return {
                    "message": f"Model {request.model_name} deployed successfuly!",
                    "endpoints": endpoints,
                }
            else:
                raise NotFoundError("Model does not exist")
        except Exception as e:
            raise Exception(f"Error deploying model: {str(e)}")

    async def undeploy_model(self, request: UndeployRequest):
        """
        Undeploys a model by updating its status in the database.
        """
        # Find the specific model by name and version
        model = await self.db_controller.find_one(
            {"name": request.model_name, "version": request.model_version}
        )

        if model["status"] != STATUS_DEPLOYED:
            raise BadRequestError("Model is not deployed")

        if not model:
            raise NotFoundError("Model not found.")

        # Update model status to 'Pending'
        update_result = await self.db_controller.update_one(
            {"_id": model["_id"]}, {"$set": {"status": STATUS_UPLOADED}}
        )

        if update_result.modified_count == 0:
            raise Exception("Failed to undeploy model.")

        return {
            "message": f"Model '{request.model_name}' (v{request.model_version}) undeployed successfully."
        }


DeploymentControllerDep = Annotated[DeploymentController, Depends()]
