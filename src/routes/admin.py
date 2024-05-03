from typing import Optional
import uuid
import cloudinary.uploader
from fastapi import APIRouter, Form, HTTPException, Depends, Path, Query, Response, status
import requests
from sqlalchemy import select

from src.schemas.user import UserReadSchema
from src.schemas.image import ImageReadSchema  
from src.models.models import Image, User, Role
from src.services.role import RoleAccess
from src.services.auth import auth_service
from src.database.db import get_db
from src.repository.users import get_user_by_email
from src.repository import images as repository_images
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin", tags=["admin"])
role_admin = RoleAccess([Role.admin])


@router.put("/users/{email}/status", dependencies=[Depends(role_admin)])
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

@router.get('/all_images', response_model=list[ImageReadSchema], dependencies=[Depends(role_admin)])
async def get_all_images_of_all_users(email: Optional[str] = None, limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0),
                                      db: AsyncSession = Depends(get_db)):
    if email:
        user = await get_user_by_email(email, db)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        query = select(Image).filter_by(user_id=user.id).offset(offset).limit(limit)
    else:
        query = select(Image).offset(offset).limit(limit)
    
    result = await repository_images.get_images(query, db)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No images found.")
    return result

@router.delete('/admin/delete/{image_id}', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(role_admin)])
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
    
    
@router.put('/update/{image_id}', response_model=ImageReadSchema, status_code=status.HTTP_200_OK, dependencies=[Depends(role_admin)])
async def update_image_by_admin(
        image_id: int = Path(..., title="The ID of the image to update"),
        title: str = Form(None, min_length=3, max_length=50, title="New title for the image (optional)"),
        tags: list[str] = Form([], title="List of tags to update"),
        current_user: User = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    query = select(Image).filter_by(id=image_id)
    image = await repository_images.get_image(query, db)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    if title is not None:
        image = await repository_images.update_image_title(image, title, db)
    if tags:
        await repository_images.add_tag_to_image(image, tags, db)

    return image