from typing import Optional
import cloudinary.uploader
from fastapi import APIRouter, Form, HTTPException, Depends, Path, Query, Response, status
import requests
from sqlalchemy import select

from src.repository import admin as repository_admin
from src.schemas.admin import ImageRequest, UserRoleUpdate, UserStatusUpdate
from src.schemas.user import UserReadSchema
from src.schemas.image import ImageReadSchema, ImageUpdateSchema
from src.models.models import Image, User, Role
from src.services.role import RoleAccess
from src.services.auth import auth_service
from src.database.db import get_db
from src.repository import users as repository_users
from src.repository import images as repository_images
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin", tags=["admin"])
role_admin = RoleAccess([Role.admin])
role_admin_moderator = RoleAccess([Role.admin, Role.moderator])


@router.put("/users/block", dependencies=[Depends(role_admin)])
async def change_user_status_by_email(
        body: UserStatusUpdate = Depends(),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user)
):
    """
    The change_user_status_by_email function changes the status of a user by email.

    :param body: UserStatusUpdate: Get the email and is_active values from the request body
    :param db: AsyncSession: Get the database session
    :param current_user: User: Get the current user
    :return: A dictionary with a message
    :doc-author: RSA
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    await repository_admin.change_user_status(user, body.is_active, db)

    return {"message": f"User status changed to {'active' if body.is_active else 'inactive'}."}


@router.put("/unblock", dependencies=[Depends(role_admin)])
async def unblock_user_by_email(
        body: UserStatusUpdate = Depends(),
        current_user: User = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """
    The unblock_user_by_email function is used to unblock a user by email.
    It takes in the body of the request, which contains an email and a boolean value for whether or not they are active.
    The function then gets the user from the database using their email address, and if it finds them, changes their
    status to active or inactive depending on what was passed in.

    :param body: UserStatusUpdate: Get the email and is_active parameters from the request body
    :param current_user: User: Get the current user
    :param db: AsyncSession: Pass the database connection to the function
    :param : Get the user's email address
    :return: A dict with a message
    :doc-author: RSA
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await repository_admin.change_user_status(user, body.is_active, db)

    return {"message": f"User status changed to {'active' if body.is_active else 'inactive'}."}


@router.put("/{user_id}/change_role", dependencies=[Depends(role_admin)])
async def update_user_role(
        body: UserRoleUpdate = Depends(),
        db: AsyncSession = Depends(get_db)
        ):
    """
    The update_user_role function updates the role of a user.

    :param body: UserRoleUpdate: Get the user_id and role from the request body
    :param db: AsyncSession: Get the database session
    :return: A dictionary with the message key
    :doc-author: RSA
    """
    user = await repository_users.get_user_by_id(body.user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    await repository_admin.update_user_role(user, body.role, db)
    return {"message": f"User role updated to {body.role}"}


@router.delete('/admin/delete/{image_id}/delete_image', status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(role_admin_moderator)])
async def admin_delete_image(body: ImageRequest = Depends(),
                             db: AsyncSession = Depends(get_db)):
    """
    The admin_delete_image function is used to delete an image from the database and cloudinary.
    The function takes in a body of type ImageRequest, which contains the id of the image to be deleted.
    It then queries for that image in the database, and if it exists, deletes it from both cloudinary
    and our own database.

    :param body: ImageRequest: Get the image_id from the request body
    :param db: AsyncSession: Get the database session
    :return: A 204 status code if the image was successfully deleted
    :doc-author: RSA
    """
    image = await repository_images.get_image(body.image_id, db)

    if image:
        image_name = await repository_images.get_filename_from_cloudinary_url(image.path)
        # response = requests.get(image.path, stream=True)
        # if response.status_code == 200:
        try:
            cloudinary.uploader.destroy(f'PhotoShareApp/{image_name}')
            await repository_images.delete_image_from_db(image, db)

            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except Exception:
            await repository_images.delete_image_from_db(image, db)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


@router.put('/update/{image_id}/updata_image', response_model=ImageReadSchema, status_code=status.HTTP_200_OK,
            dependencies=[Depends(role_admin_moderator)])
async def update_image_by_admin(
        body: ImageUpdateSchema = Depends(),
        db: AsyncSession = Depends(get_db)
):

    """
    The update_image_by_admin function updates the title of an image.
    The function takes in a body parameter, which is a dictionary containing the image_id and title of the image to be updated.
    The function also takes in a db parameter, which is an async session object that allows us to interact with our database.

    :param body: ImageUpdateSchema: Get the image_id and title from the request body
    :param db: AsyncSession: Get the database session
    :return: The updated image
    :doc-author: RSA
    """
    image = await repository_images.get_image(body.image_id, db)
    if image:
        image = await repository_images.update_image_title(image, body.title, db)
        return image
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


@router.delete("/{comment_id}/delete_comment", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(role_admin_moderator)])
async def delete_comment(comment_id: int,
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)
                         ):
    """
    The delete_comment function deletes a comment from the database.
        The function takes in an integer representing the id of the comment to be deleted,
        and returns a Comment object that has been deleted.

    :param comment_id: int: Identify the comment to be deleted
    :param db: AsyncSession: Pass the database session to the repository layer
    :param user: User: Get the current user
    :return: The comment that was deleted
    :doc-author: RSA
    """
    comment = await repository_admin.delete_comment(comment_id, db, user)
    return comment

