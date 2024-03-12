from time import sleep

from sqlalchemy import event, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased
from sqlalchemy.orm.attributes import get_history

from app.api.v0.routes import auth as auth_route
from app.db.session import get_db
from app.models import admin as admin_model
from app.models import user as user_model
from app.schemas import auth as auth_schema
from app.services import admin as admin_service
from app.services import comment as comment_service
from app.services import post as post_service
from app.services import user as user_service

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
        oldvalue not in ("DAH", "DAK", "PDH", "TBN", "PBN", "INA")
        and value in ("TBN", "PBN", "INA")
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


# event listener for if appeal status updates to ACP from URV i.e. if appeal is accepted
# First we join appeal table with restrict/ban table
# Appeal type is account
#     - We will get the post/comment associated with the restrict/ban
#     - So we can unban the content too along with removal of user's restrict/ban
# Appeal type is post/comment
#     - Case 1:
#         - We will get the restrict/ban associated with that post/comment
#         - So we can remove the restrict/ban on user along with post/comment unban
#     - Case 2:
#         - There is no restrict/ban entry for the appeal post/comment
#         - So only unban the post/comment


def user_restrict_ban_detail_user_operation(
    user_id: str, report_id: str, status: str, db: Session
):
    current_entry = admin_service.get_user_active_restrict_ban_entry_user_id_report_id(
        user_id=user_id, status=status, report_id=report_id, db_session=db
    )
    if not current_entry:
        raise Exception(
            "Error. Active restrict/ban entry to remove restrict/ban not found"
        )

    # remove the current restrict/ban
    current_entry.is_active = False

    # check next restrict/ban
    # consecutive_violation_query = (
    #     db.query(admin_model.UserRestrictBanDetail)
    #     .filter(
    #         admin_model.UserRestrictBanDetail.user_id == user_id,
    #         admin_model.UserRestrictBanDetail.enforce_action_at > func.now(),
    #         admin_model.UserRestrictBanDetail.is_active == False,
    #         admin_model.UserRestrictBanDetail.is_deleted == False,
    #     )
    #     .order_by(admin_model.UserRestrictBanDetail.enforce_action_at.asc())
    # )

    # subquery to get the next nearest enforce_action_at which is greater than now(), scalar is used to directly fetch the value of single column value from the query
    subq_min_enforce_action_at = (
        db.query(func.min(admin_model.UserRestrictBanDetail.enforce_action_at))
        .filter(
            admin_model.UserRestrictBanDetail.user_id == user_id,
            admin_model.UserRestrictBanDetail.report_id
            != report_id,  # exclude the current deactivated restrict/ban entry
            admin_model.UserRestrictBanDetail.enforce_action_at > func.now(),
            admin_model.UserRestrictBanDetail.is_active == False,
            admin_model.UserRestrictBanDetail.is_deleted == False,
        )
        .scalar()
    )

    # print(subq_min_enforce_action_at)
    consecutive_violation_query = db.query(admin_model.UserRestrictBanDetail).filter(
        admin_model.UserRestrictBanDetail.user_id == user_id,
        admin_model.UserRestrictBanDetail.enforce_action_at
        == subq_min_enforce_action_at,
    )

    consecutive_violation = consecutive_violation_query.first()

    # get user
    user = user_service.get_user_by_id(
        user_id,
        ["DAH", "DAK", "PDH", "PDK", "INA", "ACT", "DEL"],
        db,
    )
    if not user:
        raise Exception("Error. User entry for changing status not found")

    if consecutive_violation:
        # enforce next restrict/ban, this will be early enforce
        consecutive_violation_query.update(
            {
                "is_active": True,
                "enforce_action_at": func.now(),
                "is_enforce_action_early": True,
            },
            synchronize_session=False,
        )

        # update user status
        user.status = consecutive_violation.status
    else:
        user.status = "ACT"


def guideline_violation_score_last_added_score_operation(
    user_id: str, report_id: str, ban_content_type: str, db: Session
):
    # get guideline violation score entry
    guideline_violation_score_entry_query = (
        admin_service.get_user_guideline_violation_score_query(
            user_id=user_id, db_session=db
        )
    )
    guideline_violation_score_entry = guideline_violation_score_entry_query.first()
    if not guideline_violation_score_entry:
        raise Exception(
            "Error. Guideline violation score entry for updating scores of user not found"
        )

    # get last_added_score from guideline_violation_last_added_score
    last_added_score_entry = admin_service.get_last_added_score(
        score_id=guideline_violation_score_entry.id, report_id=report_id, db_session=db
    )
    if not last_added_score_entry:
        raise Exception("Error. Last added score entry of restrict/ban not found")

    # update is_removed to True
    last_added_score_entry.is_removed = True

    # set the score_type and get curr_score for the content type
    if ban_content_type == "post":
        score_type = "post_score"
        curr_score = guideline_violation_score_entry.post_score
    elif ban_content_type == "comment":
        score_type = "comment_score"
        curr_score = guideline_violation_score_entry.comment_score
    elif ban_content_type == "message":
        score_type = "message_score"
        curr_score = guideline_violation_score_entry.message_score
    # if reported item type is account, then use post_score, as posts reflect most of the account
    else:
        score_type = "post_score"
        curr_score = guideline_violation_score_entry.post_score

    last_added_score = last_added_score_entry.last_added_score
    curr_final_violation_score = guideline_violation_score_entry.final_violation_score

    # adjust the scores (appropriate content score and final violation score)
    # if scores after adjustment goes -ve, make it 0
    diff_score = max(curr_score - last_added_score, 0)
    new_final_violation_score = max(curr_final_violation_score - last_added_score, 0)

    guideline_violation_score_entry_query.update(
        {
            score_type: diff_score,
            "final_violation_score": new_final_violation_score,
        },
        synchronize_session=False,
    )


def post_comment_operation(ban_content_id: str, ban_content_type: str, db: Session):
    if ban_content_type == "post":
        # get post
        post_entry = post_service.get_a_post(
            post_id=ban_content_id,
            status_not_in_list=["PUB", "DRF", "HID", "DEL"],
            db_session=db,
        )
        if not post_entry:
            raise Exception("Error. Post to be unbanned not found")

        # update status to PUB
        post_entry.status = "PUB"

    if ban_content_type == "comment":
        # get comment
        comment_entry = comment_service.get_a_comment(
            comment_id=ban_content_id,
            status_not_in_list=["PUB", "HID", "DEL"],
            db_session=db,
        )
        if not comment_entry:
            raise Exception("Error. Comment to be unbanned not found")
            return None

        # update status to PUB
        comment_entry.status = "PUB"


def appeal_status_accept_after_update_attribute_listener(
    target, value, oldvalue, initiator
):
    print(f"Status updated to {value}")
    print(target.__dict__)
    print(oldvalue)
    print(value)
    sleep(3)
    if oldvalue is not None and (oldvalue == "URV" and value == "ACP"):
        print("Hello")
        db = next(get_db())

        join_model = aliased(admin_model.AppealRestrictJoinView)
        # query the view
        appeal_restrict_join_entries_query = db.query(join_model)
        print(appeal_restrict_join_entries_query)

        print(appeal_restrict_join_entries_query.all())
        print(target.user_id)

        restrict_ban_entry = appeal_restrict_join_entries_query.filter(
            join_model.user_id == target.user_id,
            join_model.report_id == target.report_id,
        )
        print(restrict_ban_entry.first())

        query_user_id = target.user_id
        query_report_id = target.report_id
        query_content_id = None
        query_content_type = None
        query_status = None

        try:
            print("Hello1")
            # based on target appeal type we go with the operations
            if target.content_type == "account":
                restrict_ban_entry_acc = restrict_ban_entry.filter(
                    join_model.user_restrict_ban_is_deleted == False
                ).first()
                if (
                    restrict_ban_entry_acc
                    and restrict_ban_entry_acc.user_restrict_ban_is_active == True
                ):
                    # check the content_type for restrict/ban
                    if (
                        restrict_ban_entry_acc.user_restrict_ban_content_type
                        == "account"
                    ):
                        # update is_active to False
                        # check for next successive violation and enforce it (is_active to True, enforce_action_at to func.now(), is_enforce_action_early to true)
                        # update user status
                        # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
                        query_status = restrict_ban_entry_acc.user_restrict_ban_status
                        query_content_type = (
                            restrict_ban_entry_acc.user_restrict_ban_content_type
                        )
                        user_restrict_ban_detail_user_operation(
                            user_id=query_user_id,
                            report_id=query_report_id,
                            status=query_status,
                            db=db,
                        )
                        guideline_violation_score_last_added_score_operation(
                            user_id=query_user_id,
                            report_id=query_report_id,
                            ban_content_type=query_content_type,
                            db=db,
                        )

                    elif restrict_ban_entry_acc.user_restrict_ban_content_type in (
                        "post",
                        "comment",
                    ):
                        # update is_active to False
                        # check for next successive violation and enforce it (is_active to True, enforce_action_at to func.now(), is_enforce_action_early to true)
                        # update user status
                        # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
                        # get the user_restrict_ban_content_id, user_restrict_ban_content_type and query the table and update status to PUB from BAN
                        query_status = restrict_ban_entry_acc.user_restrict_ban_status
                        query_content_type = (
                            restrict_ban_entry_acc.user_restrict_ban_content_type
                        )
                        query_content_id = (
                            restrict_ban_entry_acc.user_restrict_ban_content_id
                        )
                        user_restrict_ban_detail_user_operation(
                            user_id=query_user_id,
                            report_id=query_report_id,
                            status=query_status,
                            db=db,
                        )
                        guideline_violation_score_last_added_score_operation(
                            user_id=query_user_id,
                            report_id=query_report_id,
                            ban_content_type=query_content_type,
                            db=db,
                        )
                        post_comment_operation(
                            ban_content_id=query_content_id,
                            ban_content_type=query_content_type,
                            db=db,
                        )

                else:
                    raise Exception("Error. Account appeal event processing failed")

            elif target.content_type in ("post", "comment"):
                print("Hello2")
                restrict_ban_entry_pc = restrict_ban_entry.first()
                print(restrict_ban_entry)
                if restrict_ban_entry_pc and restrict_ban_entry_pc.is_active == True:
                    print("Hello3")
                    # appeal post/comment is involved in a restrict/ban
                    # get the user_restrict_ban_content_id, user_restrict_ban_content_type and query the table and update status to PUB from BAN
                    # update is_active to False
                    # check for next successive violation and enforce it (is_active to True, enforce_action_at to func.now(), is_enforce_action_early to true)
                    # update user status (check for deactivate/inactive)
                    # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
                    query_status = restrict_ban_entry_pc.user_restrict_ban_status
                    query_content_id = (
                        restrict_ban_entry_pc.user_restrict_ban_content_id
                    )
                    query_content_type = (
                        restrict_ban_entry_pc.user_restrict_ban_content_type
                    )
                    post_comment_operation(
                        ban_content_id=query_content_id,
                        ban_content_type=query_content_type,
                        db=db,
                    )
                    user_restrict_ban_detail_user_operation(
                        user_id=query_user_id,
                        report_id=query_report_id,
                        status=query_status,
                        db=db,
                    )
                    guideline_violation_score_last_added_score_operation(
                        user_id=query_user_id,
                        report_id=query_report_id,
                        ban_content_type=query_content_type,
                        db=db,
                    )

                elif restrict_ban_entry_pc and restrict_ban_entry_pc.is_active in (
                    False,
                    None,
                ):
                    print("Hello4")
                    # appeal post/comment is not involved in a restrict/ban, or maybe the user restrict/ban appeal got closed (no action)
                    # get the ban_content_id, ban_content_type and query the table and update status to PUB from BAN
                    # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
                    query_content_id = target.content_id
                    query_content_type = target.content_type
                    post_comment_operation(
                        ban_content_id=query_content_id,
                        ban_content_type=query_content_type,
                        db=db,
                    )
                    guideline_violation_score_last_added_score_operation(
                        user_id=query_user_id,
                        report_id=query_report_id,
                        ban_content_type=query_content_type,
                        db=db,
                    )

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error", exc)
        except Exception as exc:
            db.rollback()
            print("Error", exc)


event.listen(
    admin_model.UserContentRestrictBanAppealDetail.status,
    "set",
    appeal_status_accept_after_update_attribute_listener,
)
