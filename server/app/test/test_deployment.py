import io
from types import SimpleNamespace
import unittest
from bson import ObjectId
from fastapi.testclient import TestClient
from fastapi import status
from app.api.deployment import app
from app.api.upload import app as upload_app
from app.controller.database import ModelMetadata, get_db_controller
from app.util.constants import STATUS_DEPLOYED

MOCKED_ID = str(ObjectId())
MOCKED_FILE_ID = str(ObjectId())

cached_mock_controller = None

async def get_mock_controller():
  global cached_mock_controller
  if not cached_mock_controller:
    cached_mock_controller = MockDBController()
  return cached_mock_controller
      
class MockDBController:
    def __init__(self):
      self.models = []
      self.find_one_result = None
  
    async def find(self, *args):
      return self.models
      
    async def delete_file(self, file_id):
      pass
      
    async def update_one(self, query, *args):
      return SimpleNamespace(modified_count=1)
      
    async def find_one(self, query, sort=None):
      return self.find_one_result
    
    async def insert_model(self, model_metadata: ModelMetadata):
      self.models.append({
        "_id": MOCKED_ID,
        **model_metadata.to_dict(),
      })
      return MOCKED_ID
    
    async def upload_file(self, filename, file):
      return MOCKED_FILE_ID
      
class TestDeploymentApi(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
      app.dependency_overrides[get_db_controller] = get_mock_controller
      cls.client = TestClient(app)
      
  @classmethod
  def tearDownClass(cls):
      app.dependency_overrides = {}
      upload_app.dependency_overrides = {}

  def test_deploy_file(self):
      file_content = b"dummy onnx content"
      response = self.client.post(
          "/deploy-file/",
          files={"file": ("model.onnx", io.BytesIO(file_content), "application/octet-stream")},
      )
      assert response.status_code == status.HTTP_200_OK
      assert response.json()['message'] == "Model model.onnx deployed successfuly!"
      assert response.json()['inference_endpoint'] == "http://localhost:3000/inference/infer/model.onnx"
      
  
  def test_deploy_model(self):
      file_content = b"dummy onnx content"
      upload_app.dependency_overrides[get_db_controller] = get_mock_controller
      upload_response = TestClient(upload_app).post(
          "/",
          files={"file": ("model.onnx", io.BytesIO(file_content), "application/octet-stream")},
      )
      model_id = upload_response.json()['model_id']
      response = self.client.post(
          "/deploy-model",
          json={
              "model_name": "model.onnx",
              "model_id": model_id
          }
      )
      assert response.status_code == status.HTTP_200_OK
      assert response.json()['message'] == "Model model.onnx deployed successfuly!"
      assert response.json()['inference_endpoint'] == "http://localhost:3000/inference/infer/model.onnx"
  
  
  def test_undeploy_model(self):
      file_content = b"dummy onnx content"
      deploy_response = self.client.post(
          "/deploy-file/",
          files={"file": ("model.onnx", io.BytesIO(file_content), "application/octet-stream")},
      )
      cached_mock_controller.find_one_result = {
          "_id": MOCKED_ID,
          "name": "model.onnx",
          "version": 1,
          "status": STATUS_DEPLOYED,
          "file_id": MOCKED_FILE_ID,
          "size": "dummy_size",
          "upload": "01/01/2023",
          "deploy": "01/01/2023",
          "endpoint": "http://localhost:3000/inference/infer/model.onnx"
      }
      response = self.client.put(
          "/undeploy/model.onnx",
          json={
              "model_name": "model.onnx",
              "model_version": 1
          }
      )
      assert response.status_code == status.HTTP_200_OK
      assert response.json()['message'] == "Model 'model.onnx' (v1) undeployed successfully."
      
      
if __name__ == "__main__":
    unittest.main()