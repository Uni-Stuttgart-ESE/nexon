import onnxruntime as ort
from pydantic import BaseModel
import numpy as np
from bson import ObjectId
from app.controller.database import DatabaseController
from app.util.errors import BadRequestError, NotFoundError
from app.util.constants import STATUS_DEPLOYED

class InferenceRequest(BaseModel):
    input: list
    
onnx_to_numpy_dtype = {
    "tensor(float)": np.float32,
    "tensor(int64)": np.int64,
    "tensor(double)": np.float64
}

class InferenceController:
  def __init__(self, db_controller: DatabaseController):
    self.db_controller = db_controller

  async def infer(self, request: InferenceRequest, model_name: str, model_version: int = None):
    """
    Runs inference on the uploaded ONNX model with the given inputs.
    """
    file_id = None
    if model_version is not None:
      model = await self.db_controller.find_one({"name": f"{model_name}", "version": model_version, "status": STATUS_DEPLOYED})
      if model:
        file_id = model["file_id"]
      else:
        raise NotFoundError("No model with this name and version has been deployed")
    else:
      models = await self.db_controller.find_and_sort({"name": model_name, "status": STATUS_DEPLOYED}, [("version", -1)])
      if not models:
        raise NotFoundError("No model with this name has been deployed")
      file_id = models[0]["file_id"]
      
    # models = await self.db_controller.find({"name": model_name})
    # if not models:
    #   raise NotFoundError("No model with this name has been uploaded")
    # file_id = None
    # for model in models:
    #   if model["status"] == STATUS_DEPLOYED:
    #       file_id = model["file_id"]
    #       break
    # if file_id == None:
    #   raise NotFoundError("No model with this name has been deployed")
        
    try:
      grid_out = await self.db_controller.download_file(file_id=ObjectId(file_id))
      model_bytes = await grid_out.read()
      session = ort.InferenceSession(model_bytes)
    except Exception as e: 
        raise Exception(f"Server error: {str(e)}. This could be due to a corrupted file or a database disconnection. Please try uploading the model again or try again later.")

    try:
        # Convert input data to NumPy array
        
        type = onnx_to_numpy_dtype.get(session.get_inputs()[0].type)
        input_data = np.array(request.input).astype(type)
        input_data = request.input
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name


        # Currently poses some problems because the shape format isn't always the same and mismatching shapes do not necessarily lead to an error

        # Check input shape compatibility
        # expected_shape = session.get_inputs()[0].shape
        # if list(input_data.shape) != expected_shape:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=f"Input shape mismatch. Expected: {expected_shape}, Received: {list(input_data.shape)}",
        #     )

        # Run inference
        results = session.run([output_name], {input_name: input_data})

        json_results = [result.tolist() for result in results]
        return {"results": json_results}

    except Exception as e:
        raise BadRequestError(f"Inference error: {str(e)}")