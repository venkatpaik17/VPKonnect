from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v0 import api_routes
from app.config.app import settings
from app.db.db_sqlalchemy import Base, engine
from app.models import admin, auth, comment, post, user
from app.utils import job_task as job_task_utils

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

app.mount("/images", StaticFiles(directory="images"), name="images")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.allowed_cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_routes.router)

scheduler = BackgroundScheduler()


@app.on_event("startup")
def scheduler_init():
    scheduler.add_job(
        job_task_utils.delete_user_after_deactivation_period_expiration,
        trigger="cron",
        hour=5,
        minute=30,
        second=0,
        timezone="UTC",
    )
    scheduler.start()


@app.on_event("shutdown")
def scheduler_end():
    scheduler.shutdown()


@app.get("/")
def root():
    return {"message": "Hello World!"}
