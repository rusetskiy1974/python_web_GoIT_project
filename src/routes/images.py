from io import BytesIO
from typing import Optional, List

import cloudinary
import cloudinary.uploader
import requests
from PIL import Image

from fastapi import UploadFile, APIRouter, HTTPException, status, Depends, File, Form, Query, Path, Response
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse, FileResponse

from src.database.db import get_db
from src.models.models import User
from src.conf.config import settings
from src.services.auth import auth_service
from src.schemas.image import ImageCreateSchema, ImageReadSchema, ImageUpdateSchema
from src.repository import images as repository_images
from src.services.role import RoleAccess

router = APIRouter(prefix='/images', tags=['image'])

cloudinary.config(
    cloud_name=settings.cloudinary_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True
)


@router.get('/tag/{tag}', response_model=List[ImageReadSchema], status_code=status.HTTP_200_OK)
async def get_images_by_tag(tag: str = Path(description="Input tag", min_length=3, max_length=50),
                            limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0),
                            db: AsyncSession = Depends(get_db)):
    """
    The get_images_by_tag function returns a list of images that have the specified tag.
    The function takes in an optional limit and offset query parameters to control how many results are returned,
    and where in the result set they start from. The default values for these parameters are 10 and 0 respectively.

    :param tag: str: Get the tag from the request url
    :param min_length: Specify the minimum length of the tag
    :param max_length: Limit the length of the input tag
    :param limit: int: Limit the number of images returned
    :param ge: Specify the minimum value of a parameter
    :param le: Limit the number of images returned
    :param offset: int: Specify the number of images to skip
    :param ge: Check if the value is greater than or equal to the given number
    :param db: AsyncSession: Get the database session
    :return: A list of images that contain the tag
    :doc-author: RSA
    """
    images = await repository_images.get_images_by_tag(tag, limit, offset, db)
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TAG NOT EXISTS")
    return images


@router.post('/{image_id}/tag/{tag}', response_model=ImageReadSchema, status_code=status.HTTP_200_OK)
async def add_tag_to_image(image_id: int = Path(ge=1),
                           tag: str = Path(description="Input tag", min_length=3, max_length=50),
                           db: AsyncSession = Depends(get_db)):
    """
    The add_tag_to_image function adds a tag to an image.

    :param image_id: int: Specify the image id
    :param tag: str: Get the tag from the path
    :param min_length: Specify the minimum length of a string
    :param max_length: Limit the length of the input string
    :param db: AsyncSession: Pass the database session to the repository layer
    :return: A dictionary with the following structure:
    :doc-author: RSA
    """
    result = await repository_images.add_tag_to_image(image_id, tag, db)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IMAGE NOT EXISTS")
    return result


@router.delete('/{image_id}/tag/{tag}', response_model=ImageReadSchema, status_code=status.HTTP_200_OK)
async def delete_tag_from_image(
        image_id: int = Path(ge=1),
        tag: str = Path(description="Input tag to delete", min_length=3, max_length=50),
        db: AsyncSession = Depends(get_db)
):
    """
    The delete_tag_from_image function deletes a tag from an image.
    Args:
        image_id (int): The id of the image to delete the tag from.
        tag (str): The name of the tag to delete.

    :param image_id: int: Specify the image id of the image to be deleted
    :param tag: str: Get the tag from the url path
    :param min_length: Specify the minimum length of a string
    :param max_length: Limit the length of the input string
    :param db: AsyncSession: Get the database connection
    :return: The number of rows affected by the query
    :doc-author: RSA
    """
    result = await repository_images.delete_tag_from_image(image_id, tag.strip(), db)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IMAGE NOT EXISTS")
    return result


@router.get('/all', response_model=List[ImageReadSchema], status_code=status.HTTP_200_OK)
async def get_all_images(limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0),
                         db: AsyncSession = Depends(get_db)):
    """
    The get_all_images function returns a list of all images in the database.
    The limit and offset parameters are used to paginate the results.


    :param limit: int: Limit the number of images returned
    :param ge: Specify the minimum value of the parameter
    :param le: Limit the number of images returned
    :param offset: int: Specify the number of records to skip before returning results
    :param ge: Specify the minimum value of the parameter
    :param db: AsyncSession: Get the database connection from the dependency
    :return: A list of images
    :doc-author: RSA
    """
    images = await repository_images.get_images(limit, offset, db)
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return images


@router.post("/", response_model=ImageReadSchema, description='No more than 5 requests per minute',
             dependencies=[Depends(RateLimiter(times=5, seconds=60))], status_code=status.HTTP_201_CREATED)
async def create_image(file: UploadFile = File(..., description="The image file to upload"),
                       title: str = Form(min_length=3, max_length=50),
                       tag: Optional[str] = None,
                       user: User = Depends(auth_service.get_current_user),
                       db: AsyncSession = Depends(get_db)):
    """
    The create_image function creates a new image in the database.
        It takes an UploadFile object, which is a file that has been uploaded to the server.
        The title and tag are optional parameters, but if they are provided they must be valid strings.

    :param file: UploadFile: Get the file from the request body
    :param description: Provide a description for the image
    :param title: str: Set the title of the image
    :param max_length: Limit the number of characters in a string
    :param tag: Optional[str]: Indicate that the tag parameter is optional
    :param user: User: Get the current user from the auth_service
    :param db: AsyncSession: Get the database session
    :return: A dict with the image data
    :doc-author: RSA
    """
    new_name = await repository_images.format_filename()
    size_is_valid = await repository_images.get_file_size(file)
    file_is_valid = await repository_images.file_is_image(file)
    if size_is_valid > settings.max_image_size:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File too large. Max size is {settings.max_image_size} bytes")
    if not file_is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="File is not an image. Only images are allowed")

    r = cloudinary.uploader.upload(file.file, public_id=f'PhotoShareApp/{new_name}', overwrite=True)
    image_path = cloudinary.CloudinaryImage(f'PhotoShareApp/{new_name}', version=r.get('version'))
    image = await repository_images.create_image(size=size_is_valid, image_path=image_path.url, title=title,
                                                 tag=tag, user=user, db=db)
    return image


@router.get('/{image_id}', status_code=status.HTTP_200_OK)
async def get_image(image_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)):
    """
    The get_image function returns an image with the given ID.
    If no such image exists, a 404 Not Found error is returned.

    :param image_id: int: Get the image id from the path
    :param db: AsyncSession: Pass the database connection to the function
    :return: A dictionary with the following keys:
    :doc-author: RSA
    """
    image = await repository_images.get_image(image_id, db)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return image


@router.get('/download/{image_id}', response_model=ImageReadSchema, status_code=status.HTTP_200_OK)
async def download_picture(image_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)):
    """
    The download_picture function downloads a picture from the database.
        The function takes an image_id as input and returns the image if it exists in the database.
        If not, it raises a 404 error.

    :param image_id: int: Specify the image id of the image that is to be downloaded
    :param db: AsyncSession: Pass the database session to the function
    :return: A streamingresponse object, which is a special type of response that allows
    :doc-author: RSA
    """
    image = await repository_images.get_image(image_id, db)
    if image:
        response = requests.get(image.path, stream=True)
        if response.status_code == 200:
            image_bytes = response.content
            image_show = Image.open(BytesIO(image_bytes))
            image_show.save("image.png")
            return FileResponse("image.png")
            # return StreamingResponse(response.iter_content(chunk_size=1024),
            #                 media_type=response.headers['content-type'])
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


@router.delete('/{image_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(image_id: int = Path(ge=1),
                       user: User = Depends(auth_service.get_current_user),
                       db: AsyncSession = Depends(get_db)):
    """
    The delete_image function deletes an image from the database and cloudinary.
    The function takes in a user object, which is used to verify that the user has permission to delete this image.
    It also takes in an integer representing the id of the image we want to delete.

    :param image_id: int: Get the image id from the path
    :param user: User: Get the user object from the database
    :param db: AsyncSession: Access the database
    :return: A dictionary with the key &quot;detail&quot; and value &quot;image successfully deleted&quot;
    :doc-author: RSA
    """
    image = await repository_images.get_user_image(image_id, user, db)

    if image:
        image_name = await repository_images.get_filename_from_cloudinary_url(image.path)
        response = requests.get(image.path, stream=True)
        if response.status_code == 200:
            cloudinary.uploader.destroy(f'PhotoShareApp/{image_name}')
            await repository_images.delete_image_from_db(image, db)
            return {'ditail': 'Image successfully deleted'}
        else:
            await repository_images.delete_image_from_db(image, db)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


@router.put('/{image_id}', response_model=ImageReadSchema, status_code=status.HTTP_200_OK)
async def update_image(image_id: int = Path(ge=1),
                       title: str = Form(min_length=3, max_length=50),
                       user: User = Depends(auth_service.get_current_user),
                       db: AsyncSession = Depends(get_db)):
    """
    The update_image function updates the title of an image.

    :param image_id: int: Specify the image to be deleted
    :param title: str: Get the new title of the image
    :param max_length: Limit the length of the title
    :param user: User: Get the current user from the database
    :param db: AsyncSession: Get the database session
    :return: The updated image
    :doc-author: RSA
    """
    image = await repository_images.get_user_image(image_id, user, db)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    image = await repository_images.update_image_title(image, title, db)
    return image


@router.get('/', response_model=list[ImageReadSchema], status_code=status.HTTP_200_OK)
async def get_images_by_user(limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0),
                             db: AsyncSession = Depends(get_db),
                             user: User = Depends(auth_service.get_current_user)):
    """
    The get_images_by_user function is used to get all images uploaded by a user.
    The function takes in the following parameters:
        limit - an integer that specifies how many images should be returned at once (defaults to 10)
        offset - an integer that specifies where in the list of all images uploaded by a user, we should start returning from (defaults to 0)

    :param limit: int: Limit the number of images returned
    :param ge: Specify the minimum value for a parameter, and le is used to specify the maximum value
    :param le: Limit the number of images returned to a maximum of 500
    :param offset: int: Skip the first offset number of images
    :param ge: Specify the minimum value, and le is used to specify the maximum value
    :param db: AsyncSession: Get the database session
    :param user: User: Get the user from the auth_service
    :return: A list of images
    :doc-author: RSA
    """
    images = await repository_images.get_user_images(limit, offset, user, db)
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return images
