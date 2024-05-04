
from typing import Optional
import uuid
import cloudinary.uploader
from fastapi import APIRouter, Form, HTTPException, Depends, Path, Query, Response, status
import requests
from sqlalchemy import select

from src.schemas.user import UserReadSchema
from src.schemas.image import ImageReadSchema, ImageUpdateSchema
from src.models.models import Image, User, Role
from src.services.role import RoleAccess
from src.services.auth import auth_service
from src.database.db import get_db
from src.repository.users import get_user_by_email, get_user_by_id
from src.repository import images as repository_images
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin", tags=["admin"])
role_admin = RoleAccess([Role.admin])
role_admin_moderator = RoleAccess([Role.admin, Role.moderator])

@router.put("/users/{email}/block", dependencies=[Depends(role_admin)])
async def change_user_status_by_email(
        is_active: bool,
        email: str = Path(..., title="The email of the user whose status to change"),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user)
):
    user = await get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

   
    user.is_active = False
    await db.commit()
    await db.refresh(user)

    return {"message": f"User status changed to {'active' if is_active else 'inactive'}."}

@router.put("/{email}/unblock", response_model=UserReadSchema, dependencies=[Depends(role_admin)])
async def unblock_user_by_email(
        email: str = Path(..., title="The email of the user to unblock"),
        current_user: User = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db),
):
    # Get the user by email from the database
    user = await get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Set the user's is_active status to True to unblock the user
    user.is_active = True
    await db.commit()

    return user


@router.delete('/admin/delete/{image_id}', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(role_admin_moderator)])
async def admin_delete_image(image_id: int = Path(..., description="The ID of the image to delete"),
                             db: AsyncSession = Depends(get_db)):
    query = select(Image).filter_by(id=image_id)
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
    
    
@router.put('/update/{image_id}', response_model=ImageReadSchema, status_code=status.HTTP_200_OK, dependencies=[Depends(role_admin_moderator)])
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

@router.put("/{user_id}/change_role", dependencies=[Depends(role_admin)])
async def update_user_role(
    user_id: uuid.UUID,
    role: Role,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    user = await get_user_by_id(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.role = role
    await db.commit()
    await db.refresh(user)
    return {"message": f"User role updated to {role}"}