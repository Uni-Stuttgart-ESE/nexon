from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from app.controller.upload_controller import UploadController
from app.controller.database import DatabaseController, get_db_controller
from app.util.errors import ErrorWithStatusCode

app = FastAPI()

@app.post("/")
async def upload_file(file: UploadFile = File(...), db_controller: DatabaseController = Depends(get_db_controller)):
    """
    Uploads an ONNX model file
    """
    try:
      return await UploadController(db_controller).upload_file(file)
    except ErrorWithStatusCode as e:
      raise e.to_http_exception()
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))