from pathlib import Path
from src.conf.config import settings

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.services.auth import auth_service

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER="smtp.meta.ua",
    MAIL_FROM_NAME=settings.mail_from,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)


async def send_email(email: EmailStr, username: str, host: str):
    """
    The send_email function sends an email to the user with a link to confirm their email address.
    The function takes in three parameters:
        -email: EmailStr, the user's email address.
        -username: str, the username of the user who is registering for an account.  This will be used in a greeting message.
        -host: str, this is where we are hosting our application (e.g., http://localhost).  This will be used as part of our confirmation link.

    :param email: EmailStr: Validate the email address
    :param username: str: Pass the username to the email template
    :param host: str: Provide the host of the application to be used in the email template
    :return: A coroutine object that can be awaited
    :doc-author: RSA
    """
    try:
        token_verification = await auth_service.create_email_token({"sub": email})

        message = MessageSchema(
            subject="Confirm your email ",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_template.html")
    except ConnectionErrors as err:
        print(err)


async def send_email_reset_password(email: EmailStr, username: str, host: str):
    """
    The send_email_reset_password function sends an email to the user with a link to reset their password.
    Args:
        email (str): The user's email address.
        username (str): The username of the user who is requesting a password reset.
        host (str): The hostname of the server where this function is being called from.

    :param email: EmailStr: Specify the email address of the user who wants to reset their password
    :param username: str: Get the username of the user who is trying to reset his password
    :param host: str: Create the link to reset password
    :return: A message that is sent to the user's email address
    :doc-author: RSA
    """
    try:
        token_verification = await auth_service.create_email_token({"sub": email})

        message = MessageSchema(
            subject="Reset password ",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="password_template.html")
    except ConnectionErrors as err:
        print(err)
