from datetime import timedelta
from time import sleep

from fastapi import BackgroundTasks
from pydantic import EmailStr
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
metadata.reflect(views=True)

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


def user_restrict_ban_detail_user_operation(
    user_id: str,
    report_id: str,
    status: str,
    db: Session,
    background_tasks: BackgroundTasks,
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

    user_inactive_deactivated = ["DAH", "DAK", "PDH", "PDK", "INA"]
    if consecutive_violation:
        # enforce next violation, this will be early enforce
        consecutive_violation_query.update(
            {
                "is_active": True,
                "enforce_action_at": func.now(),
                "is_enforce_action_early": True,
            },
            synchronize_session=False,
        )

        # get user
        user = user_service.get_user_by_id(
            str(consecutive_violation.user_id),
            ["ACT", "TBN", "PBN", "DEL"],
            db,
        )
        if user:
            job_task_utils.consecutive_violation_operations(
                consecutive_violation=consecutive_violation, db=db
            )

            # send email if status is TBN/PBN
            if consecutive_violation.status == "PBN" or (
                consecutive_violation.status == "TBN"
                and user.status not in user_inactive_deactivated
            ):
                # generate appeal link
                appeal_link = "https://vpkonnect.in/accounts/appeals/form_ban"

                email_subject = "VPKonnect - Account Ban"
                email_details = admin_schema.SendEmail(
                    template=(
                        "permanent_ban_email.html"
                        if consecutive_violation.status == "PBN"
                        else "temporary_ban_email.html"
                    ),
                    email=[EmailStr(user.email)],
                    body_info={
                        "username": user.username,
                        "link": appeal_link,
                        "days": consecutive_violation.duration // 24,
                        "ban_enforced_datetime": consecutive_violation.enforce_action_at.strftime(
                            "%b %d, %Y %H:%M %Z"
                        ),
                    },
                )

                email_utils.send_email(email_subject, email_details, background_tasks)

            # update user status
            if user.status not in user_inactive_deactivated or (
                user.status in user_inactive_deactivated
                and consecutive_violation.status == "PBN"
            ):
                user.status = consecutive_violation.status

        else:
            raise Exception("Error. User entry for changing status not found")

    else:
        user = user_service.get_user_by_id(user_id, ["ACT", "TBN", "PBN", "DEL"], db)
        if user and user.status not in user_inactive_deactivated:
            user.status = "ACT"


def guideline_violation_score_last_added_score_operation(
    user_id: str,
    report_id: str,
    ban_content_type: str,
    db: Session,
    account_report_flagged_posts: int,
    posts_to_be_unbanned: int,
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

    # for account report cases, where many flagged posts are involved, some posts unbanned through different appeals, some remain unbanned or not unbanned at all
    # So only the fraction of last_added_score will be considered
    effective_last_added_score = int(
        (posts_to_be_unbanned / account_report_flagged_posts) * last_added_score
    )

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

    # Access the reflected view
    join_view = metadata.tables["appeal_restrict_join_view"]

    if oldvalue is not None and (oldvalue == "URV" and value == "ACP"):
        print("Hello")
        db = next(get_db())

        # join_model = aliased(admin_model.AppealRestrictJoinView)

        # query the view
        appeal_restrict_join_entries_query = db.query(join_view)
        print(target.user_id)

        # get the required entry using user id and report id
        restrict_ban_appeal_entry_query = appeal_restrict_join_entries_query.filter(
            join_view.c.user_id == target.user_id,
            join_view.c.report_id == target.report_id,
            join_view.c.user_restrict_ban_is_deleted == False,
        )

        restrict_ban_appeal_entry = restrict_ban_appeal_entry_query.first()
        if not restrict_ban_appeal_entry:
            raise Exception("Error. Entry associated with accepted appeal not found")

        print(restrict_ban_appeal_entry)

        query_user_id = target.user_id
        query_report_id = target.report_id
        query_content_id = None
        query_content_type = None
        query_status = None

        try:
            print("Hello1")

            if target.content_type == "account":
                # Appeal type: account, Report type: account
                if (
                    restrict_ban_appeal_entry.user_restrict_ban_content_type
                    == "account"
                ):
                    # fetch the flagged posts from account_report_flagged_content, check if all or partial no of posts, change the status from BAN to PUB
                    # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
                    # revoke the active restrict/ban, activate consecutive violation if any (set enforce_action_at with func.now() and is_enforce_action_early as True), update user status
                    account_report_valid_flagged_content = (
                        admin_service.get_all_valid_flagged_content_account_report_id(
                            report_id=query_report_id, db_session=db
                        )
                    )
                    account_report_flagged_content_ids = [
                        content[0] for content in account_report_valid_flagged_content
                    ]
                    no_of_flagged_posts = len(account_report_flagged_content_ids)

                    account_report_flagged_posts = (
                        post_service.get_all_posts_by_id_query(
                            post_id_list=account_report_flagged_content_ids,
                            status_in_list=["BAN"],
                            db_session=db,
                        ).all()
                    )
                    no_of_banned_posts = len(account_report_flagged_posts)

                    for post in account_report_flagged_posts:
                        post.status = "PUB"

                    query_content_type = (
                        restrict_ban_appeal_entry.user_restrict_ban_content_type
                    )
                    guideline_violation_score_last_added_score_operation(
                        user_id=query_user_id,
                        report_id=query_report_id,
                        ban_content_type=query_content_type,
                        db=db,
                        account_report_flagged_posts=no_of_flagged_posts,
                        posts_to_be_unbanned=no_of_banned_posts,
                    )

                    query_status = restrict_ban_appeal_entry.user_restrict_ban_status
                    # user_restrict_ban_detail_user_operation(
                    #     user_id=query_user_id,
                    #     report_id=query_report_id,
                    #     status=query_status,
                    #     db=db,
                    #     background_tasks=BackgroundTasks,
                    # )

                # Appeal type: account, Report type: post/comment
                elif restrict_ban_appeal_entry.user_restrict_ban_content_type in (
                    "post",
                    "comment",
                ):
                    # revoke the active restrict/ban, activate consecutive violation if any (set enforce_action_at with func.now() and is_enforce_action_early as True), update user status
                    # fetch the banned post/comment and change the status to PUB
                    # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
                    pass
            elif target.content_type in ("post", "comment"):
                if (
                    target.content_type == "post"
                    and restrict_ban_appeal_entry.user_restrict_ban_content_type
                    == "account"
                ):
                    # Appeal type: post, Report type: account, (RSP/RSF, active restrict)
                    if restrict_ban_appeal_entry.user_restrict_ban_is_active == "True":
                        # fetch the post, change the status to PUB
                        # fetch the flagged posts from account_report_flagged_content
                        #     check if all the flagged posts have PUB status, if yes then revoke the restrict, else don't
                        #     adjust the scores in guideline violation score table
                        # If all posts have their bans revoked then only fetch last added score and manage it, update is_removed to True
                        #     Else don't touch the last added score table
                        # if restrict is revoked, activate consecutive violation if any (set enforce_action_at with func.now() and is_enforce_action_early as True), update user status
                        pass
                    # Appeal type: post, Report type: account (RSP/RSF, no active restrict)
                    else:
                        # fetch the post, change status to PUB
                        # adjust the scores in guideline violation score table
                        pass
                elif restrict_ban_appeal_entry.user_restrict_ban_content_type in (
                    "post",
                    "comment",
                ):
                    # Appeal type: post/comment, Report type: post/comment (active restrict/ban)
                    if restrict_ban_appeal_entry.user_restrict_ban_is_active == "True":
                        # fetch the banned post/comment, update status to PUB
                        # revoke the active restrict/ban, activate consecutive violation if any (set enforce_action_at with func.now() and is_enforce_action_early as True), update user status
                        # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
                        pass
                    # Appeal type: post/comment, Report type: post/comment (active restrict/ban concluded)
                    elif (
                        restrict_ban_appeal_entry.user_restrict_ban_is_active == "False"
                    ):
                        # fetch the post, change status to PUB
                        # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
                        pass
                    # Appeal type: post/comment, Report type: post/comment (no restrict/ban entry)
                    elif restrict_ban_appeal_entry.user_restrict_ban_is_active is None:
                        # fetch the post, change status to PUB
                        pass

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error:", exc)
        except Exception as exc:
            db.rollback()
            print("Error", exc)


event.listen(
    admin_model.UserContentRestrictBanAppealDetail.status,
    "set",
    appeal_status_accept_after_update_attribute_listener,
)


# event trigger for REJ status in appeal
def appeal_status_reject_after_update_attribute_listener(
    target, value, oldvalue, initiator
):
    if oldvalue is not None and (oldvalue == "URV" and value == "REJ"):
        db: Session = next(get_db())
        try:
            if target.content_type == "account":
                # PBN
                # get the ban entry using report id
                # check if the appeal rejection happenned after 21 days appeal limit or not
                # If yes, then get the user using user_id
                # update user status to PDB
                # update is_active of ban entry to False
                ban_entry = admin_service.get_user_active_restrict_ban_entry_report_id(
                    report_id=target.report_id, db_session=db
                )
                if not ban_entry:
                    raise Exception(
                        "Error. Ban entry associated with rejected appeal not found"
                    )

                if ban_entry.status == "PBN":
                    if target.updated_at > (
                        ban_entry.enforce_action_at + timedelta(days=21)
                    ):
                        # PBN user
                        pbn_appeal_reject_user_query = (
                            user_service.get_user_by_id_query(
                                user_id=target.user_id,
                                status_not_in_list=[
                                    "ACT",
                                    "INA",
                                    "RSP",
                                    "RSF",
                                    "TBN",
                                    "PDB",
                                    "PDI",
                                    "DAH",
                                    "DAK",
                                    "PDH",
                                    "DEL",
                                ],
                                db_session=db,
                            )
                        )

                        pbn_appeal_reject_user_query.update(
                            {"status": "PDB"},
                            synchronize_session=False,
                        )

                        ban_entry.is_active = False

                        db.commit()
            elif target.content_type in ("post", "comment"):
                # post/comment
                # get the post/comment using content id and content type
                # check if appeal rejection happened after 21 days appeal limit or not
                # if yes, update the is_deleted of post/comment to True
                if target.content_type == "post":
                    appeal_reject_post = post_service.get_a_post(
                        post_id=str(target.content_id),
                        status_not_in_list=["PUB", "DRF", "HID", "DEL", "FLB", "FLD"],
                        db_session=db,
                    )
                    if not appeal_reject_post:
                        raise Exception(
                            "Error. Post associated with rejected appeal not found"
                        )

                    if target.updated_at > (
                        appeal_reject_post.updated_at + timedelta(days=21)
                    ):
                        appeal_reject_post.is_deleted = True

                        db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error:", exc)
        except Exception as exc:
            db.rollback()
            print("Error", exc)


event.listen(
    admin_model.UserContentRestrictBanAppealDetail.status,
    "set",
    appeal_status_reject_after_update_attribute_listener,
)
