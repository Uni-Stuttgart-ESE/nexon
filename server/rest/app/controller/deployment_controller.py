from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel
from app.controller.database import DatabaseController
from app.util.constants import STATUS_DEPLOYED, STATUS_UPLOADED
from app.util.errors import BadRequestError, NotFoundError

BASE_URL = "http://localhost:3000"

class DeployRequest(BaseModel):
    model_name: str
    model_id: str

class UndeployRequest(BaseModel):
    model_name: str
    model_version: int     
    
def get_inference_endpoint(model_name: str, model_version: int = None) -> str:
    if model_version:
        return f"{BASE_URL}/inference/infer/{model_name}/{model_version}"
    return f"{BASE_URL}/inference/infer/{model_name}"
      
class DeploymentController:
  def __init__(self, db_controller: DatabaseController):
    self.db_controller = db_controller
    
  async def deploy_model(self, request: DeployRequest):
    """
    Deploys an already uploaded model
    """
    model_id = ObjectId(request.model_id)
    try:
      models = await self.db_controller.find({"name": request.model_name})
      for model in models:
        if (model["status"] == STATUS_DEPLOYED):
          if model["_id"] == model_id:
            raise BadRequestError("This version is already deployed!")
          else:
            raise BadRequestError("Another version of this model is already deployed!")

      date = f"{datetime.now().day}/{datetime.now().month}/{datetime.now().year}"
      api_endpoint = get_inference_endpoint(request.model_name)
      updated_result = await self.db_controller.update_one(
          {"_id": model_id},
          {"$set": {"status": STATUS_DEPLOYED, "deploy": date, "endpoint": api_endpoint}},
      )
      if updated_result.modified_count > 0:
        return {
          "message": f"Model {request.model_name} deployed successfuly!",
          "inference_endpoint": api_endpoint
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
      model = await self.db_controller.find_one({"name": request.model_name, "version": request.model_version})

      if(model["status"] != STATUS_DEPLOYED) :
        raise BadRequestError("Model is not deployed")

      if not model:
          raise NotFoundError("Model not found.")

      # Update model status to 'Pending'
      update_result = await self.db_controller.update_one(
          {"_id": model["_id"]}, 
          {"$set": {"status": STATUS_UPLOADED}}
      )

      if update_result.modified_count == 0:
          raise Exception("Failed to undeploy model.")

      return {"message": f"Model '{request.model_name}' (v{request.model_version}) undeployed successfully."}