
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import User, Comment, Image


async def create_comment(image_id: int,
                         text: str,
                         db: AsyncSession,
                         user: User):
    stmt = select(Image).filter_by(id=image_id)
    result = await db.execute(stmt)
    image_exist = result.unique().scalar_one_or_none()
    if image_exist is None:
        return None
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
        print(err)
        return None


async def get_comments(image_id: int, limit: int, offset: int, db: AsyncSession):
    stmt = select(Comment).filter_by(image_id=image_id).offset(offset).limit(limit)
    comments = await db.execute(stmt)
    return comments.scalars().all()


async def update_contact(comment_id: int, text: str, db: AsyncSession, user: User):
    stmt = select(Comment).filter_by(id=comment_id, user_id=user.id)
    result = await db.execute(stmt)
    comment = result.scalar_one_or_none()
    if comment:
        comment.text = text
        await db.commit()
        await db.refresh(comment)
    return comment


async def delete_comment(comment_id: int, db: AsyncSession, user: User):
    stmt = select(Comment).filter_by(id=comment_id)
    comment = await db.execute(stmt)
    comment = comment.scalar_one_or_none()
    if comment:
        await db.delete(comment)
        await db.commit()
    return comment
