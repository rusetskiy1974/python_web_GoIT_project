import uuid

from fastapi import Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.database.db import get_db
from src.models.models import User, Role
from src.schemas.user import UserCreateSchema


async def get_user_by_id(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> User | None:
    """
    The get_user_by_id function returns a user object from the database, given an id.

    :param user_id: uuid.UUID: Specify the type of the user_id parameter
    :param db: AsyncSession: Pass the database session to the function
    :return: A user object or none if the user is not found
    :doc-author: RSA
    """
    query = select(User).filter_by(id=user_id)
    user = await db.execute(query)
    return user.scalar_one_or_none()


async def create_user(body: UserCreateSchema, db: AsyncSession = Depends(get_db)) -> User:
    """
    The create_user function creates a new user in the database.

    :param body: UserCreateSchema: Validate the request body
    :param db: AsyncSession: Pass the database session to the function
    :return: A user object
    :doc-author: RSA
    """
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
    """
    The get_user_by_email function takes an email address and returns the user associated with that email.
    If no such user exists, it returns None.

    :param email: str: Pass in the email of the user we want to retrieve
    :param db: AsyncSession: Pass in the database session
    :return: A user object or none if no user with the given email exists
    :doc-author: RSA
    """
    query = select(User).filter_by(email=email)
    user = await db.execute(query)
    return user.unique().scalar_one_or_none()


async def update_token(user: User, token: str | None, db: AsyncSession):
    """
    The update_token function updates the refresh token for a user.

    :param user: User: Identify the user to update
    :param token: str | None: Update the refresh token of the user
    :param db: AsyncSession: Pass the database session to the function
    :return: The user object
    :doc-author: RSA
    """
    user.refresh_token = token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession):
    """
    The confirmed_email function takes in an email and a database session,
    and sets the confirmed field of the user with that email to True.
    It also sets their is_active field to True.

    :param email: str: Get the email of the user
    :param db: AsyncSession: Pass the database connection to the function
    :return: A boolean value of true if the user's email has been confirmed
    :doc-author: RSA
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    user.is_active = True
    await db.commit()


async def update_avatar(email, url: str, db: AsyncSession) -> User:
    """
    The update_avatar function updates the avatar of a user.

    :param email: Find the user in the database
    :param url: str: Specify the type of the parameter
    :param db: AsyncSession: Pass in the database session
    :return: The updated user object
    :doc-author: RSA
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user


async def update_password(user: User, new_password: str, db: AsyncSession) -> User:
    """
    The update_password function takes a user object, a new password string, and an async database session.
    It updates the user's password to the new_password string and commits it to the database.
    Then it refreshes that user object from the database so that we can be sure we have all of its attributes.

    :param user: User: Pass in the user object that we want to update
    :param new_password: str: Pass the new password to the function
    :param db: AsyncSession: Pass in the database session
    :return: The updated user object
    :doc-author: RSA
    """
    user.password = new_password
    await db.commit()
    await db.refresh(user)
    return user
