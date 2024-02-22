from enum import unique

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.db_sqlalchemy import Base


class Employee(Base):
    __tablename__ = "employee"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    emp_id = Column(String(length=16), nullable=False, unique=True)
    first_name = Column(String(length=50), nullable=False)
    last_name = Column(String(length=50), nullable=False)
    password = Column(String(length=65), nullable=False)
    personal_email = Column(String(length=320), nullable=False, unique=True)
    work_email = Column(String(length=320), nullable=False, unique=True)
    country_phone_code = Column(String(length=10), nullable=False)
    phone_number = Column(String(length=12), nullable=False)
    date_of_birth = Column(Date(), nullable=False)
    age = Column(Integer(), nullable=False)
    profile_picture = Column(String(), nullable=True)
    gender = Column(String(length=1), nullable=False)
    aadhaar = Column(String(length=12), nullable=False, unique=True)
    pan = Column(String(length=10), nullable=False, unique=True)
    address_line_1 = Column(Text(), nullable=False)
    address_line_2 = Column(Text(), nullable=True)
    city = Column(String(), nullable=False)
    state_province = Column(String(), nullable=False)
    zip_postal_code = Column(String(length=16), nullable=False)
    country = Column(String(length=3), nullable=False)
    join_date = Column(Date(), nullable=False)
    termination_date = Column(Date(), nullable=True)
    status = Column(
        String(length=3),
        nullable=False,
        server_default=text("'ACP'"),
    )
    type = Column(String(length=3), nullable=False)
    designation = Column(String(), nullable=False)
    supervisor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("employee.id", ondelete="CASCADE"),
        nullable=True,
    )
    is_deleted = Column(Boolean(), server_default="False", nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )


class EmployeeSession(Base):
    __tablename__ = "employee_session"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.generate_ulid(),
    )
    device_info = Column(String(), nullable=False)
    login_at = Column(
        TIMESTAMP(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    )
    logout_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )
    employee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("employee.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_active = Column(Boolean(), server_default=text("True"), nullable=False)
