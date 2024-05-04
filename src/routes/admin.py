
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
    user = await repository_users.get_user_by_email(body.email, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await repository_admin.change_user_status(user, body.is_active, db)

    return {"message": f"User status changed to {'active' if body.is_active else 'inactive'}."}


@router.put("/{user_id}/change_role", dependencies=[Depends(role_admin)])
async def update_user_role(
    body: UserRoleUpdate = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    user = await repository_users.get_user_by_id(body.user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    await repository_admin.update_user_role(user, body.role, db)
    return {"message": f"User role updated to {body.role}"}


@router.delete('/admin/delete/{image_id}/delete_image', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(role_admin_moderator)])
async def admin_delete_image(body: ImageRequest = Depends(),
                             db: AsyncSession = Depends(get_db)):
    query = select(Image).filter_by(id=body.image_id)
    image = await repository_images.get_image(query, db)

    if image:
        image_name = await repository_images.get_filename_from_cloudinary_url(image.path)
        response = requests.get(image.path, stream=True)
        if response.status_code == 200:
            cloudinary.uploader.destroy(f'PhotoShareApp/{image_name}')
        await repository_images.delete_image_from_db(image, db)
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    
    
@router.put('/update/{image_id}/updata_image', response_model=ImageReadSchema, status_code=status.HTTP_200_OK, dependencies=[Depends(role_admin_moderator)])
async def update_image_by_admin(
        image_id: int,
        body: ImageUpdateSchema = Depends(),
        db: AsyncSession = Depends(get_db)
):
    query = select(Image).filter_by(id=image_id)
    image = await repository_images.get_image(query, db)
    if image:
        image = await repository_images.update_image_title(image, body.title, db)
        return image  
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    

@router.delete("/{comment_id}/delete_comment", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(role_admin_moderator)])
async def delete_comment(comment_id: int, 
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)
                         ):
    comment = await repository_admin.delete_comment(comment_id, db, user)
    return comment