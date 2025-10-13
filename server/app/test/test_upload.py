import io
import unittest
from fastapi.testclient import TestClient
from fastapi import status
from app.api.upload import app
from app.controller.database import get_db_controller

MOCKED_ID = "mocked_id"
MOCKED_FILE_ID = "mocked_file_id"

async def get_mock_controller():
    return MockDBController()
      
class MockDBController:
    async def insert_model(self, model_metadata):
        return MOCKED_ID
      
    async def upload_file(self, filename, file):
        return MOCKED_FILE_ID
      
    async def find_one(self, query, sort=None):
        return None
      
class TestUploadApi(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
      app.dependency_overrides[get_db_controller] = get_mock_controller
      cls.client = TestClient(app)
      
  @classmethod
  def tearDownClass(cls):
      app.dependency_overrides = {}

  def test_upload_file_success(self):
      file_content = b"dummy onnx content"
      response = self.client.post(
          "/",
          files={"file": ("model.onnx", io.BytesIO(file_content), "application/octet-stream")},
      )
      assert response.status_code == status.HTTP_200_OK
      assert response.json()['model_id'] == MOCKED_ID
      assert response.json()['file_id'] == MOCKED_FILE_ID
      
if __name__ == "__main__":
    unittest.main()