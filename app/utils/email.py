from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from app.config.app import settings


def send_email(username: str, email: str, reset_link: str, bg_tasks: BackgroundTasks):
    email_body = f"""\
        <html>
            <head></head>
            <body>
                <h2>VPKonnect</h2>
                <p>Hello {username},</p>
                <p>You have requested a password reset for your account. Please click the link below to reset your password:</p>
                <p><a href="{reset_link}">Reset Password</a></p>
                <p>If you did not request this password reset, you can safely ignore this email.</p>
                <p>Regards,</p>
                <p>VPKonnect Admin Team</p>
            </body>
        </html>
        """

    conf = ConnectionConfig(
        MAIL_USERNAME=settings.email_settings.email_username,
        MAIL_PASSWORD=settings.email_settings.email_password,
        MAIL_FROM=settings.email_settings.email_from,
        MAIL_PORT=settings.email_settings.email_port,
        MAIL_SERVER=settings.email_settings.email_host,
        MAIL_STARTTLS=False,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )

    message = MessageSchema(
        subject="VPKonnect - Password Reset Request",
        recipients=[EmailStr(email)],
        body=email_body,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    bg_tasks.add_task(fm.send_message, message)
