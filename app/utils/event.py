from sqlalchemy import event, inspect
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import get_history

from app.api.v0.routes import auth as auth_route
from app.db.session import get_db
from app.models import user as user_model
from app.schemas import auth as auth_schema

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


# attribute events
def call_logout_after_update_user_status_attribute_listener(
    target, value, oldvalue, initiator
):
    print(f"Status updated to {value}")
    result = None
    print(target)

    if oldvalue is not None and (
        oldvalue not in ("TBN", "PBN", "INA") and value in ("TBN", "PBN", "INA")
    ):
        db = next(get_db())
        logout = auth_schema.UserLogout(
            username=target.username, device_info=None, action="all", flow="admin"
        )
        result = auth_route.user_logout(logout_user=logout, db=db, is_api_call=False)

        if result:
            print(f"Job done successfully. User {target.username} logged out")
        else:
            print("No action")


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
