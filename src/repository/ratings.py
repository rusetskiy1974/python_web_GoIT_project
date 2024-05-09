import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.models import UserToImage, Image, User
from src.schemas.rating import ImageRatingCreateSchema


async def rate_image(image: Image, new_rating: int, user_id: uuid.UUID, db: AsyncSession):
    query = select(UserToImage).filter_by(image_id=image.id, user_id=user_id)
    rating_obj = await db.execute(query)
    rating_obj = rating_obj.scalar_one_or_none()
    if rating_obj is not None:
        raise HTTPException(status_code=400, detail="You have already rated this image")
    if image.user_id == user_id:
        raise HTTPException(status_code=400, detail="You can't rate your own image")

    data = ImageRatingCreateSchema(image_id=image.id, rating=new_rating)
    new_rating_obj = UserToImage(**data.model_dump(exclude_unset=True), user_id=user_id)
    image.rating_count += 1
    image.average_rating = int((image.average_rating + new_rating*10) / image.rating_count)

    db.add(new_rating_obj)
    await db.commit()
    await db.refresh(new_rating_obj)
    await db.refresh(image)
    return image
