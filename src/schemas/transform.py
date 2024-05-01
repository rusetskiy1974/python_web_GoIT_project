from pydantic import BaseModel


class TransformedImageRequest(BaseModel):
    image_url: str


class TransformedImageResponse(BaseModel):
    transformed_image_url: str
    qr_code_url: str

