from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.db_sqlalchemy import Base


# orm model for post table
class Post(Base):
    __tablename__ = "post"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )

    # length param is just a hint for db schema, not a enforced restriction, 20MiB is limit
    image = Column(LargeBinary(length=20971520), nullable=False)
    caption = Column(String(length=2200), nullable=True)
    status = Column(String(length=20), nullable=False)
    is_deleted = Column(Boolean, nullable=False, server_default="False")
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, onupdate=func.now())
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )


# orm model for post like table
class PostLike(Base):
    __tablename__ = "post_like"
    id = Column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        server_default=func.generate_ulid(),
    )
    is_deleted = Column(Boolean, nullable=False, server_default="False")
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    )
    post_id = Column(
        UUID(as_uuid=True), ForeignKey("post.id", ondelete="CASCADE"), primary_key=True
    )


# orm model for post activity table.
class PostActivity(Base):
    __tablename__ = "post_activity"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    total_likes = Column(Integer, nullable=False, server_default=text("0"))
    total_comments = Column(Integer, nullable=False, server_default=text("0"))
    post_id = Column(
        UUID(as_uuid=True), ForeignKey("post.id", ondelete="CASCADE"), nullable=False
    )
