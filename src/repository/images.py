import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.models.models import Image, Tag, User
from src.conf.config import settings
from src.schemas.image import ImageCreateSchema


async def get_image(image_id: int, db: AsyncSession):
    query = select(Image).filter_by(id=image_id)
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()


async def get_images(limit: int, offset: int, db: AsyncSession):
    query = select(Image).offset(offset).limit(limit)
    images = await db.execute(query)
    return images.unique().scalars().all()


async def get_user_image(image_id: int, user: User, db: AsyncSession):
    query = select(Image).filter_by(id=image_id).filter_by(user_id=user.id)
    images = await db.execute(query)
    return images.unique().scalar_one_or_none()


async def get_user_images(limit: int, offset: int, user: User, db: AsyncSession):
    query = select(Image).filter_by(user_id=user.id).offset(offset).limit(limit)
    images = await db.execute(query)
    return images.unique().scalars().all()


async def get_tag(tag_name: str, db: AsyncSession):
    query = select(Tag).filter_by(name=tag_name)
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()


# Get file size
async def get_file_size(file):
    file_content = await file.read()
    file_size = len(file_content)
    await file.seek(0)
    return file_size


async def file_is_image(file: UploadFile):
    if file.content_type.startswith("image"):
        return True
    else:
        return False


# Update File in DB
async def update_image_title(image: Image, title: str, db: AsyncSession):
    image.title = title
    await db.commit()
    await db.refresh(image)
    return image


# Delete image from DB
async def delete_image_from_db(image: Image, db: AsyncSession):
    await db.delete(image)
    await db.commit()


async def get_images_by_tag(tag_name: str, limit: int, offset: int, db: AsyncSession):
    query = select(Tag).filter_by(name=tag_name)
    tag = await db.execute(query)
    tag = tag.unique().scalar_one_or_none()
    if tag:
        query = (
            select(Image).filter(Image.tags.contains(tag)).offset(offset).limit(limit)
        )
        images = await db.execute(query)
        return images.unique().scalars().all()
    return


async def add_tag_to_image(image_id: int, tag_name: str, db: AsyncSession):
    query = select(Image).filter_by(id=image_id)
    image = await db.execute(query)
    image = image.unique().scalar_one_or_none()
    tag = await create_tag(tag_name.strip(), db)
    if image:
        if tag not in image.tags and image.count_tags <= settings.max_add_tags - 1:
            image.count_tags += 1
            image.tags.append(tag)
            await db.commit()
            await db.refresh(image)
            return image
        else:
            if tag in image.tags:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tag is already added to image",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"You can't add more than {settings.max_add_tags} tags to image",
                )

    return


async def delete_tag_from_image(image_id: int, tag_name: str, db: AsyncSession):
    # query = select(Image).filter_by(id=image_id)
    # image = await db.execute(query)
    image = await get_image(image_id, db)
    tag = await get_tag(tag_name.strip(), db)
    if image:
        if tag in image.tags:
            image.tags.remove(tag)
            image.count_tags -= 1
            await db.commit()
            await db.refresh(image)
            return image
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No tag: {tag_name} on this image",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No image with id: {image_id}",
        )


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


async def create_image(user: User, db: AsyncSession, **kwargs):
    data = ImageCreateSchema(title=kwargs['title'], path=kwargs['image_path'])
    new_image = Image(**data.model_dump(exclude_unset=True), size=kwargs['size'], user_id=user.id)

    if kwargs['tag']:
        tag = await create_tag(kwargs['tag'], db)
        new_image.count_tags = 1
        new_image.tags.append(tag)
    db.add(new_image)
    await db.commit()
    await db.refresh(new_image)
    return new_image


async def format_filename():
    new_filename = f"{uuid4().hex}"
    return new_filename


async def get_filename_from_cloudinary_url(cloudinary_url):
    # Розділіть URL за допомогою /
    parts = cloudinary_url.split("/")
    # Останній елемент списку є ім'ям файлу
    filename = parts[-1]
    return filename


async def get_user_by_email(email: str, db: AsyncSession):
    query = select(User).where(User.email == email)
    user = await db.execute(query)
    return user.unique().scalar_one_or_none()
