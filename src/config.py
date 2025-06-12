from enum import StrEnum


from dotenv import dotenv_values
from pydantic import BaseModel


config = dotenv_values(".env")


class Accounts(BaseModel):
    """InNoHassle Accounts integration settings"""
    api_url: str = "https://api.innohassle.ru/accounts/v0"
    api_jwt_token: str = config["API_JWT_TOKEN"]


class Settings(BaseModel):
    """Settings for the application."""
    app_root_path: str = ""
    database_uri: str = config["DATABASE_URI"]
    is_prod: bool = config["IS_PROD"]

    # TODO: recheck
    cors_allow_origin_regex: str = "https://.*.innohassle.ru"
    accounts: Accounts = Accounts()


settings = Settings()
