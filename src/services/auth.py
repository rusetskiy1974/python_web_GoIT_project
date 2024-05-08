from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.conf.config import settings
from src.database.db import get_db
from src.repository import users as repository_users


class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

    # blacklist_access_tokens = []

    async def verify_password(self, plain_password, hashed_password) -> bool:
        """
        The verify_password function takes a plain-text password and a hashed password,
        and returns True if the two match. This is used to verify that the user's inputted
        password matches what we have stored in our database.

        :param self: Represent the instance of the class
        :param plain_password: Store the password that is entered by the user
        :param hashed_password: Verify the plain_password parameter
        :return: True if the plain_password matches the hashed_password, and false otherwise
        :doc-author: RSA
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    async def get_password_hash(self, password) -> str:
        """
        The get_password_hash function is a helper function that hashes the password using the passlib library.
        The hashing algorithm used by this function is PBKDF2 with HMAC-SHA256, which is considered to be one
        of the most secure algorithms available today.

        :param self: Represent the instance of the class
        :param password: Hash the password
        :return: A hash of the password
        :doc-author: RSA
        """
        return self.pwd_context.hash(password)

    # function to generate a new access token
    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        The create_access_token function creates a new access token.
        Args:
            data (dict): A dictionary containing the claims to be encoded in the JWT.
            expires_delta (Optional[float]): An optional parameter specifying how long, in seconds,
            the access token should last before expiring. If not specified, it defaults to 4 minutes.

        :param self: Access the class attributes
        :param data: dict: Pass in the data that will be encoded into the jwt
        :param expires_delta: Optional[float]: Set the expiration time of the access token
        :return: A token that is encoded with the data passed to it
        :doc-author: RSA
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    # function to generate a new refresh token
    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        The create_refresh_token function creates a refresh token for the user.
        Args:
            data (dict): A dictionary containing the user's id and username.
            expires_delta (Optional[float]): The number of seconds until the token expires, defaults to 30 days if not specified.

        :param self: Represent the instance of the class
        :param data: dict: Pass in the user's id and username
        :param expires_delta: Optional[float]: Set the expiration time of the refresh token
        :return: An encoded refresh token
        :doc-author: RSA
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=30)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        """
        The decode_refresh_token function takes a refresh token and decodes it.
        If the scope is 'refresh_token', then we return the email address of the user who owns that token.
        Otherwise, we raise an HTTPException with status code 401 (UNAUTHORIZED) and detail message &quot;
        Invalid scope for token&quot;.
        If there's a JWTError, then we also raise an HTTPException with status code 401 (UNAUTHORIZED) and
        detail message &quot;Could not validate credentials&quot;.

        :param self: Represent the instance of the class
        :param refresh_token: str: Pass the refresh token to the function
        :return: The email of the user who is logged in
        :doc-author: RSA
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            print(payload)
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid scope for token")

        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
        """
        The get_current_user function is a dependency that will be used in the protected route.
        It takes an OAuth2 token as input and returns the user object if it's valid, or raises an exception otherwise.

        :param self: Represent the instance of a class
        :param token: str: Get the token from the header
        :param db: AsyncSession: Get the database session
        :return: The user object
        :doc-author: RSA
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception

            else:
                raise credentials_exception

            email = payload["sub"]
            if email is None:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        user = await repository_users.get_user_by_email(email, db)
        if user is None:
            raise credentials_exception

        if user.refresh_token is None:
            raise credentials_exception

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

        return user

    async def create_email_token(self, data: dict):
        """
        The create_email_token function takes in a dictionary of data and returns a token.
        The token is created using the JWT library, which encodes the data into a string that can be decoded later.
        The function also adds an expiration date to the encoded data.

        :param self: Make the function a method of the user class
        :param data: dict: Pass the data to be encoded
        :return: A token that is encoded using the jwt library
        :doc-author: RSA
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):
        """
        The get_email_from_token function takes a token as an argument and returns the email address associated with that token.
        The function uses the jwt library to decode the token, which is then used to return the email address.

        :param self: Represent the instance of the class
        :param token: str: Get the token from the request
        :return: The email from the token
        :doc-author: RSA
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email verification")

    # @staticmethod
    async def get_user_access_token(self, access_token: str = Depends(oauth2_scheme)):
        """
        The get_user_access_token function is a dependency that will be used by the
        get_current_user function. It takes an access token as input and returns it.
        The access token is provided by the oauth2_scheme dependency, which uses the OAuth2PasswordBearer scheme to validate
        the user's credentials.

        :param self: Access the class variables and methods
        :param access_token: str: Get the access token from the request
        :return: The access_token
        :doc-author: RSA
        """
        return access_token

    async def get_token_expiration_time(self, token: str):
        """
        The get_token_expiration_time function takes a token as an argument and returns the expiration time of that token.
        If the token is invalid, it will return None.

        :param self: Represent the instance of a class
        :param token: str: Pass in the token that is being decoded
        :return: The expiration time of the token
        :doc-author: RSA
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                expiration_time = datetime.utcfromtimestamp(payload['exp'])
                return expiration_time
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid scope for token")

        except JWTError:
            return


auth_service = Auth()
