
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import User, Comment, Image


async def create_comment(image_id: int,
                         text: str,
                         db: AsyncSession,
                         user: User):

    """
    The create_comment function creates a comment for an image.

    :param image_id: int: Specify the image that the comment is being made on
    :param text: str: Store the text of the comment
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the user_id from the user object
    :return: The comment object if it is created successfully
    :doc-author: RSA
    """
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
    """
    The get_comments function returns a list of comments for the image with the given id.
    The limit and offset parameters are used to paginate through results.


    :param image_id: int: Filter the comments by image_id
    :param limit: int: Limit the number of comments returned
    :param offset: int: Get the comments after a certain number of comments
    :param db: AsyncSession: Pass the database session to the function
    :return: A list of comments for the given image
    :doc-author: RSA
    """
    stmt = select(Comment).filter_by(image_id=image_id).offset(offset).limit(limit)
    comments = await db.execute(stmt)
    return comments.scalars().all()


async def update_contact(comment_id: int, text: str, db: AsyncSession, user: User):

    """
    The update_contact function updates a contact in the database.

    :param comment_id: int: Identify the comment that is to be updated
    :param text: str: Update the text of a comment
    :param db: AsyncSession: Connect to the database
    :param user: User: Make sure that the user who is updating the comment is also
    :return: A comment object
    :doc-author: RSA
    """
    stmt = select(Comment).filter_by(id=comment_id, user_id=user.id)
    result = await db.execute(stmt)
    comment = result.scalar_one_or_none()
    if comment:
        comment.text = text
        await db.commit()
        await db.refresh(comment)
    return comment


async def delete_comment(comment_id: int, db: AsyncSession, user: User):
    """
    The delete_comment function deletes a comment from the database.
        Args:
            comment_id (int): The id of the comment to be deleted.
            db (AsyncSession): An async session object for interacting with the database.
            user (User): A User object representing who is deleting this post, used for authorization purposes.

    :param comment_id: int: Find the comment to delete
    :param db: AsyncSession: Access the database
    :param user: User: Ensure that the user is authorized to delete the comment
    :return: The comment that was deleted, or none if no comment was found
    :doc-author: RSA
    """
    stmt = select(Comment).filter_by(id=comment_id)
    comment = await db.execute(stmt)
    comment = comment.scalar_one_or_none()
    if comment:
        await db.delete(comment)
        await db.commit()
    return comment
