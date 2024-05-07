from sqlalchemy.ext.asyncio import AsyncSession
from src.models import Rating
from src.schemas import RatingCreateSchema
from src.repository import images as repository_images




def get_rating_by_user_and_image(self, user_id: int, image_id: int):
    return self.session.query(Rating).filter(Rating.user_id == user_id, Rating.image_id == image_id).first()

def create_rating(self, rating_data: RatingCreateSchema, user_id: int, image_id: int):
    rating = Rating(user_id=user_id, image_id=image_id, rating=rating_data.rating)
    self.session.add(rating)
    self.session.commit()
    self.session.refresh(rating)
    return rating
    

def get_ratings_for_image(self, image_id: int):
    return self.session.query(Rating).filter(Rating.image_id == image_id).all()

def calculate_average_rating(self, image_id: int):
    ratings = self.get_ratings_for_image(image_id)
    if not ratings:
        return 0
    total_rating = sum(rating.rating for rating in ratings)
    average_rating = total_rating / len(ratings)
    return average_rating
    

async def update_image_average_rating(image_id: int, average_rating: float, db: AsyncSession):
    image = await repository_images.get_image_by_id(image_id=image_id, db=db)
    if image:
        image.average_rating = average_rating
        await db.commit()
        await db.refresh(image)
    else:
        raise ValueError("Image not found.")
        
        