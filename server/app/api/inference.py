from fastapi import FastAPI, Depends, HTTPException
from app.controller.inference_controller import InferenceController, InferenceRequest
from app.controller.database import get_db_controller, DatabaseController
from app.util.errors import ErrorWithStatusCode

app = FastAPI()

@app.post("/infer/{model_name}")
async def infer(request: InferenceRequest, model_name, db_controller: DatabaseController = Depends(get_db_controller)):
    """
    Runs inference on the uploaded ONNX model with the given inputs.
    """
    try:
      return await InferenceController(db_controller).infer(request, model_name)
    except ErrorWithStatusCode as e:
      raise e.as_http_exception()
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/infer/{model_name}/{model_version}")
async def infer_version(request: InferenceRequest, model_name, model_version: int, db_controller: DatabaseController = Depends(get_db_controller)):
    """
    Runs inference on the uploaded ONNX model with the given inputs.
    """
    try:
      return await InferenceController(db_controller).infer(request, model_name, model_version)
    except ErrorWithStatusCode as e:
      raise e.as_http_exception()
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))