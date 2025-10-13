from fastapi import BackgroundTasks, Depends, FastAPI, Response

from app.controller.mlflow_sync_controller import MLFlowSyncController, SyncModelsRequest
from app.controller.database import DatabaseController, get_db_controller

app = FastAPI()

@app.post("/sync")
async def post_mlflow_sync(models: SyncModelsRequest, response: Response, background_tasks: BackgroundTasks, db_controller: DatabaseController = Depends(get_db_controller)):
  return await MLFlowSyncController().sync_models(models, api_response=response, background_tasks=background_tasks, db_controller=db_controller)
