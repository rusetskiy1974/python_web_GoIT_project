from sqlalchemy import select
from src.models.models import User, Role, Comment
from sqlalchemy.ext.asyncio import AsyncSession


async def change_user_status(user: User, is_active: bool, db: AsyncSession):
    user.is_active = is_active
    await db.commit()
    await db.refresh(user)


async def update_user_role(user: User, role: Role, db: AsyncSession):
    user.role = role
    await db.commit()
    await db.refresh(user)


async def delete_comment(comment_id: int, db: AsyncSession, user: User):
    stmt = select(Comment).filter_by(id=comment_id)
    comment = await db.execute(stmt)
    comment = comment.scalar_one_or_none()
    if comment:
        await db.delete(comment)
        await db.commit()
    return comment
