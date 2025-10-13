import io
from types import SimpleNamespace
import unittest
from bson import ObjectId
from fastapi.testclient import TestClient
from fastapi import status
from app.api.models import app
from app.controller.database import get_db_controller
from app.util.constants import STATUS_DEPLOYED, STATUS_UPLOADED

MOCKED_ID = "mocked_id"
MOCKED_FILE_ID = str(ObjectId())

async def get_mock_controller():
    return MockDBController()
      
class MockDBController:
    async def find(self, *args):
      models = [
        {
          "_id": MOCKED_ID + "1",
          "file_id": MOCKED_FILE_ID,
          "name": "mocked_model",
          "version": 1,
          "status": STATUS_DEPLOYED
        },
        {
          "_id": MOCKED_ID + "2",
          "file_id": MOCKED_FILE_ID,
          "name": "mocked_model",
          "version": 1,
          "status": STATUS_UPLOADED
        }
      ]
        
      if not args:
        return models

      # Convert args to a dictionary: ("status", STATUS_DEPLOYED) -> {"status": STATUS_DEPLOYED}
      if len(args) == 1 and isinstance(args[0], dict):
        filter_dict = args[0]
      else:
        filter_dict = dict(zip(args[::2], args[1::2]))

      return [
        model for model in models
        if all(model.get(key) == value for key, value in filter_dict.items())
      ]
      
    async def delete_file(self, file_id):
        pass
      
    async def delete_one(self, query):
        return SimpleNamespace(deleted_count=1)
      
    async def find_one(self, query, sort=None):
        return {
            "_id": MOCKED_ID+"1",
            "file_id": MOCKED_FILE_ID,
            "name": "mocked_model",
            "version": 1,
            "status": STATUS_DEPLOYED
        }
      
class TestModelsApi(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
      app.dependency_overrides[get_db_controller] = get_mock_controller
      cls.client = TestClient(app)
      
  @classmethod
  def tearDownClass(cls):
      app.dependency_overrides = {}

  def test_get_deployed_models(self):
      response = self.client.get("/deployedModels")
      
      assert response.status_code == status.HTTP_200_OK
      assert len(response.json()) == 1
      
      assert response.json()[0]['_id'] == MOCKED_ID+"1"
      assert response.json()[0]['file_id'] == MOCKED_FILE_ID
      assert response.json()[0]['name'] == "mocked_model"
      assert response.json()[0]['version'] == 1
      assert response.json()[0]['status'] == STATUS_DEPLOYED
      
  
  def test_get_uploaded_models(self):
      response = self.client.get("/uploadedModels")
      
      assert response.status_code == status.HTTP_200_OK
      assert len(response.json()) == 1
      
      assert response.json()[0]['_id'] == MOCKED_ID+"2"
      assert response.json()[0]['file_id'] == MOCKED_FILE_ID
      assert response.json()[0]['name'] == "mocked_model"
      assert response.json()[0]['version'] == 1
      assert response.json()[0]['status'] == STATUS_UPLOADED
  
  
  def test_get_all_models(self):
      response = self.client.get("/allModels")
      
      assert response.status_code == status.HTTP_200_OK
      assert len(response.json()) == 2
      
      assert response.json()[0]['_id'] == MOCKED_ID+"1"
      assert response.json()[0]['file_id'] == MOCKED_FILE_ID
      assert response.json()[0]['name'] == "mocked_model"
      assert response.json()[0]['version'] == 1
      assert response.json()[0]['status'] == STATUS_DEPLOYED
      
      assert response.json()[1]['_id'] == MOCKED_ID+"2"
      
  
  def test_delete_model(self):
      response = self.client.delete("/deleteModel/mocked_model/1")
      assert response.status_code == status.HTTP_200_OK
      assert response.json()['message'] == "Model 'mocked_model' deleted successfully"
      
if __name__ == "__main__":
    unittest.main()