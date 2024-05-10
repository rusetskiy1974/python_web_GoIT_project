import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.models import UserToImage, Image, User
from src.repository.images import get_image
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
    # image.rating_count += 1
    # image.average_rating = int((image.average_rating + new_rating * 10) / image.rating_count)
    #
    db.add(new_rating_obj)
    await db.commit()
    await db.refresh(new_rating_obj)

    return await get_image_rating(image, db)


async def get_all_ratings(limit, offset, db: AsyncSession):
    query = select(UserToImage).offset(offset).limit(limit)
    ratings = await db.execute(query)
    return ratings.scalars().all()


async def get_rating(rating_id, db: AsyncSession):
    query = select(UserToImage).filter_by(id=rating_id)
    rating = await db.execute(query)
    return rating.scalar_one_or_none()


class ImageRating:
    pass


async def get_image_rating(image: Image, db: AsyncSession):
    query = select(UserToImage).filter_by(image_id=image.id)
    image_rating = await db.execute(query)
    image_rating = image_rating.scalars().all()
    total_rating = sum(map(lambda x: x.rating, image_rating))
    num_ratings = len(image_rating)
    if num_ratings == 0:
        average_rating = 0
    else:
        average_rating = int(total_rating / num_ratings * 10)
    image.average_rating = average_rating
    await db.commit()
    await db.refresh(image)
    return image


async def delete_rating(rating, db: AsyncSession):
    image = await get_image(rating.image_id, db)
    await db.delete(rating)
    await db.commit()
    return await get_image_rating(image, db)
