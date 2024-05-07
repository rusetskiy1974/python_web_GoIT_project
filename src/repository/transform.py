from io import BytesIO

import cloudinary
import qrcode
from cloudinary.utils import cloudinary_url

from src.repository import images as repository_images
from src.conf.config import settings


async def transform_image(image_url, transformation_options=None):
    """
    The transform_image function takes in an image_url and transformation_options.
    The function then transforms the image using cloudinary's url method, which returns a transformed url and options.
    The function then returns the transformed url.

    :param image_url: Specify the image to be transformed
    :param transformation_options: Pass in the transformation options to be applied to the image
    :return: A transformed image url
    :doc-author: RSA
    """
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True)

    # Transform image in cloudinary
    # transformed_url = image_url
    name = await repository_images.get_filename_from_cloudinary_url(image_url)
    if transformation_options:
        transformed_url, options = cloudinary_url(f"PhotoShareApp/{name}", **transformation_options)
        return transformed_url


async def generate_qr_code(data):

    """
    The generate_qr_code function takes in a string of data and returns a QR code image.

    :param data: Store the data that is to be encoded in the qr code
    :return: A qr code image
    :doc-author: RSA
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr_image = qr.make_image(fill_color="black", back_color="white")

    return qr_image
