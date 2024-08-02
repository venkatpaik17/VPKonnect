from pathlib import Path

from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.config.app import settings
from app.schemas import admin as admin_schema

conf = ConnectionConfig(
    MAIL_USERNAME=settings.email_settings.email_username,
    MAIL_PASSWORD=settings.email_settings.email_password,
    MAIL_FROM=settings.email_settings.email_from,
    MAIL_PORT=settings.email_settings.email_port,
    MAIL_SERVER=settings.email_settings.email_host,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates",
)


def send_email(
    email_subject: str, email_details: admin_schema.SendEmail, bg_tasks: BackgroundTasks
):
    message = MessageSchema(
        subject=email_subject,
        recipients=email_details.email,
        template_body=email_details.body_info,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    bg_tasks.add_task(fm.send_message, message, template_name=email_details.template)
