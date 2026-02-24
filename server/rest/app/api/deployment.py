from app.controller.deployment_controller import DeploymentController, DeployRequest, UndeployRequest
from app.controller.upload_controller import UploadController
from app.controller.database import get_db_controller, DatabaseController
from app.util.errors import ErrorWithStatusCode
from bson import ObjectId
from fastapi import FastAPI, File, HTTPException, UploadFile, Depends

app = FastAPI()


@app.post("/deploy-file/")
async def deploy_file(file: UploadFile = File(...), db_controller: DatabaseController = Depends(get_db_controller)):
    """
    Uploads an ONNX model file and initializes an inference session.
    """
    try:
      uploaded_model = await UploadController(db_controller).upload_file(file)
      model_name = uploaded_model["name"]
      return await DeploymentController(db_controller).deploy_model(
          DeployRequest(
              model_name=model_name, model_id=uploaded_model["model_id"]
          )
      )
    except ErrorWithStatusCode as e:  
      raise e.as_http_exception()
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))


@app.post("/deploy-model/")
async def deploy_model(request: DeployRequest, db_controller: DatabaseController = Depends(get_db_controller)):
    """
    Deploys an already uploaded model
    """
    try:
      return await DeploymentController(db_controller).deploy_model(request)
    except ErrorWithStatusCode as e:  
      raise e.as_http_exception()
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
    

@app.put("/undeploy/{model_name}")
async def undeploy_model(request: UndeployRequest, db_controller: DatabaseController = Depends(get_db_controller)):
    """
    Undeploys a model by updating its status in the database.
    """
    try:
      return await DeploymentController(db_controller).undeploy_model(request)
    except ErrorWithStatusCode as e:  
      raise e.as_http_exception()
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
