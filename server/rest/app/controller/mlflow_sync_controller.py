from datetime import datetime
from typing import Dict, List, Optional, Tuple
from bson import ObjectId
from fastapi import BackgroundTasks, Response
import mlflow
import os
import tempfile
import mlflow.artifacts
from pydantic import BaseModel
import logging
import traceback

from mlflow.entities.model_registry import RegisteredModel

from app.controller.database import DatabaseController, ModelMetadata
from app.util.constants import STATUS_DEPLOYED, STATUS_DOWNLOADING, STATUS_UPLOADED
from app.util.file_utils import convert_size
from app.controller.deployment_controller import get_inference_endpoint

logger = logging.getLogger("uvicorn")

BASE_URL = "http://localhost:3000"

VERSION_STATE_DOWNLOADING = "downloading"
VERSION_STATE_DEPLOYING = "deploying"
VERSION_STATE_UNDEPLOYING = "undeploying"
VERSION_STATE_AVAILABLE = "available"

STATE_QUEUED = "queued"
STATE_ERROR = "error"
STATE_EXISTS = "exists"

class SyncResultEntry(BaseModel):
    model_name: str
    version_selector: str
    success: bool
    details: Optional[str] = None
    resolved_versions: List[str] = []

def not_found_result(model_name: str, version_selector: str):
    return SyncResultEntry(model_name=model_name, version_selector=version_selector, success=False, details="Model not found")

def invalid_selector_result(model_name: str, version_selector: str):
    return SyncResultEntry(model_name=model_name, version_selector=version_selector, success=False, details="Invalid version selector")

def success_result(model_name: str, version_selector: str, versions: List[str], details: str = None):
    return SyncResultEntry(model_name=model_name, version_selector=version_selector, success=True, resolved_versions=versions, details=details)

class VersionResultEntry(BaseModel):
    version: str
    status: str

class QueuedModelInfos():
    def __init__(self, model_name: str, model_version: str, model_uri: str, source_selectors: List[str], nexon_id: str = None, exists: bool = False):
        self.nexon_id = nexon_id
        self.exists = exists
        self.model_name = model_name
        self.model_version = model_version
        self.model_uri = model_uri
        self.source_selectors = source_selectors

class SyncModelsRequest(BaseModel):
    models: List[Tuple[str, str]]  # List of tuples (model_name, version_specifier)
    
class SyncModelsResponse(BaseModel):
    error_count: int = 0
    results: List[SyncResultEntry] = []
    versions: List[VersionResultEntry] = []

class MLFlowSyncController:
    def __init__(self):
        self._set_mlflow_tracking_uri()
        self.mlflow_client = mlflow.tracking.MlflowClient()

    def _set_mlflow_tracking_uri(self):
        """
        Sets the MLflow tracking URI from environment variable.
        """
        mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
        if not mlflow_tracking_uri:
            raise ValueError("MLFLOW_TRACKING_URI environment variable not set.")
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        logger.info(f"MLflow tracking URI set to: {mlflow_tracking_uri}")

    async def sync_models(self, request: SyncModelsRequest, api_response: Response, background_tasks: BackgroundTasks, db_controller: DatabaseController):
      """
      Download and deploy the models specified in 'request' based on their version selectors.
      
      Args:
          request (SyncModelsRequest): Request object containing model names and version selectors.
          api_response (Response): FastAPI response object to set status codes.
          background_tasks (BackgroundTasks): FastAPI background tasks to run downloads asynchronously.
          db_controller (DatabaseController): Database controller for interacting with NEXON database.
      """
      sync_models_response = SyncModelsResponse(has_errors=False, results=[])
      versions_to_deploy: Dict[str, QueuedModelInfos] = {}

      for model_name, version_selector in request.models:
          result = None
          
          # Resolve given selectors to actual model versions from MLflow
          try:
            full_selector = f"{model_name}/{version_selector}"
            if (version_selector == "latest"):
              result =  await self.find_version_uri_latest(model_name)
            elif (version_selector.startswith("@")):
              result = await self.find_version_uri_by_alias(model_name, version_selector)
            elif (":" in version_selector):
              result = await self.find_version_uri_by_tag(model_name, version_selector)
            elif (version_selector.isdigit()):
              result = await self.find_version_uri_by_version(model_name, version_selector)
            else:
              result = invalid_selector_result(model_name, version_selector)
              
            for version_uri in result.resolved_versions:
              if version_uri not in versions_to_deploy:
                versions_to_deploy[version_uri] = QueuedModelInfos(model_name, version_uri.split("/")[-1], version_uri, [full_selector])
              else:
                versions_to_deploy[version_uri].source_selectors.append(full_selector)
          except Exception as e:
            logger.warning(f"Failed to find MLflow version for {model_name} - {version_selector}: {e}")
            traceback.print_exc()
            result = not_found_result(model_name, version_selector)

          self._push_result(sync_models_response, result)
     
      resolved_versions = set(versions_to_deploy.keys())
      logger.info(f"Resolved model versions: {resolved_versions}\n")
      for uri, info in versions_to_deploy.items():
        logger.info(f"- {uri} selectors: {info.source_selectors}")
      
      latest_deployment = await db_controller.get_latest_mlflow_deployment()
      previous_deployed_versions = set(latest_deployment.versions) if latest_deployment else set()
      logger.info(f"\nPrevious deployed versions: {previous_deployed_versions}\n")
      
      added_versions = resolved_versions - previous_deployed_versions
      removed_versions = previous_deployed_versions - resolved_versions
      persistent_versions = resolved_versions.intersection(previous_deployed_versions)
      logger.info(f"Added versions: {added_versions}")
      logger.info(f"Removed versions: {removed_versions}")
      logger.info(f"Persistent versions: {persistent_versions}\n")
      
      for uri in added_versions:
          logger.info(f"Inserting new model to deploy: {uri}")
          existing_model = await self._find_model_in_db(db_controller, versions_to_deploy[uri].model_name, versions_to_deploy[uri].model_version)
          if not existing_model:
            sync_models_response.versions.append(VersionResultEntry(version=uri, status=VERSION_STATE_DOWNLOADING))
            await self._insert_model_in_db(db_controller, versions_to_deploy[uri])
          else:
            sync_models_response.versions.append(VersionResultEntry(version=uri, status=VERSION_STATE_DEPLOYING))
            versions_to_deploy[uri].nexon_id = existing_model["_id"]
            versions_to_deploy[uri].exists = True
      
      for uri in removed_versions:
          sync_models_response.versions.append(VersionResultEntry(version=uri, status=VERSION_STATE_UNDEPLOYING))
          
      for uri in persistent_versions:
          sync_models_response.versions.append(VersionResultEntry(version=uri, status=VERSION_STATE_AVAILABLE))
      
      logger.info(f"Starting background task to download and deploy models.")
      added_model_infos = [versions_to_deploy[uri] for uri in added_versions]
      persistent_model_infos = [versions_to_deploy[uri] for uri in persistent_versions]
      background_tasks.add_task(self.background_task_download_and_deploy_models, added_model_infos, removed_versions, persistent_model_infos, db_controller=db_controller)

      await db_controller.insert_mlflow_deployment(timestamp=int(datetime.now().timestamp()), versions=list(resolved_versions))
      
      if (sync_models_response.error_count > 0):
        api_response.status_code = 207
      return sync_models_response
    
    async def _insert_model_in_db(self, db_controller: DatabaseController, queued_model_info: QueuedModelInfos):
      logger.info(f"Registering model in DB: {queued_model_info.model_uri}")
      now = datetime.now()
      upload_date = f"{now.day}/{now.month}/{now.year}"
      model_metadata = ModelMetadata(
        name= queued_model_info.model_name,
        upload= upload_date,
        version= int(queued_model_info.model_version),
        status= STATUS_DOWNLOADING,
        mlflow_uri= queued_model_info.model_uri,
        mlflow_source_selectors=queued_model_info.source_selectors
      )
      logger.debug(f"Model metadata: {model_metadata}")
      new_id = await db_controller.insert_model(model_metadata)
      queued_model_info.nexon_id = new_id

    async def _find_model_in_db(self, db_controller: DatabaseController, model_name: str, model_version: str):
      return await db_controller.find_one({"name": model_name, "version": int(model_version)})
    
    def _push_result(self, response: SyncModelsResponse, result: SyncResultEntry):
      response.results.append(result)
      if not result.success:
        response.error_count += 1

    def _get_registered_model(self, model_name: str) -> Optional[RegisteredModel]:
      try:
          reg_model = self.mlflow_client.get_registered_model(model_name)
          return reg_model
      except Exception:
          return None

    async def find_version_uri_latest(self, model_name: str, version_selector: str = "latest"):
      """
      Find the latest version of the given MLflow model.
      Args:
          model_name (str): Name of the registered model
          version_selector (str): "latest"
      """
      registered_model = self._get_registered_model(model_name)
      if not registered_model:
          return not_found_result(model_name, version_selector)

      latest_versions = registered_model.latest_versions
      if not latest_versions:
          return not_found_result(model_name, version_selector)
      version = latest_versions[0].version
      version_uri = f"models:/{model_name}/{version}"
      return success_result(model_name, version_selector, [version_uri])

    async def find_version_uri_by_version(self, model_name: str, version_selector: str):
      """
      Find the specific given version of the given MLflow model.
      Args:
          model_name (str): Name of the registered model
          version_selector (str): Specific version number
      """
      version_uri = f"models:/{model_name}/{version_selector}"
      registered_model = self._get_registered_model(model_name)
      if not registered_model:
          return not_found_result(model_name, version_selector)
      return success_result(model_name, version_selector, [version_uri])

    async def find_version_uri_by_alias(self, model_name: str, version_selector: str):
      """
      Find the version of the given MLflow model by the given alias.
      Args:
          model_name (str): Name of the registered model
          version_selector (str): "@alias_name"
      """
      alias = version_selector[1:]  # Remove '@' prefix
      version = self.mlflow_client.get_model_version_by_alias(model_name, alias)
      if not version:
          return not_found_result(model_name, version_selector)
      version_uri = f"models:/{model_name}/{version.version}"
      return success_result(model_name, version_selector, [version_uri])

    async def find_version_uri_by_tag(self, model_name: str, version_selector: str):
      """
      Find all versions of the given MLflow model with the given tag.
      Args:
          model_name (str): Name of the registered model
          version_selector (str): "tag_key:tag_value"
      """
      tag = version_selector.split(":")
      tagged_versions = self.mlflow_client.search_model_versions(f"name='{model_name}' and tag.{tag[0]}='{tag[1]}'")
      versions = []
      for v in tagged_versions:
          versions.append(f"models:/{model_name}/{v.version}")
      return success_result(model_name, version_selector, versions, details=f"Found {len(tagged_versions)} tagged versions.")

    async def background_task_download_and_deploy_models(self, added_models: List[QueuedModelInfos], removed_models: List[str], persistent_models: List[QueuedModelInfos], db_controller: DatabaseController):
      logger.info(f"Downloading added models...")

      for model_infos in added_models:
        if not model_infos.exists:
          try:
            logger.info(f"Downloading and deploying model: {model_infos.model_uri} [{model_infos.nexon_id}]")
            artifacts = mlflow.artifacts.list_artifacts(model_infos.model_uri)
            for artifact in artifacts:
              if artifact.path.endswith(".onnx"):
                logger.debug(f"Found ONNX artifact: {artifact.path}")
                with tempfile.TemporaryDirectory() as tmpdir:
                  logger.debug(f"Temporary directory created: {tmpdir}")
                  logger.debug(f"Downloading model artifact from URI: {model_infos.model_uri}")
                  artifact_uri = f"{model_infos.model_uri}/{artifact.path}"
                  download_result = mlflow.artifacts.download_artifacts(
                      artifact_uri=artifact_uri,
                      dst_path=tmpdir
                  )
                  local_file_path = os.path.join(tmpdir, artifact.path)
                  logger.debug(f"Model downloaded to '{local_file_path}': {download_result}")
                  await self.upload_and_update_model(model_infos, local_file_path, artifact.path, db_controller)
          except Exception as e:
            logger.error(f"Error downloading and deploying model {model_infos.model_name} version {model_infos.model_version}: {e}")
            import traceback
            traceback.print_exc()
        else:
          await self._set_model_deployed_in_db(db_controller, model_infos.nexon_id, model_infos)
      
      logger.info(f"Undeploying removed models...")
      for version_uri in removed_models:
        logger.info(f"Undeploying model: {version_uri}")
        try:
          model = await db_controller.find_one({"mlflow_uri": {"$eq": version_uri}})
          if model:
            await db_controller.update_one(
              {"_id": ObjectId(model["_id"])},
              {"$set": {"status": STATUS_UPLOADED, "deploy": None, "endpoint": None, "mlflow_source_selectors": []}},
            )
          else:
            logger.warning(f"Cannot remove model {model_infos.model_name} version {model_infos.model_version}: Not found.")
        except Exception as e:
          logger.error(f"Error undeploying model {model_infos.model_name} version {model_infos.model_version}: {e}")
          import traceback
          traceback.print_exc()
      
      logger.info(f"Updating persistent models...")
      for model_infos in persistent_models:
        logger.info(f"Updating model: {model_infos.model_uri}")
        try:
          model = await self._find_model_in_db(db_controller, model_infos.model_name, model_infos.model_version)
          if model:
            if (model.get("status") == STATUS_DEPLOYED):
              await db_controller.update_one(
                {"_id": ObjectId(model["_id"])},
                {"$set": {
                  "mlflow_source_selectors": model_infos.source_selectors,
                  }},
              )
            else:
              await self._set_model_deployed_in_db(db_controller, model["_id"], model_infos)
          else:
            logger.warning(f"Cannot update model {model_infos.model_name} version {model_infos.model_version}: Not found.")
        except Exception as e:
          logger.error(f"Error updating model {model_infos.model_name} version {model_infos.model_version}: {e}")
          import traceback
          traceback.print_exc()
      logger.info(f"Background task completed.")
      
    async def upload_and_update_model(self, model_infos: QueuedModelInfos, file_path: str, file_name: str, db_controller: DatabaseController) -> ObjectId:
      with open(file_path, "rb") as file_stream:
          logger.debug(f"File opened successfully: {file_stream}")
          logger.debug(f"Uploading model file to database...")
          file_id = await db_controller.upload_file(file_name, file_stream)
          now = datetime.now()
          deploy_date = f"{now.day}/{now.month}/{now.year}"
          file_size_bytes = os.fstat(file_stream.fileno()).st_size
          logger.debug(f"File size (bytes): {file_size_bytes}")
          file_size_readable = convert_size(file_size_bytes)
          api_endpoint = get_inference_endpoint(model_infos.model_name, int(model_infos.model_version))
          logger.debug(f"Nexon Model ID: {model_infos.nexon_id}, File ID: {file_id}, Deploy Date: {deploy_date}, API Endpoint: {api_endpoint}")
          updated_result = await db_controller.update_one(
            {"_id": ObjectId(model_infos.nexon_id)},
            {"$set": {
              "status": STATUS_DEPLOYED,
              "deploy": deploy_date,
              "file_id": str(file_id),
              "endpoint": api_endpoint,
              "size": file_size_readable,
              "mlflow_source_selectors": model_infos.source_selectors
            }},
          )
          logger.debug(f"Model metadata updated in database: {updated_result}")
          
    async def _set_model_deployed_in_db(self, db_controller: DatabaseController, nexon_id: str, model_infos: QueuedModelInfos):
      now = datetime.now()
      deploy_date = f"{now.day}/{now.month}/{now.year}"
      api_endpoint = get_inference_endpoint(model_infos.model_name, int(model_infos.model_version))
      await db_controller.update_one(
        {"_id": ObjectId(nexon_id)},
        {"$set": {
          "mlflow_source_selectors": model_infos.source_selectors,
          "status": STATUS_DEPLOYED,
          "deploy": deploy_date,
          "endpoint": api_endpoint,
          }},
      )