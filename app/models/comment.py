from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
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
    is_ban_final = Column(Boolean, nullable=False, server_default="False")
    comment_user = relationship(
        "User", back_populates="comments", foreign_keys=[user_id]
    )
    published_comment_post = relationship(
        "Post", back_populates="published_comments", foreign_keys=[post_id]
    )
    flagged_comment_post = relationship(
        "Post",
        back_populates="flagged_comments",
        foreign_keys=[post_id],
        overlaps="published_comment_post",
    )
    likes = relationship("CommentLike", back_populates="like_comment")
    # activity = relationship("CommentActivity", back_populates="activity_comment")


# orm model for comment liske table
class CommentLike(Base):
    __tablename__ = "comment_like"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.generate_ulid(),
    )
    is_deleted = Column(Boolean, nullable=False, server_default="False")
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    comment_id = Column(
        UUID(as_uuid=True), ForeignKey("comment.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(
        String(length=3),
        nullable=False,
        server_default=text("'ACT'"),
    )
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, onupdate=func.now())
    UniqueConstraint(
        "user_id",
        "comment_id",
        "status",
        "created_at",
        name="comment_like_comment_id_user_id_status_created_at_key",
    )
    comment_like_user = relationship(
        "User", back_populates="comment_likes", foreign_keys=[user_id]
    )
    like_comment = relationship(
        "Comment", back_populates="likes", foreign_keys=[comment_id]
    )


# # orm model for comment activity table.
# class CommentActivity(Base):
#     __tablename__ = "comment_activity"
#     id = Column(
#         UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
#     )
#     total_likes = Column(BigInteger, nullable=False, server_default=text("0"))
#     comment_id = Column(
#         UUID(as_uuid=True), ForeignKey("comment.id", ondelete="CASCADE"), nullable=False
#     )
#     activity_comment = relationship("Comment", back_populates="activity")
