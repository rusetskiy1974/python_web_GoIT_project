import enum

from fastapi import Query, Path
from pydantic import BaseModel

from src.conf.transform import TRANSFORM_METHOD


class TransformedImageRequest(BaseModel):
    method: enum.Enum(list[TRANSFORM_METHOD.keys()])                                      #Query(..., description=f"Allowed transform methods: {', '.join(TRANSFORM_METHOD.keys())}")
    image_id: int = Path(..., ge=1)


class TransformedImageResponse(BaseModel):
    qr_code_url: str

