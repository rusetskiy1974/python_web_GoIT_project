import enum
from typing import Literal

from fastapi import Path
from pydantic import BaseModel
from fastapi.params import Query
from starlette.datastructures import UploadFile
from starlette.responses import FileResponse

from src.conf.transform import TRANSFORM_METHOD
from src.models.models import Image
from src.schemas.image import ImageReadSchema

method_list = tuple(TRANSFORM_METHOD.keys())


class TransformedImageRequest(BaseModel):
    image_id: int = Path(..., ge=1),
    method: Literal[method_list] = Query(...)  # type: ignore


class TransformedImageResponse(BaseModel):
    image: ImageReadSchema

