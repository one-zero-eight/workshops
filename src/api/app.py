import src.logging_  # noqa

from fastapi import FastAPI
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi_swagger import patch_fastapi
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from src.logging_ import logger
from src.api import docs
from src.api.lifespan import lifespan
from src.config import settings

app = FastAPI(
    title=docs.TITLE,
    summary=docs.SUMMARY,
    description=docs.DESCRIPTION,
    version=docs.VERSION,
    contact=docs.CONTACT_INFO,
    license_info=docs.LICENSE_INFO,
    openapi_tags=docs.TAGS_INFO,
    servers=[
        {"url": settings.app_root_path, "description": "Current"},
        {
            "url": "https://api.innohassle.ru/workshops/v0",
            "description": "Production environment",
        },
        {
            "url": "https://api.innohassle.ru/workshops/staging-v0",
            "description": "Staging environment",
        },
    ],
    root_path=settings.app_root_path,
    root_path_in_servers=False,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    swagger_ui_oauth2_redirect_url=None,
)
patch_fastapi(app)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Log validation errors and return the default FastAPI JSON response.
    Based on https://github.com/dantetemplar/fastapi-how-to-log#exceptions
    """
    as_validation_error = ValidationError.from_exception_data(
        str(request.url.path),
        line_errors=exc.errors(),  # type: ignore
    )
    logger.warning(str(as_validation_error), exc_info=False)
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """
    Log non-request Pydantic validation errors and return JSON details.
    """
    logger.warning("Pydantic validation error on %s: %s", request.url.path, exc, exc_info=False)
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Log raised HTTPException.
    Based on https://github.com/dantetemplar/fastapi-how-to-log#exceptions
    """
    logger.warning(exc, exc_info=exc)
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Log unexpected errors and avoid leaking raw exception text to clients.
    """
    logger.exception("Unhandled server error on %s", request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.modules.users.routes import router as router_users  # noqa: E402
from src.modules.workshops.routes import router as router_workshops  # noqa: E402

# Import routers above and include them below [do not edit this comment]
app.include_router(router_users)
app.include_router(router_workshops)
# ^
