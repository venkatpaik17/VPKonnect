from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID

from app.db.db_sqlalchemy import Base


class UserAuthTrack(Base):
    __tablename__ = "user_auth_track"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    refresh_token_id = Column(String, nullable=False, unique=True)
    status = Column(String(length=3), nullable=False, server_default=text("'ACT'"))
    device_info = Column(String, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, onupdate=func.now())
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    is_deleted = Column(Boolean(), server_default=text("False"), nullable=False)


class UserVerificationCodeToken(Base):
    __tablename__ = "user_verification_code_token"
    id = Column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        server_default=func.generate_ulid(),
    )
    code_token_id = Column(String, primary_key=True)
    type = Column(String(length=3), nullable=False)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    )
    is_deleted = Column(Boolean, nullable=False, server_default="False")
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )


class EmployeeAuthTrack(Base):
    __tablename__ = "employee_auth_track"
    id = Column(
        UUID(as_uuid=True), server_default=func.generate_ulid(), primary_key=True
    )
    refresh_token_id = Column(String(), nullable=False, unique=True)
    status = Column(
        String(length=20),
        server_default=text("'ACT'"),
        nullable=False,
    )
    device_info = Column(String(), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )
    employee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("employee.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_deleted = Column(Boolean(), server_default=text("False"), nullable=False)
