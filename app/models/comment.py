from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.db_sqlalchemy import Base


# orm model for comment table
class Comment(Base):
    __tablename__ = "comment"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    content = Column(String(length=2200), nullable=False)
    status = Column(String(length=3), nullable=False, server_default=text("'PUB'"))
    is_deleted = Column(Boolean, nullable=False, server_default="False")
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, onupdate=func.now())
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    post_id = Column(
        UUID(as_uuid=True), ForeignKey("post.id", ondelete="CASCADE"), nullable=False
    )
    comment_user = relationship(
        "User", back_populates="comments", foreign_keys=[user_id]
    )
    comment_post = relationship(
        "Post", back_populates="comments", foreign_keys=[post_id]
    )
    likes = relationship("CommentLike", back_populates="like_comment")
    activity = relationship("CommentActivity", back_populates="activity_comment")


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
    status = Column(
        String(length=3),
        nullable=False,
        server_default=text("'ACT'"),
    )
    comment_like_user = relationship(
        "User", back_populates="comment_likes", foreign_keys=[user_id]
    )
    like_comment = relationship(
        "Comment", back_populates="likes", foreign_keys=[comment_id]
    )


# orm model for comment activity table.
class CommentActivity(Base):
    __tablename__ = "comment_activity"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    total_likes = Column(BigInteger, nullable=False, server_default=text("0"))
    comment_id = Column(
        UUID(as_uuid=True), ForeignKey("comment.id", ondelete="CASCADE"), nullable=False
    )
    activity_comment = relationship("Comment", back_populates="activity")
