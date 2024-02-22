from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr

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
    reported_item: (
        post_schema.PostOutput | comment_schema.CommentOutput | user_schema.UserOutput
    )
    reported_item_type: str
    case_number: int
    report_reason: str
    report_reason_user: user_schema.UserOutput | None
    moderator_note: str | None
    moderator: employee_schema.EmployeeOutput | None
    reported_at: datetime

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
    reported_user_id: UUID
    reported_item_type: str
    reported_item_id: UUID
    report_reason: str


class EnforceReportActionManual(EnforceReportActionAuto):
    action: str
    duration: int
