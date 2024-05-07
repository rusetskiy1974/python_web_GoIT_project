from sqlalchemy import select
from src.models.models import User, Role, Comment
from sqlalchemy.ext.asyncio import AsyncSession


async def change_user_status(user: User, is_active: bool, db: AsyncSession):

    """
    The change_user_status function changes the is_active status of a user.

    :param user: User: Pass in the user that we want to change
    :param is_active: bool: Set the user's status to active or inactive
    :param db: AsyncSession: Pass the database session to the function
    :return: None
    :doc-author: RSA
    """
    user.is_active = is_active
    await db.commit()
    await db.refresh(user)


async def update_user_role(user: User, role: Role, db: AsyncSession):
    """
    The update_user_role function updates the role of a user.

    :param user: User: Pass in the user object that we want to update
    :param role: Role: Pass in the role that we want to update the user with
    :param db: AsyncSession: Pass the database session to the function
    :return: A coroutine object
    :doc-author: RSA
    """
    user.role = role
    await db.commit()
    await db.refresh(user)


async def delete_comment(comment_id: int, db: AsyncSession, user: User):
    """
    The delete_comment function deletes a comment from the database.
        Args:
            comment_id (int): The id of the comment to be deleted.
            db (AsyncSession): An async session object for interacting with the database.
            user (User): A User object representing who is making this request, used for authorization purposes.

    :param comment_id: int: Specify the comment to delete
    :param db: AsyncSession: Pass in the database session
    :param user: User: Check if the user is allowed to delete the comment
    :return: The comment that was deleted, or none if the comment didn't exist
    :doc-author: RSA
    """
    stmt = select(Comment).filter_by(id=comment_id)
    comment = await db.execute(stmt)
    comment = comment.scalar_one_or_none()
    if comment:
        await db.delete(comment)
        await db.commit()
    return comment
