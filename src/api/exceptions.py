__all__ = ["IncorrectCredentialsException"]

from typing import Any, ClassVar

from fastapi import HTTPException
from starlette import status
from src.logging import logger


class CustomHTTPException(HTTPException):
    responses: ClassVar[dict[int | str, dict[str, Any]]]


class IncorrectCredentialsException(CustomHTTPException):
    """
    HTTP_401_UNAUTHORIZED
    """

    def __init__(self, no_credentials: bool = False):
        if no_credentials:
            logger.warning("Credentials are lacking")
            super().__init__(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=self.responses[401]["description"],
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            logger.warning("Unable to verify credentials")
            super().__init__(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=self.responses[401]["description"],
            )

    responses = {
        401: {"description": "Unable to verify credentials OR Credentials not provided"}
    }
