from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID

from app.db.db_sqlalchemy import Base


class UserAuthTrack(Base):
    __tablename__ = "user_auth_track"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    refresh_token_id = Column(String, nullable=False, unique=True)
    status = Column(String(length=20), nullable=False, server_default=text("'active'"))
    device_info = Column(String, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, onupdate=func.now())
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )


class UserPasswordResetToken(Base):
    __tablename__ = "user_password_reset_token"
    id = Column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        server_default=func.generate_ulid(),
    )
    reset_token_id = Column(String, primary_key=True)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    )
    is_deleted = Column(Boolean, nullable=False, server_default="False")
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
