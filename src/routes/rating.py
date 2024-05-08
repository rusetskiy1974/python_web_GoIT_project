from fastapi import HTTPException, Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.rating import RatingCreateSchema
from src.repository import rating as repository_ratings
from src.database.db import get_db
from src.models.models import User
from src.services.auth import auth_service
from src.repository import images as repository_images

router = APIRouter(prefix="/rate", tags=["rate"])

@router.post("/rate/{image_id}")
async def rate_image(body: RatingCreateSchema = Depends(), 
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
    ):
    
    # Перевірка, чи користувач вже оцінив це зображення
    existing_rating = await repository_ratings.get_rating_by_user_and_image(
        user_id=current_user.id, image_id=body.image_id, db=db)
    if existing_rating:
        raise HTTPException(status_code=400, detail="You have already rated this image.")

    # Перевірка, чи користувач не оцінює свої власні зображення
    image = await repository_images.get_image(image_id=body.image_id, db=db)
    if image.owner == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot rate your own image.")

    # Перевірка діапазону рейтингу (від 1 до 5)
    if not 1 <= body.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating should be between 1 and 5.")

    # Створення нового рейтингу
    await repository_ratings.create_rating(
        user_id=current_user.id, image_id=body.image_id, rating=body.rating, db=db
    )

    # Оновлення середнього рейтингу зображення
    average_rating = await repository_ratings.calculate_average_rating(body.image_id, db)
    await repository_ratings.update_image_average_rating(body.image_id, average_rating, db)

    return {"message": "Rating added successfully."}