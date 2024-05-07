from pydantic import BaseModel

class RatingCreateSchema(BaseModel):
    rating: int
    image_id: int