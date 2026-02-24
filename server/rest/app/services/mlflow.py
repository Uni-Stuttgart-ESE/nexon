from fastapi import APIRouter, Response

from ..controller.mlflow import (
    MLFlowSyncControllerDep,
    SyncModelsRequest,
)

router = APIRouter(prefix="/mlflow", tags=["MLflow"])


@router.post("/sync")
async def post_mlflow_sync(
    models: SyncModelsRequest,
    response: Response,
    mlflow_sync_controller: MLFlowSyncControllerDep,
):
    return await mlflow_sync_controller.sync_models(models, api_response=response)
