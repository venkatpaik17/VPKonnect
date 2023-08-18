from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.app import settings
from app.db.db_sqlalchemy import Base, engine
from app.models import admin, comment, post, user

ENVIRONMENT = settings.app_environment
SHOW_DOCS_ENVIRONMENT = ("dev", "test")

if ENVIRONMENT not in SHOW_DOCS_ENVIRONMENT:
    settings.openapi_url = None
    settings.docs_url = None
    settings.redoc_url = None

# connection is established and model tables are created, only needed if using sqlalchemy for create operations. Not required if using alembic (DB Migr tool)
# all the models are imported and Base instance is used
Base.metadata.create_all(bind=engine)

app = FastAPI(**settings.fastapi_kwargs)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.allowed_cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Hello World!"}
