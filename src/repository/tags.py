from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import Tag


async def create_tag(tag_name: str, db: AsyncSession):
    query = select(Tag).filter_by(name=tag_name)
    tag = await db.execute(query)
    tag = tag.unique().scalar_one_or_none()
    if tag is None:
        new_tag = Tag(name=tag_name)
        db.add(new_tag)
        await db.commit()
        await db.refresh(new_tag)
        return new_tag
    return tag
