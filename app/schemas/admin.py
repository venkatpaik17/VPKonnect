from datetime import datetime, timedelta
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas import comment as comment_schema
from app.schemas import employee as employee_schema
from app.schemas import post as post_schema
from app.schemas import user as user_schema
from app.utils.exception import CustomValidationError


class SendEmail(BaseModel):
    template: str
    email: list[EmailStr]
    body_info: dict[str, Any]


class ReportBaseOutput(BaseModel):
    case_number: int


class ReportRequest(BaseModel):
    status: str


class RestrictBanOutput(BaseModel):
    status: str
    duration: int
    enforced_at: datetime
    enforced_till: datetime


class ReportResponse(ReportRequest):
    case_number: int
    reporter_user: user_schema.UserBaseOutput
    reported_user: user_schema.UserBaseOutput
    reported_item_type: str
    reported_item: (
        post_schema.PostOutput
        | comment_schema.CommentBaseOutput
        | user_schema.UserBaseOutput
    )
    flagged_banned_posts: list[UUID] = Field(
        default_factory=list,
        description="This attribute will only display if it's not an empty list.",
    )
    report_reason: str
    report_reason_user: user_schema.UserBaseOutput = Field(
        None, description="This attribute will only display if it's not None"
    )
    moderator_note: str = Field(
        None, description="This attribute will only display if it's not None"
    )
    account_restrict_ban: RestrictBanOutput = Field(
        None, description="This attribute will only display if it's not None"
    )
    effective_user_status: str
    moderator: employee_schema.EmployeeOutput = Field(
        None, description="This attribute will only display if it's not None"
    )
    reported_at: datetime
    last_updated_at: datetime = Field(
        None, description="This attribute will only display if it's not None"
    )

    @classmethod
    def parse_obj(cls, obj):
        reported_item_type = obj["reported_item_type"]
        reported_item_data = obj["reported_item"]
        account_restrict_ban = obj["account_restrict_ban"]

        if reported_item_type == "post":
            reported_item = post_schema.PostOutput(**reported_item_data)
        elif reported_item_type == "comment":
            reported_item = comment_schema.CommentBaseOutput(**reported_item_data)
        else:
            reported_item = user_schema.UserBaseOutput(**reported_item_data)

        obj["reported_item"] = reported_item

        if account_restrict_ban:
            account_restrict_ban_enforced_at = account_restrict_ban.get(
                "enforce_action_at"
            )
            account_restrict_ban_duration = account_restrict_ban.get("duration")

            account_restrict_ban_enforced_till = (
                account_restrict_ban_enforced_at
                + timedelta(hours=account_restrict_ban_duration)
            )
            account_restrict_ban["enforced_till"] = account_restrict_ban_enforced_till
            account_restrict_ban["enforced_at"] = account_restrict_ban_enforced_at

        obj["account_restrict_ban"] = account_restrict_ban

        return super().parse_obj(obj)

    class Config:
        orm_mode = True


class AllReportResponse(ReportRequest):
    case_number: int
    reported_at: datetime

    class Config:
        orm_mode = True


class ReportUnderReviewUpdate(BaseModel):
    case_number_list: list[int]


class ReportAssignUpdate(ReportUnderReviewUpdate):
    moderator_emp_id: str


class EnforceReportActionAuto(BaseModel):
    case_number: int
    reported_username: str


class EnforceReportActionManual(EnforceReportActionAuto):
    action: Literal["RSP", "RSF", "TBN", "PBN"]
    duration: int
    contents_to_be_banned: list[UUID] | None


class CloseReport(BaseModel):
    moderator_note: Literal["RF", "RNB", "RNF", "RND", "RNU", "SE", "UD", "UDI", "UDB"]


class AppealRequest(BaseModel):
    status: str


class AllAppealResponse(AppealRequest):
    case_number: int
    appealed_at: datetime

    class Config:
        orm_mode = True


class AppealResponse(AppealRequest):
    case_number: int
    appeal_user: user_schema.UserOutput
    report: ReportBaseOutput
    content_type: str
    appealed_content: (
        post_schema.PostOutput
        | comment_schema.CommentBaseOutput
        | user_schema.UserBaseOutput
    )
    appeal_detail: str
    attachment: str = Field(
        None, description="This attribute will only display if it's not None"
    )
    moderator_note: str = Field(
        None, description="This attribute will only display if it's not None"
    )
    moderator: employee_schema.EmployeeOutput = Field(
        None, description="This attribute will only display if it's not None"
    )
    appealed_at: datetime
    last_updated_at: datetime = Field(
        None, description="This attribute will only display if it's not None"
    )

    @classmethod
    def parse_obj(cls, obj):
        print("parse_obj")
        appealed_item_type = obj["content_type"]
        appealed_item_data = obj["appealed_content"]

        if appealed_item_type == "post":
            appealed_content = post_schema.PostOutput(**appealed_item_data)
        elif appealed_item_type == "comment":
            appealed_content = comment_schema.CommentBaseOutput(**appealed_item_data)
        else:
            appealed_content = user_schema.UserBaseOutput(**appealed_item_data)

        obj["appealed_content"] = appealed_content

        return super().parse_obj(obj)

    class Config:
        orm_mode = True


class AppealAction(BaseModel):
    case_number: int
    action: Literal["accept", "reject"]
    appeal_username: str
    moderator_note: Literal["AS", "AF0"]


class AppealUnderReviewUpdate(ReportUnderReviewUpdate):
    pass


class AppealAssignUpdate(AppealUnderReviewUpdate):
    moderator_emp_id: str


class UserSendBanEmail(BaseModel):
    status: str
    email: EmailStr
    username: str
    duration: int
    enforced_action_at: datetime


class UserSendDeleteEmail(BaseModel):
    email: list[EmailStr]
    subject: str
    template: str


class CloseAppeal(BaseModel):
    moderator_note: Literal["AF1", "AF2", "AF3", "AF4", "ANU", "ANPC", "AE", "SE", "UD"]


class AppUserMetrics(BaseModel):
    users_added: int
    users_unverified: int
    users_active: int
    users_inactive: int
    users_restricted_partial: int
    users_restricted_full: int
    users_deactivated: int
    users_pending_delete: int
    users_banned_temp: int
    users_banned_perm: int
    users_unrestricted_partial: int
    users_unrestricted_full: int
    users_unbanned_temp: int
    users_unbanned_perm: int
    users_reactivated: int
    users_restored: int
    users_deleted: int

    class Config:
        orm_mode = True


class AppPostMetrics(BaseModel):
    total_added_posts: int
    total_available_posts: int
    active_posts: int
    draft_posts: int
    hidden_posts: int
    flagged_to_be_banned_posts: int
    banned_posts: int
    flagged_deleted_posts: int
    removed_posts: int

    class Config:
        orm_mode = True


class AppCommentMetrics(BaseModel):
    total_added_comments: int
    total_available_comments: int
    active_comments: int
    hidden_comments: int
    flagged_to_be_banned_comments: int
    banned_comments: int
    flagged_deleted_comments: int
    removed_comments: int

    class Config:
        orm_mode = True


class AppPostLikeMetrics(BaseModel):
    total_likes: int
    total_available_likes: int
    active_likes: int
    hidden_likes: int

    class Config:
        orm_mode = True


class AppCommentLikeMetrics(AppPostLikeMetrics):
    pass


class AppMetricsUserOutput(BaseModel):
    username: str
    profile_picture: str | None

    class Config:
        orm_mode = True


class UsersMaxPosts(BaseModel):
    user: AppMetricsUserOutput
    total_active_posts: int

    class Config:
        orm_mode = True


class UsersMaxComments(BaseModel):
    user: AppMetricsUserOutput
    total_active_comments: int

    class Config:
        orm_mode = True


class PostsMax(BaseModel):
    user: AppMetricsUserOutput
    post_id: UUID
    post_image: str
    post_caption: str | None
    post_datetime: datetime


class PostsMaxComments(PostsMax):
    total_posts_comments: int

    class Config:
        orm_mode = True


class PostsMaxLikes(PostsMax):
    total_posts_likes: int

    class Config:
        orm_mode = True


class CommentsMaxLikes(BaseModel):
    user: AppMetricsUserOutput
    comment_id: UUID
    comment_content: str
    total_comment_likes: int
    comment_datetime: datetime
    post_id: UUID

    class Config:
        orm_mode = True


class UsersMaxFollowers(BaseModel):
    user: AppMetricsUserOutput
    total_followers: int

    class Config:
        orm_mode = True


class UsersMaxFollowing(BaseModel):
    user: AppMetricsUserOutput
    total_following: int

    class Config:
        orm_mode = True


class AppActivityMetricsResponse(BaseModel):
    user_metrics: AppUserMetrics
    post_metrics: AppPostMetrics
    comment_metrics: AppCommentMetrics
    post_like_metrics: AppPostLikeMetrics
    comment_like_metrics: AppCommentLikeMetrics
    users_with_max_posts: list[UsersMaxPosts]
    users_who_commented_max: list[UsersMaxComments]
    posts_with_max_comments: list[PostsMaxComments]
    posts_with_max_likes: list[PostsMaxLikes]
    comments_with_max_likes: list[CommentsMaxLikes]
    users_with_max_followers: list[UsersMaxFollowers]
    users_with_max_following: list[UsersMaxFollowing]

    class Config:
        orm_mode = True
