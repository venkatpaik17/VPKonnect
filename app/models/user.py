from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Date,
    Integer,
    LargeBinary,
    String,
    func,
    text,
    update,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.db_sqlalchemy import Base, engine


# this is user orm model to create user table, here id is ulid generated db/server side using function and stored as uuid in the table.
class User(Base):
    __tablename__ = "user"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    first_name = Column(String(length=50), nullable=False)
    last_name = Column(String(length=50), nullable=False)
    username = Column(String(length=320), nullable=False, unique=True)
    password = Column(String(length=65), nullable=False)
    email = Column(String(length=320), nullable=False, unique=True)
    date_of_birth = Column(Date, nullable=False)
    age = Column(Integer, nullable=False)

    # length param is just a hint for db schema, not a enforced restriction
    profile_picture = Column(LargeBinary(length=3072), nullable=True)
    gender = Column(String(length=1), nullable=False)
    bio = Column(String(length=150), nullable=True)
    country = Column(String(length=3), nullable=True)
    account_visibility = Column(
        String(length=20), nullable=False, server_default=text("'public'")
    )
    status = Column(String(length=20), nullable=False, server_default=text("'active'"))
    type = Column(String(length=20), nullable=False, server_default=text("'standard'"))
    is_deleted = Column(Boolean, nullable=False, server_default="False")
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, onupdate=func.now())


# testing onupdate for updated_at column
stmt = update(User).where(User.first_name == "vpk").values(gender="F")
with engine.connect() as conn:
    result = conn.execute(stmt)
    conn.commit()
