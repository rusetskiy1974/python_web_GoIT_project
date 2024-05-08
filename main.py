import asyncio
import uvicorn

from typing import Callable

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi_limiter import FastAPILimiter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from src.database.db import get_db, db_redis
from src.routes import auth, users, images, transform, admin, comments,rating
from src.routes.auth import blacklisted_tokens
from src.utils.utils import periodic_clean_blacklist

app = FastAPI(swagger_ui_parameters={"operationsSorter": "method"}, title="PhotoShare")

origins = ['*']


@app.middleware("http")
async def block_blacklisted_tokens(request: Request, call_next: Callable):
    """
    The block_blacklisted_tokens function is a middleware function that checks if the access token in the Authorization
    header of an incoming request is blacklisted. If it is, then this function returns a 401 Unauthorized response.
    Otherwise, it passes control to the next handler.

    :param request: Request: Access the request object
    :param call_next: Callable: Pass the request to the next middleware in line
    :return: The result of calling the next handler in the chain
    :doc-author: RSA
    """
    authorization_header = request.headers.get("Authorization")
    if authorization_header is None:
        # Якщо відсутній заголовок "Authorization", пропустити до наступного обробника
        response = await call_next(request)
        return response
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Token is invalid"})
    access_token = parts[1]
    if access_token in blacklisted_tokens:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Token is blacklisted"})

    response = await call_next(request)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    r = await db_redis
    await FastAPILimiter.init(r)
    asyncio.create_task(periodic_clean_blacklist(4))


app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(images.router, prefix="/api")
app.include_router(transform.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(comments.router, prefix="/api")
app.include_router(rating.router, prefix="/api")


@app.get("/")
def index():
    return {"message": "PhotoShare Application"}


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")


if __name__ == '__main__':
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
