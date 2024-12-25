from datetime import timedelta
from logging import Logger
from time import sleep

import requests
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import event, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased, object_session
from sqlalchemy.orm.attributes import get_history

from app.api.v0.routes import auth as auth_route
from app.db.db_sqlalchemy import metadata
from app.db.session import get_db
from app.models import admin as admin_model
from app.models import user as user_model
from app.schemas import admin as admin_schema
from app.schemas import auth as auth_schema
from app.services import admin as admin_service
from app.services import comment as comment_service
from app.services import post as post_service
from app.services import user as user_service
from app.utils import email as email_utils
from app.utils import job_task as job_task_utils
from app.utils import log as log_utils


def send_logout_request(target):
    url = "http://127.0.0.1:8000/api/v0/users/logout"
    json_data = {
        "username": target.username,
        "device_info": None,
        "action": "all",
        "flow": "admin",
    }
    logger: Logger = log_utils.get_logger()

    try:
        # Make the POST request with JSON body parameters and a timeout
        response = requests.post(url, json=json_data, timeout=3)
        response.raise_for_status()
        logger.info("Request sent to %s successfully", url)
    except requests.Timeout as exc:
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Request is timed out",
        ) from exc
    except requests.HTTPError as err:
        logger.error(err, exc_info=True)
        raise HTTPException(
            status_code=err.response.status_code,
            detail=f"HTTP error occurred: {err.response.text}",
        ) from err
    except requests.RequestException as exc:
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Exception occurred: {str(exc)}",
        ) from exc

    print(f"{target.username} logged out successfully")


def call_logout_after_update_user_status_attribute_listener(
    target, value, oldvalue, initiator
):
    print(f"Status updated to {value}")

    if oldvalue is not None and (
        oldvalue not in ("DAH", "PDH", "TBN", "PBN", "INA")
        and value in ("DAH", "PDH", "TBN", "PBN", "INA")
    ):
        # Obtain the session that is associated with the target object
        session = object_session(target)
        if session:
            # Listen for the after_commit event on this session
            event.listen(session, "after_commit", lambda _: send_logout_request(target))


# Listen for changes in the status attribute of the User model
event.listen(
    user_model.User.status,
    "set",
    call_logout_after_update_user_status_attribute_listener,
)
