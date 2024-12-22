import json
import logging.config
from pathlib import Path

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import Cookie, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask

from app.api.v0 import api_routes
from app.config.app import settings
from app.db.db_sqlalchemy import Base, engine
from app.models import admin, auth, comment, post, user
from app.utils import auth as auth_utils
from app.utils import event
from app.utils import job_task as job_task_utils
from app.utils import log as log_utils
from app.utils import map as map_utils
from app.utils.exception import CustomValidationError, TokenExpiredSignatureError

ENVIRONMENT = settings.app_environment
SHOW_DOCS_ENVIRONMENT = ("dev", "test")

if ENVIRONMENT not in SHOW_DOCS_ENVIRONMENT:
    settings.openapi_url = None
    settings.docs_url = None
    settings.redoc_url = None

# connection is established and model tables are created, only needed if using sqlalchemy for create operations. Not required if using alembic (DB Migr tool)
# all the models are imported and Base instance is used
# Base.metadata.create_all(bind=engine)

app = FastAPI(**settings.fastapi_kwargs)

app.mount("/images/user", StaticFiles(directory="images/user"), name="user_images")
app.mount(
    "/images/employee", StaticFiles(directory="images/employee"), name="employee_images"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.allowed_cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# setup logging using dictConfig and json
config_file = Path("app/config/log_config.json")
print(config_file)
with open(config_file) as f:
    config = json.load(f)

logging.config.dictConfig(config=config)


@app.middleware("http")
async def log_request(request: Request, call_next):
    response = await call_next(request)
    response.background = BackgroundTask(log_utils.write_log_data, request, response)
    return response


@app.exception_handler(CustomValidationError)
def custom_validation_exception_handler(request, exc: CustomValidationError):
    # request
    print(f"Request: {request}")

    # Return a JSONResponse with the status code and detail
    return JSONResponse(
        status_code=exc.status_code,  # Set the status code from the exception
        content={"detail": exc.detail},  # Set the error detail in the response body
    )


@app.exception_handler(TokenExpiredSignatureError)
def token_expiry_exception_handler(request, exc: TokenExpiredSignatureError):
    # extract type
    detail_segments = exc.detail.split(" ")
    type_ = detail_segments[0]

    # get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")

    # check user or employee
    if type_ in map_utils.transform_access_role(value="user"):
        # user token refresh
        return refresh_request(
            refresh_token=refresh_token,
            url="http://127.0.0.1:8000/api/v0/users/token/refresh",
        )
    else:
        # employee token refresh
        return refresh_request(
            refresh_token=refresh_token,
            url="http://127.0.0.1:8000/api/v0/employees/token/refresh",
        )


app.include_router(api_routes.router)

scheduler = BackgroundScheduler()


@app.on_event("startup")
def scheduler_init():
    scheduler.add_job(
        func=job_task_utils.delete_user_after_deactivation_period_expiration,
        trigger=IntervalTrigger(seconds=10),
    )
    scheduler.add_job(
        func=job_task_utils.remove_restriction_on_user_after_duration_expiration,
        trigger=IntervalTrigger(seconds=5),
    )
    scheduler.add_job(
        func=job_task_utils.remove_ban_on_user_after_duration_expiration,
        trigger=IntervalTrigger(seconds=5),
    )
    scheduler.add_job(
        func=job_task_utils.user_inactivity_inactive,
        trigger=IntervalTrigger(seconds=7),
    )
    scheduler.add_job(
        func=job_task_utils.user_inactivity_delete,
        trigger=IntervalTrigger(seconds=7),
    )
    scheduler.add_job(
        func=job_task_utils.close_appeal_after_duration_limit_expiration,
        trigger=IntervalTrigger(seconds=3),
    )
    scheduler.add_job(
        func=job_task_utils.delete_user_after_permanent_ban_appeal_limit_expiry,
        trigger=IntervalTrigger(seconds=5),
    )
    scheduler.add_job(
        func=job_task_utils.delete_content_after_ban_appeal_limit_expiry,
        trigger=IntervalTrigger(seconds=3),
    )
    scheduler.add_job(
        func=job_task_utils.reduce_violation_score_quarterly,
        trigger=IntervalTrigger(seconds=10),
    )

    scheduler.start()


@app.on_event("shutdown")
def scheduler_end():
    scheduler.shutdown()


def refresh_request(refresh_token: str, url: str):
    cookie_ = {"refresh_token": refresh_token}
    response = None
    try:
        # Make the POST request with JSON body parameters and a timeout
        response = requests.post(url, cookies=cookie_, timeout=3)
        response.raise_for_status()
        print("Request sent successfully")

        response_json = response.json()
        json_response = JSONResponse(
            content=response_json, status_code=response.status_code
        )

        if response.cookies:
            cookie_value = response.cookies.get("refresh_token")
            if not cookie_value:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Refresh token not set",
                )

            json_response.set_cookie(
                key="refresh_token", value=cookie_value, httponly=True, secure=True
            )

    except requests.Timeout as exc:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Request is timed out",
        ) from exc
    except requests.HTTPError as err:
        print(err.response.json())
        raise err
    except requests.RequestException as exc:
        raise exc

    return json_response


@app.get(settings.api_prefix + "/")
def root(request: Request, refresh_token: str = Cookie(None)):
    auth_header = request.headers.get("Authorization")
    main_page_message = "Hello, Welcome to VPKonnect Main Page"

    # url for user token refresh
    url = "http://127.0.0.1:8000/api/v0/users/token/refresh"

    if not refresh_token:
        return {"message": main_page_message}

    if auth_header:
        # get access_token
        access_token = auth_header.split()[1]

        # validate access_token
        try:
            current_user = auth_utils.verify_access_token(access_token=access_token)

            return RedirectResponse(
                url=settings.api_prefix + "/users/feed",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        except HTTPException as exc:
            print(exc)
            return refresh_request(refresh_token=refresh_token, url=url)
        except Exception as exc:
            print(exc)
            return refresh_request(refresh_token=refresh_token, url=url)
    else:
        return refresh_request(refresh_token=refresh_token, url=url)
