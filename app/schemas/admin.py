from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas import comment as comment_schema
from app.schemas import employee as employee_schema
from app.schemas import post as post_schema
from app.schemas import user as user_schema


class SendEmail(BaseModel):
    template: str
    email: list[EmailStr]
    body_info: dict[str, Any]


class ReportRequest(BaseModel):
    status: str


class ReportResponse(ReportRequest):
    reporter_user: user_schema.UserOutput
    reported_user: user_schema.UserOutput
    reported_item_type: str
    reported_item: (
        post_schema.PostOutput | comment_schema.CommentOutput | user_schema.UserOutput
    )
    flagged_banned_posts: list[UUID] = Field(
        default_factory=list,
        description="This attribute will only display if it's not an empty list.",
    )
    case_number: int
    report_reason: str
    report_reason_user: user_schema.UserOutput = Field(
        None, description="This attribute will only display if it's not None"
    )
    moderator_note: str = Field(
        None, description="This attribute will only display if it's not None"
    )
    moderator: employee_schema.EmployeeOutput = Field(
        None, description="This attribute will only display if it's not None"
    )
    reported_at: datetime

    @classmethod
    def parse_obj(cls, obj):
        print("parse_obj")
        reported_item_type = obj["reported_item_type"]
        reported_item_data = obj["reported_item"]

        if reported_item_type == "post":
            reported_item = post_schema.PostOutput(**reported_item_data)
        elif reported_item_type == "comment":
            reported_item = comment_schema.CommentOutput(**reported_item_data)
        else:
            reported_item = user_schema.UserOutput(**reported_item_data)

        obj["reported_item"] = reported_item

        return super().parse_obj(obj)

    class Config:
        orm_mode = True


class AllReportRequest(ReportRequest):
    emp_id: str | None
    reported_at: date | None


class AllReportResponse(ReportRequest):
    case_number: int
    reported_at: datetime

    class Config:
        orm_mode = True


class ReportUnderReviewUpdate(BaseModel):
    case_number_list: list[int]


class EnforceReportActionAuto(BaseModel):
    case_number: int
    reported_username: str
    moderator_emp_id: str


class EnforceReportActionManual(EnforceReportActionAuto):
    action: str
    duration: int
    contents_to_be_banned: list[UUID] | None


class CloseReport(BaseModel):
    reported_username: str
    moderator_note: str
    moderator_emp_id: str


class AppealAction(BaseModel):
    case_number: int
    user_id: UUID
    report_id: UUID
    content_type: str
    content_id: UUID
    action: str
    moderator_id: UUID
