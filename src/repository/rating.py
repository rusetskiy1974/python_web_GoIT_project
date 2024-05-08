import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.models import ImageRating
from src.schemas.rating import RatingCreateSchema
from src.repository import images as repository_images
from sqlalchemy.future import select


async def get_rating_by_user_and_image(user_id: uuid.UUID, image_id: int, db: AsyncSession):
    statement = select(ImageRating).where(
        ImageRating.user_id == user_id,
        ImageRating.image_id == image_id
    )
    result = await db.execute(statement)
    return result.scalars().first()

async def create_rating(user_id: uuid.UUID, image_id: int, rating: int, db: AsyncSession):
    rating_obj = ImageRating(user_id=user_id, image_id=image_id, rating=rating)
    db.add(rating_obj)
    await db.commit()
    return rating_obj

async def calculate_average_rating(image_id: int, db: AsyncSession):
    result = await db.execute(select(ImageRating).filter(ImageRating.image_id == image_id))
    ratings = await result.scalars().all()
    if not ratings:
        return 0
    total_rating = sum(rating.rating for rating in ratings)
    average_rating = total_rating / len(ratings)
    return average_rating

async def update_image_average_rating(image_id: int, average_rating: float, db: AsyncSession):
    image = await repository_images.get_image(image_id=image_id, db=db)
    if image:
        image.average_rating = average_rating
        await db.commit()
        return image
    else:
        raise ValueError("Image not found.")