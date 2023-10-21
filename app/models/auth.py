from sqlalchemy import TIMESTAMP, Boolean, Column, Enum, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import ENUM, UUID

from app.db.db_sqlalchemy import Base


class UserAuthTrack(Base):
    __tablename__ = "user_auth_track"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    refresh_token_id = Column(String, nullable=False, unique=True)
    # status = Column(String(length=20), nullable=False, server_default=text("'active'"))
    status = Column(
        Enum(name="user_auth_track_status_enum"),
        nullable=False,
        server_default=text("'ACT'::user_auth_track_status_enum"),
    )
    device_info = Column(String, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, onupdate=func.now())
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )


# class UserPasswordResetToken(Base):
#     __tablename__ = "user_password_reset_token"
#     id = Column(
#         UUID(as_uuid=True),
#         unique=True,
#         nullable=False,
#         server_default=func.generate_ulid(),
#     )
#     reset_token_id = Column(String, primary_key=True)
#     user_id = Column(
#         UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
#     )
#     is_deleted = Column(Boolean, nullable=False, server_default="False")
#     created_at = Column(
#         TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
#     )


class UserVerificationCodeToken(Base):
    __tablename__ = "user_verification_code_token"
    id = Column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        server_default=func.generate_ulid(),
    )
    code_token_id = Column(String, primary_key=True)
    # type = Column(String, nullable=False)
    type = Column(Enum(name="user_verification_code_token_type_enum"), nullable=False)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    )
    is_deleted = Column(Boolean, nullable=False, server_default="False")
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
