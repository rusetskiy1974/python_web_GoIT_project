
from uuid import uuid4

from fastapi import UploadFile, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.models.models import Image, Tag, User
from src.conf.config import settings
from src.schemas.image import ImageCreateSchema


async def get_image(image_id: int, db: AsyncSession):
    """
    The get_image function takes an image_id and a database session as arguments.
    It then queries the Image table for the row with that id, returning it if found.

    :param image_id: int: Specify the image id to search for
    :param db: AsyncSession: Pass the database session to the function
    :return: An image object
    :doc-author: RSA
    """
    query = select(Image).filter_by(id=image_id)
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()


async def get_images(limit: int, offset: int, db: AsyncSession):
    """
    The get_images function returns a list of images from the database.

    :param limit: int: Limit the number of images returned
    :param offset: int: Get the next set of images
    :param db: AsyncSession: Pass the database session to the function
    :return: A list of image objects
    :doc-author: RSA
    """
    query = select(Image).order_by(Image.average_rating.desc()).offset(offset).limit(limit)
    images = await db.execute(query)
    return images.unique().scalars().all()


async def get_user_image(image_id: int, user: User, db: AsyncSession):
    """
    The get_user_image function is used to retrieve a single image from the database.
    It takes in an image_id and user object, and returns a single Image object if it exists.


    :param image_id: int: Filter the images by id
    :param user: User: Filter the images by user
    :param db: AsyncSession: Pass the database session to the function
    :return: The image that matches the given id and user
    :doc-author: RSA
    """
    query = select(Image).filter_by(id=image_id).filter_by(user_id=user.id)
    images = await db.execute(query)
    return images.unique().scalar_one_or_none()


async def get_user_images(limit: int, offset: int, user: User, db: AsyncSession):
    """
    The get_user_images function returns a list of images for the given user.

    :param limit: int: Limit the number of images returned
    :param offset: int: Determine the offset of images to return
    :param user: User: Get the user_id of the user
    :param db: AsyncSession: Pass the database session to the function
    :return: A list of images
    :doc-author: RSA
    """
    query = select(Image).filter_by(user_id=user.id).offset(offset).limit(limit)
    images = await db.execute(query)
    return images.unique().scalars().all()


async def get_tag(tag_name: str, db: AsyncSession):
    """
    The get_tag function takes a tag name and an async database session as arguments.
    It then creates a query to select the Tag object with the given name from the database.
    The result of this query is returned asynchronously.

    :param tag_name: str: Specify the name of the tag to be retrieved
    :param db: AsyncSession: Pass the database session into the function
    :return: A single row from the database
    :doc-author: RSA
    """
    query = select(Tag).filter_by(name=tag_name)
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()


# Get file size
async def get_file_size(file):
    """
    The get_file_size function takes a file object as an argument and returns the size of that file in bytes.
    The function first reads the entire contents of the file into memory, then uses Python's built-in len() function to get
    the length (i.e., number of characters) in that string, which is equivalent to getting the size of a binary file.

    :param file: Pass in the file object
    :return: The size of the file in bytes
    :doc-author: RSA
    """
    file_content = await file.read()
    file_size = len(file_content)
    await file.seek(0)
    return file_size


async def file_is_image(file: UploadFile):
    """
    The file_is_image function checks if the file is an image.


    :param file: UploadFile: Check if the file is an image
    :return: A boolean value
    :doc-author: RSA
    """
    if file.content_type.startswith("image"):
        return True
    else:
        return False


# Update File in DB
async def update_image_title(image: Image, title: str, db: AsyncSession):
    """
    The update_image_title function updates the title of an image.

    :param image: Image: Pass the image object to the function
    :param title: str: Pass in the new title for the image
    :param db: AsyncSession: Pass the database session to the function
    :return: The updated image object
    :doc-author: RSA
    """
    image.title = title
    await db.commit()
    await db.refresh(image)
    return image


# Delete image from DB
async def delete_image_from_db(image: Image, db: AsyncSession):
    """
    The delete_image_from_db function deletes an image from the database.

    :param image: Image: Pass the image object to be deleted
    :param db: AsyncSession: Pass the database session to the function
    :return: A coroutine
    :doc-author: RSA
    """
    await db.delete(image)
    await db.commit()


async def get_images_by_tag(tag_name: str, limit: int, offset: int, db: AsyncSession):
    """
    The get_images_by_tag function takes in a tag name, limit, offset and database session.
    It then queries the Tag table for the given tag name. If it finds a match it will query
    the Image table for all images that contain that tag and return them as an array of image objects.

    :param tag_name: str: Filter the images by tag name
    :param limit: int: Limit the number of images returned
    :param offset: int: Skip a certain number of images
    :param db: AsyncSession: Pass in the database session to the function
    :return: A list of images with a given tag
    :doc-author: RSA
    """
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
    """
    The add_tag_to_image function adds a tag to an image.
    Args:
        image_id (int): The id of the image to add a tag to.
        tag_name (str): The name of the new tag.

    :param image_id: int: Get the image from the database
    :param tag_name: str: Get the tag name
    :param db: AsyncSession: Pass the database session to the function
    :return: An image object
    :doc-author: RSA
    """
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
    """
    The delete_tag_from_image function deletes a tag from an image.
    Args:
        image_id (int): The id of the image to delete the tag from.
        tag_name (str): The name of the tag to be deleted.

    :param image_id: int: Find the image in the database
    :param tag_name: str: Specify the tag name to be deleted from the image
    :param db: AsyncSession: Pass the database session into the function
    :return: The image object with the tag removed
    :doc-author: RSA
    """
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
    """
    The create_tag function takes a tag name and an async database session as arguments.
    It then queries the database for a tag with that name, if it exists. If it does not exist,
    it creates one and returns the new Tag object.

    :param tag_name: str: Specify the name of the tag to be created
    :param db: AsyncSession: Pass in the database session
    :return: A tag object
    :doc-author: RSA
    """
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
    """
    The create_image function creates a new image in the database.
    Args:
        user (User): The user who is creating the image.
        db (AsyncSession): An async session to interact with the database.

    :param user: User: Get the user id of the image
    :param db: AsyncSession: Access the database
    :param **kwargs: Pass in the arguments of the function
    :return: An image object
    :doc-author: RSA
    """
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
    """
    The format_filename function takes no arguments and returns a string.
    The string is the filename of an image that has been uploaded to the server,
    with its extension removed and replaced with a UUID4 hexadecimal identifier.

    :return: A random string of 32 characters
    :doc-author: RSA
    """
    new_filename = f"{uuid4().hex}"
    return new_filename


async def get_filename_from_cloudinary_url(cloudinary_url):
    """
    The get_filename_from_cloudinary_url function takes a Cloudinary URL as input and returns the filename of the image.

    :param cloudinary_url: Get the filename from the url
    :return: The filename from the cloudinary url
    :doc-author: RSA
    """
    parts = cloudinary_url.split("/")
    filename = parts[-1]
    return filename


async def get_user_by_email(email: str, db: AsyncSession):
    """
    The get_user_by_email function takes in an email and a database session,
    and returns the user with that email. If no such user exists, it returns None.

    :param email: str: Specify the email of the user we want to retrieve
    :param db: AsyncSession: Pass in the database session
    :return: A user object
    :doc-author: RSA
    """
    query = select(User).where(User.email == email)
    user = await db.execute(query)
    return user.unique().scalar_one_or_none()
