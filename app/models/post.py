from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.db_sqlalchemy import Base


# orm model for post table
class Post(Base):
    __tablename__ = "post"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )

    image = Column(String, nullable=False)
    caption = Column(String(length=2200), nullable=True)
    status = Column(String(length=3), nullable=False)
    is_deleted = Column(Boolean, nullable=False, server_default="False")
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, onupdate=func.now())
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    is_ban_final = Column(Boolean, nullable=False, server_default="False")
    post_user = relationship("User", back_populates="posts")
    likes = relationship("PostLike", back_populates="like_post")

    published_comments = relationship(
        "Comment",
        primaryjoin="and_(Post.id == Comment.post_id, Comment.status == 'PUB', Comment.is_deleted == False)",
        back_populates="published_comment_post",
        overlaps="flagged_comment_post",
    )
    flagged_comments = relationship(
        "Comment",
        primaryjoin="and_(Post.id == Comment.post_id, Comment.status == 'FLB', Comment.is_deleted == False)",
        back_populates="flagged_comment_post",
        overlaps="published_comments, published_comment_post",
    )


# orm model for post like table
class PostLike(Base):
    __tablename__ = "post_like"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.generate_ulid(),
    )
    is_deleted = Column(Boolean, nullable=False, server_default="False")
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"))
    post_id = Column(UUID(as_uuid=True), ForeignKey("post.id", ondelete="CASCADE"))
    status = Column(
        "status",
        String(length=3),
        nullable=False,
        server_default=text("'ACT'"),
    )
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, onupdate=func.now())
    UniqueConstraint(
        "user_id",
        "post_id",
        "status",
        "created_at",
        name="post_like_post_id_user_id_status_created_at_key",
    )
    post_like_user = relationship(
        "User", back_populates="post_likes", foreign_keys=[user_id]
    )
    like_post = relationship("Post", back_populates="likes", foreign_keys=[post_id])
