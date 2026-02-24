from fastapi import UploadFile, File
from datetime import datetime
from app.controller.database import DatabaseController, ModelMetadata
from app.util.errors import BadRequestError
from app.util.file_utils import convert_size
from app.util.constants import STATUS_UPLOADED


class UploadController:
  def __init__(self, db_controller: DatabaseController):
    self.db_controller = db_controller
    
  async def upload_file(self, file: UploadFile):
    """
    Uploads an ONNX model file
    """
    if not file.filename.endswith(".onnx"):
      raise BadRequestError("Only ONNX files are allowed.")
    
    try:
      latest_model = await self.db_controller.find_one(
          {"name": file.filename}, sort=[("version", -1)]
      )
      new_version = 1 if latest_model is None else latest_model["version"] + 1

      file_id = await self.db_controller.upload_file(file.filename, file.file)
      size = convert_size(file.size)
      upload_date = f"{datetime.now().day}/{datetime.now().month}/{datetime.now().year}"

      model_metadata = ModelMetadata(
          file_id= str(file_id),
          name= file.filename,
          upload= upload_date,
          version= new_version,
          deploy= "",
          size= size,
          status= STATUS_UPLOADED,
      )
      new_id = await self.db_controller.insert_model(model_metadata)
      result = {
          "message": f"Model {file.filename} uploaded successfully!",
          "model_id": new_id,
          **model_metadata.to_dict()
      }
      return result
      
    except Exception as e:
      raise Exception(f"Error uploading model: {str(e)}")