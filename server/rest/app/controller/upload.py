from typing import Annotated

from fastapi import Depends, UploadFile

from ..util.constants import STATUS_UPLOADED
from ..util.datetime import today
from ..util.errors import BadRequestError
from ..util.file_utils import convert_size
from .database import ModelRepositoryDep, ModelMetadata


class UploadController:
    def __init__(self, db_controller: ModelRepositoryDep):
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
            # Preserve semantics; some servers don't expose UploadFile.size → fallback to "unknown"
            size_bytes = getattr(file, "size", None)
            try:
                size = (
                    convert_size(int(size_bytes))
                    if size_bytes is not None
                    else "unknown"
                )
            except Exception:
                size = "unknown"

            upload_date = today()

            model_metadata = ModelMetadata(
                file_id=str(file_id),
                name=file.filename,
                upload=upload_date,
                version=new_version,
                deploy="",
                size=size,
                status=STATUS_UPLOADED,
            )
            new_id = await self.db_controller.insert_model(model_metadata)
            result = {
                "message": f"Model {file.filename} uploaded successfully!",
                "model_id": new_id,
                "file_id": model_metadata.file_id,
            }
            return result

        except Exception as e:
            raise Exception(f"Error uploading model: {str(e)}")


UploadControllerDep = Annotated[UploadController, Depends()]
