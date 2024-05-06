import uuid

from fastapi import Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.database.db import get_db
from src.models.models import User, Role, BlackList
from src.schemas.user import UserCreateSchema


async def get_user_by_id(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> User | None:
    query = select(User).filter_by(id=user_id)
    user = await db.execute(query)
    return user.scalar_one_or_none()


async def create_user(body: UserCreateSchema, db: AsyncSession = Depends(get_db)) -> User:
    avatar = None
    try:
        g = Gravatar(email=body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    new_user = User(**body.model_dump(), avatar=avatar)

    query = select(func.count(User.id))
    count = await db.execute(query)
    user_count = count.scalar()
    if user_count == 0:
        new_user.role = Role.admin

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)) -> User | None:
    query = select(User).filter_by(email=email)
    user = await db.execute(query)
    return user.scalar_one_or_none()


async def update_token(user: User, token: str | None, db: AsyncSession):
    user.refresh_token = token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession):
    user = await get_user_by_email(email, db)
    user.confirmed = True
    user.is_active = True
    await db.commit()


async def update_avatar(email, url: str, db: AsyncSession) -> User:
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user


async def update_password(user: User, new_password: str, db: AsyncSession) -> User:
    user.password = new_password
    await db.commit()
    await db.refresh(user)
    return user


async def save_token_to_blacklist(user: User, token: str, db: AsyncSession):
    query = select(BlackList).filter_by(email=user.email)
    existing_record = await db.execute(query)
    token_to_blacklist = existing_record.scalar_one_or_none()
    if token_to_blacklist is not None:
        token_to_blacklist.token = token
    else:
        token_to_blacklist = BlackList(token=token, email=user.email)
        db.add(token_to_blacklist)

    await db.commit()
    await db.refresh(token_to_blacklist)
    return token_to_blacklist


async def find_black_list_token(email: str, db: AsyncSession):
    query = select(BlackList).filter_by(email=email)
    token = await db.execute(query)
    return token.unique().scalar_one_or_none()


async def clear_black_list_token(email: str, db: AsyncSession):
    query = select(BlackList).filter_by(email=email)
    token = await db.execute(query)
    token = token.unique().scalar_one_or_none()
    if token is not None:
        await db.delete(token)
        await db.commit()
