"""Deployment endpoints for publishing ONNX models via the shared orchestrator."""

from __future__ import annotations


from fastapi import (
    APIRouter,
    ErrorWithStatusCode,
    HTTPException,
    Request,
    UploadFile,
)
from pydantic import BaseModel

from ..controller.deployment import (
    DeploymentControllerDep,
    DeployRequest,
    UndeployRequest,
)
from ..controller.upload import UploadControllerDep

router = APIRouter(prefix="/deployment", tags=["Deployment"])


class DeployResponse(BaseModel):
    """Response payload summarizing deployment status and endpoints."""

    message: str
    endpoints: dict  # {rest_envoy, rest_direct, grpc_envoy, grpc_direct, grpc_service}


@router.post(
    "/deploy-file/",
    response_model=DeployResponse,
    summary="Upload an ONNX file and deploy it immediately (status -> Deployed)",
)
async def deploy_file(
    http_request: Request,
    file: UploadFile,
    upload_controller: UploadControllerDep,
    deployment_controller: DeploymentControllerDep,
):
    """
    Uploads an ONNX model file and initializes an inference session.
    """
    try:
        uploaded_model = await upload_controller.upload_file(file)
        model_name = uploaded_model["name"]
        return await deployment_controller.deploy_model(
            http_request.base_url,
            DeployRequest(model_name=model_name, model_id=uploaded_model["model_id"]),
        )
    except ErrorWithStatusCode as e:
        raise e.as_http_exception()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/deploy-model/",
    response_model=DeployResponse,
    summary="Deploy an already uploaded model (status -> Deployed)",
)
async def deploy_model(
    http_request: Request,
    deploy_request: DeployRequest,
    deployment_controller: DeploymentControllerDep,
):
    """
    Deploys an already uploaded model
    """
    try:
        return await deployment_controller.deploy_model(
            http_request.base_url,
            deploy_request,
        )
    except ErrorWithStatusCode as e:
        raise e.as_http_exception()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/undeploy/{model_name}",
    summary="Undeploy a model (status -> Uploaded)",
)
async def undeploy_model(
    undeploy_request: UndeployRequest,
    deployment_controller: DeploymentControllerDep,
):
    """
    Undeploys a model by updating its status in the database.
    """
    try:
        return await deployment_controller.undeploy_model(undeploy_request)
    except ErrorWithStatusCode as e:
        raise e.as_http_exception()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
