from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.db_sqlalchemy import Base


# orm model for comment table
class Comment(Base):
    __tablename__ = "comment"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    content = Column(String(length=2200), nullable=False)
    status = Column(
        String(length=20), nullable=False, server_default=text("'published'")
    )
    is_deleted = Column(Boolean, nullable=False, server_default="False")
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, onupdate=func.now())
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    post_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )


# orm model for comment liske table
class CommentLike(Base):
    __tablename__ = "comment_like"
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
    comment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("comment.id", ondelete="CASCADE"),
        primary_key=True,
    )


# orm model for comment activity table.
class CommentActivity(Base):
    __tablename__ = "comment_activity"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    total_likes = Column(Integer, nullable=False, server_default=text("0"))
    comment_id = Column(
        UUID(as_uuid=True), ForeignKey("comment.id", ondelete="CASCADE"), nullable=False
    )
