
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.models.models import User, Role
from src.services.auth import auth_service
from src.schemas.comments import CommentResponseShema, CommentResponseShemaLight
from src.repository import comments as repository_comments

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post('/', response_model=CommentResponseShema, status_code=status.HTTP_201_CREATED)
async def create_comment(image_id: int,
                         text: str,
                         db: AsyncSession = Depends(get_db),
                         user=Depends(auth_service.get_current_user)
                         ):
    """
    The create_comment function creates a new comment for an image.
    The function takes the following parameters:
        - image_id: int, the id of the image to which we want to add a comment.
        - text: str, the text of our new comment.

    :param image_id: int: Specify the image that the comment is being made on
    :param text: str: Get the text of the comment from the request body
    :param db: AsyncSession: Pass the database connection to the function
    :param user: Get the current user
    :return: A comment object
    :doc-author: RSA
    """
    comment = await repository_comments.create_comment(image_id, text, db, user)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Oooops")
    return comment


@router.get('/all', response_model=list[CommentResponseShemaLight])
async def get_comments(
        image_id: int,
        limit: int = Query(10, ge=10, le=500),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db)
):
    """
    The get_comments function returns a list of comments for the image with the given id.
    The limit and offset parameters are used to paginate through results.

    :param image_id: int: Specify the image id of the comment
    :param limit: int: Limit the number of comments returned
    :param ge: Specify the minimum value of the limit parameter
    :param le: Set a maximum value for the limit parameter
    :param offset: int: Specify the offset of the first comment to be returned
    :param ge: Specify a minimum value for the integer, and le is used to specify a maximum
    :param db: AsyncSession: Pass the database session to the function
    :return: A list of comments for the image with the given id
    :doc-author: RSA
    """
    comments = await repository_comments.get_comments(image_id, limit, offset, db)
    return comments


@router.put("/{comment_id}", response_model=CommentResponseShema)
async def update_comment(comment_id: int,
                         text: str,
                         db: AsyncSession = Depends(get_db),
                         user=Depends(auth_service.get_current_user)
                         ):
    """
    The update_comment function updates a comment in the database.
    The function takes an id of the comment to be updated, and a new text for that comment.
    It returns the updated contact.

    :param comment_id: int: Specify the id of the comment to be deleted
    :param text: str: Update the text of a comment
    :param db: AsyncSession: Access the database
    :param user: Get the current user from the auth_service
    :return: A comment object
    :doc-author: RSA
    """
    comment = await repository_comments.update_contact(comment_id, text, db, user)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: int,
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)
                         ):
    """
    The delete_comment function deletes a comment from the database.
    The function takes in an integer representing the id of the comment to be deleted,
    and returns a dictionary containing information about that comment.

    :param comment_id: int: Specify the id of the comment to be deleted
    :param db: AsyncSession: Get the database connection
    :param user: User: Get the current user
    :return: A comment object
    :doc-author: RSA
    """
    if user.role == Role.user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="U cann't do it")
    comment = await repository_comments.delete_comment(comment_id, db, user)
    return comment
