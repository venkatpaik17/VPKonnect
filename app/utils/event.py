from datetime import timedelta
from time import sleep

import requests
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import event, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased
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

# reflect database schema into the MetaData object
# metadata.reflect(views=True)

# mapper events
# this event listener will only work if ORM style updates are done instead of query updates
# user.status = "status_value" -> ORM update
# query.update({"status": "status_value"}, synchronize_session=False) -> query update
# def call_logout_after_update_user_status_listener(mapper, connection, target):
#     print(f"Status updated to {target.status}")
#     hist = get_history(target, "status")
#     result = None
#     if hist.has_changes() and target.status in ("TBN", "PBN"):
#         print(hist)
#         db = next(get_db())
#         logout = auth_schema.UserLogout(
#             username=target.username, device_info=None, action="all", flow="admin"
#         )
#         result = auth_route.user_logout(logout_user=logout, db=db, is_api_call=False)

#     if result:
#         print(f"Job done successfully. User {target.username} logged out")
#     else:
#         print("No action")


# event.listen(
#     user_model.User, "after_update", call_logout_after_update_user_status_listener
# )


# # attribute events
# def call_logout_after_update_user_status_attribute_listener(
#     target, value, oldvalue, initiator
# ):
#     print(f"Status updated to {value}")
#     result = None
#     print(target)

#     if oldvalue is not None and (
#         oldvalue not in ("DAH", "PDH", "TBN", "PBN", "INA")
#         and value in ("DAH", "PDH", "TBN", "PBN", "INA")
#     ):
#         db = next(get_db())
#         try:
#             logout = auth_schema.UserLogout(
#                 username=target.username, device_info=None, action="all", flow="admin"
#             )
#             result = auth_route.user_logout(
#                 logout_user=logout, db=db, is_func_call=True
#             )

#             if result:
#                 print(f"Job done successfully. User {target.username} logged out")
#             else:
#                 print("No action")
#         except Exception as exc:
#             print("Error: ", exc)
#         finally:
#             db.close()


def call_logout_after_update_user_status_attribute_listener(
    target, value, oldvalue, initiator
):
    print(f"Status updated to {value}")
    result = None
    print(target)
    url = "http://127.0.0.1:8000/api/v0/users/logout"
    json_data = {
        "username": target.username,
        "device_info": None,
        "action": "all",
        "flow": "admin",
    }
    if oldvalue is not None and (
        oldvalue not in ("DAH", "PDH", "TBN", "PBN", "INA")
        and value in ("DAH", "PDH", "TBN", "PBN", "INA")
    ):
        db = next(get_db())
        response = None
        try:
            # Make the POST request with JSON body parameters and a timeout
            response = requests.post(url, json=json_data, timeout=3)
            response.raise_for_status()
            print("Request sent successfully")
        except requests.Timeout as exc:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Request is timed out",
            ) from exc
        except requests.HTTPError as err:
            raise err
        except requests.RequestException as exc:
            raise exc
        finally:
            print(f"{target.username} logged out successfully")
            db.close()


# Listen for changes in the status attribute of the User model
event.listen(
    user_model.User.status,
    "set",
    call_logout_after_update_user_status_attribute_listener,
)


# @event.listens_for(Session, "do_orm_execute")
# def call_logout_after_update_user_status_listener(context):
#     if context.is_update:
#         target = context.get_current_parameters()
#         if "status" in target and target["status"] in (
#             "DAH",
#             "DAK",
#             "PDH",
#             "PDK",
#             "TBN",
#             "PBN",
#             "INA",
#         ):
#             print(f"Status updated to {target['status']}")
#             db: Session = next(get_db())
#             logout = auth_schema.UserLogout(
#                 username=target["username"],
#                 device_info=None,
#                 action="all",
#                 flow="admin",
#             )
#             auth_route.user_logout(logout_user=logout, db=db)
