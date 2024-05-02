from datetime import date, timedelta

from sqlalchemy import select, or_, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.comments import CommentCreateSchema
from src.models.models import User, Comment, Image

async def create_comment(image_id: int,
                         text: str,
                         db: AsyncSession, 
                         user: User):
    comment = Comment(
        text=text,
        image_id=image_id,
        user=user) 
    db.add(comment)
    try:
        await db.commit()
        await db.refresh(comment)
        return comment
    except Exception as err:
        return None