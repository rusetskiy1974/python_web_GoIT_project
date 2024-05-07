from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Settings for the application.
    """
    db_url: str
    db_local_url: str
    db_user: str
    db_password: str
    db_port: str
    db_name: str
    secret_key: str
    algorithm: str
    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int
    mail_server: str
    redis_host: str
    redis_local_host: str = 'localhost'
    redis_port: int = '6379'
    redis_password: str
    cloudinary_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    cloudinary_url: str
    max_image_size: int
    max_add_tags: int

    model_config = ConfigDict(extra='ignore', env_file="../../env", env_file_encoding="utf-8")


settings = Settings()
