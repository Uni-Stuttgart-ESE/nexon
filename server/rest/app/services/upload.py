"""Upload endpoints for registering ONNX models and metadata."""

from __future__ import annotations


from fastapi import APIRouter, ErrorWithStatusCode, HTTPException, UploadFile
from pydantic import BaseModel

from ..controller.upload import UploadControllerDep

router = APIRouter(prefix="/upload", tags=["Upload"])


class UploadResponse(BaseModel):
    """Response payload returned after successfully uploading a model."""

    message: str
    model_id: str
    file_id: str


@router.post(
    "/",
    response_model=UploadResponse,
    summary="Upload an ONNX model (status=Uploaded)",
    responses={400: {"description": "Only .onnx files are allowed"}},
)
async def upload_file(file: UploadFile, upload_controller: UploadControllerDep):
    """
    Uploads an ONNX model file
    """
    try:
        return upload_controller.upload_file(file)
    except ErrorWithStatusCode as e:
        raise e.to_http_exception()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
