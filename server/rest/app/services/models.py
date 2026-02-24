from fastapi import HTTPException, APIRouter

from ..controller.model import ModelControllerDep
from ..util.errors import ErrorWithStatusCode

router = APIRouter(tags=["Inventory"])


@router.get("/deployedModels")
async def getDeployedModels(model_controller: ModelControllerDep):
    return await model_controller.get_deployed_models()


@router.get("/uploadedModels")
async def getUploadedModels(model_controller: ModelControllerDep):
    return await model_controller.get_undeployed_models()


@router.get("/allModels")
async def getAllModels(model_controller: ModelControllerDep):
    return await model_controller.get_all_models()


@router.delete("/deleteModel/{model_name}/{model_version}")
async def delete_model(
    model_name: str,
    model_version: int,
    model_controller: ModelControllerDep,
):
    try:
        return await model_controller.delete_model(model_name, model_version)
    except ErrorWithStatusCode as e:
        raise e.as_http_exception()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
