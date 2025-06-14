from src.api import docs
from fastapi import FastAPI
from src.api.lifespan import lifespan
from src.api.routers import routers

from starlette.middleware.cors import CORSMiddleware
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
    ],
    root_path=settings.app_root_path,
    root_path_in_servers=False,
    generate_unique_id_function=docs.generate_unique_operation_id,
    lifespan=lifespan,
    # docs_url=None,
    # redoc_url=None,
    # swagger_ui_oauth2_redirect_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in routers:
    app.include_router(router)
