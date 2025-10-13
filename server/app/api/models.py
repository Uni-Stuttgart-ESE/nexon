from fastapi import FastAPI, Depends, HTTPException
from app.controller.model_controller import ModelController
from app.controller.database import get_db_controller, DatabaseController
from app.util.errors import ErrorWithStatusCode

app = FastAPI()


@app.get("/deployedModels")
async def getUploadedModels(db_controller: DatabaseController = Depends(get_db_controller)):
  return await ModelController(db_controller).get_deployed_models()


@app.get("/uploadedModels")
async def getUploadedModels(db_controller: DatabaseController = Depends(get_db_controller)):
  return await ModelController(db_controller).get_undeployed_models()
  
  
@app.get("/allModels")
async def getAllModels(db_controller: DatabaseController = Depends(get_db_controller)):
  return await ModelController(db_controller).get_all_models()
  
  
@app.delete("/deleteModel/{model_name}/{model_version}")
async def delete_model(model_name: str, model_version: int, db_controller: DatabaseController = Depends(get_db_controller)):
  try:
    return await ModelController(db_controller).delete_model(model_name, model_version)
  except ErrorWithStatusCode as e:
    raise e.as_http_exception()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))