import secrets

from fastapi import APIRouter, Depends, HTTPException, status, Security, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.models.models import User
from src.repository import users as repository_users
from src.schemas.user import UserCreateSchema, TokenSchema, UserResponseSchema, RequestEmail, ConfirmationResponse, \
    LogoutResponseSchema
from src.services.auth import auth_service
from src.services.email import send_email
from src.conf import messages

router = APIRouter(prefix="/auth", tags=["auth"])

blacklisted_tokens = set()

get_refresh_token = HTTPBearer()


@router.post("/signup/", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def signup(background_tasks: BackgroundTasks,
                 request: Request,
                 body: UserCreateSchema = Depends(),
                 db: AsyncSession = Depends(get_db),
                 ):
    """
    The signup function creates a new user.

    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base_url of the request
    :param body: UserCreateSchema: Validate the request body
    :param db: AsyncSession: Get the database session
    :param : Send the email in the background
    :return: A dict with a user and detail
    :doc-author: RSA
    """
    if not secrets.compare_digest(body.password, body.password_confirmation):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.PASSWORDS_NOT_MATCH)
    del body.password_confirmation
    exist_user = await repository_users.get_user_by_email(email=body.email, db=db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.ACCOUNT_EXISTS)
    body.password = await auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db=db)
    background_tasks.add_task(send_email, new_user.email, new_user.fullname, str(request.base_url))

    return {"user": new_user, "detail": "User successfully created. Check your email for confirmation."}


@router.post("/login", response_model=TokenSchema)
async def login(body: OAuth2PasswordRequestForm = Depends(),
                db: AsyncSession = Depends(get_db)):
    """
    The login function is used to authenticate a user.
    It takes the username and password from the request body,
    verifies them against the database, and returns an access token.

    :param body: OAuth2PasswordRequestForm: Get the username and password from the request body
    :param db: AsyncSession: Get the database session
    :return: A dictionary with the access_token, refresh_token and token type
    :doc-author: RSA
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_EMAIL)
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.NOT_CONFIRMED_EMAIL)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.INACTIVE_USER)
    if not await auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_PASSWORD)

    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token_ = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token_, db)
    return {"access_token": access_token, "refresh_token": refresh_token_, "token_type": "bearer"}


@router.post("/logout", response_model=LogoutResponseSchema)
async def logout(access_token: str = Depends(auth_service.get_user_access_token),
                 user: User = Depends(auth_service.get_current_user),
                 db: AsyncSession = Depends(get_db)) -> dict:
    """
    The logout function is used to logout a user.
    It takes an access token as input and returns a message indicating that the logout was successful.

    :param access_token: str: Get the access token from the authorization header
    :param user: User: Get the user that is currently logged in
    :param db: AsyncSession: Get a database session
    :return: A dict with a message
    :doc-author: RSA
    """
    blacklisted_tokens.add(access_token)
    user.refresh_token = None
    await db.commit()
    return {"message": "Logout successful."}


@router.get('/refresh_token', response_model=TokenSchema)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(get_refresh_token),
                        db: AsyncSession = Depends(get_db)) -> dict:
    """
    The refresh_token function is used to refresh the access token.
    The function takes in a refresh token and returns an access token, a new refresh token, and the type of
    authentication being used (bearer). If there is no valid user associated with the given email address or if
    there are any errors during this process then an HTTPException will be raised.

    :param credentials: HTTPAuthorizationCredentials: Get the token from the request header
    :param db: AsyncSession: Get the database session
    :return: A dict with the access_token, refresh_token and token type
    :doc-author: RSA
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if not secrets.compare_digest(user.refresh_token, token):
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_REFRESH_TOKEN)

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token_ = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token_, db)
    return {"access_token": access_token, "refresh_token": refresh_token_, "token_type": "bearer"}


@router.post("/request_email")
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: AsyncSession = Depends(get_db)) -> dict:
    """
    The request_email function is used to send an email to the user with a link that will allow them
    to confirm their account. The function takes in a RequestEmail object, which contains the email of
    the user who wants to confirm their account. It then checks if there is already a confirmed user with
    that email address, and if so returns an error message saying that this account has already been confirmed.
    If not, it sends an email containing a confirmation link.

    :param body: RequestEmail: Validate the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base_url of the request
    :param db: AsyncSession: Get the database session
    :return: A dict with a message
    :doc-author: RSA
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if user.confirmed:
        return {"message": messages.EMAIL_ALREADY_CONFIRMED}
    if user:
        background_tasks.add_task(send_email, user.email, user.fullname, str(request.base_url))
    return {"message": messages.CHECK_EMAIL_FOR_CONFIRMATION}


@router.get('/confirmed_email/{token}', response_model=ConfirmationResponse)
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)) -> ConfirmationResponse:
    """
    The confirmed_email function takes a token and database session as input.
    It returns a ConfirmationResponse object with the message &quot;Email confirmed&quot; if successful.
    If unsuccessful, it raises an HTTPException with status code 400 and detail &quot;Verification error&quot;.


    :param token: str: Get the token from the url
    :param db: AsyncSession: Pass the database session to the function
    :return: A confirmationresponse object
    :doc-author: RSA
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return ConfirmationResponse(message="Your email is already confirmed")
    await repository_users.confirmed_email(email, db)
    return ConfirmationResponse(message="Email confirmed")
