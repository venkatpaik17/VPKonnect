from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
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

    # length param is just a hint for db schema, not a enforced restriction, 20MiB is limit
    # image = Column(LargeBinary(length=20971520), nullable=False)
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
    post_user = relationship("User", back_populates="posts")
    likes = relationship("PostLike", back_populates="like_post")
    activity = relationship("PostActivity", back_populates="activity_post")
    comments = relationship("Comment", back_populates="comment_post")


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
    status = Column(
        "status",
        String(length=3),
        nullable=False,
        server_default=text("'ACT'"),
    )
    post_like_user = relationship(
        "User", back_populates="post_likes", foreign_keys=[user_id]
    )
    like_post = relationship("Post", back_populates="likes", foreign_keys=[post_id])


# orm model for post activity table.
class PostActivity(Base):
    __tablename__ = "post_activity"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    total_likes = Column(BigInteger, nullable=False, server_default=text("0"))
    total_comments = Column(BigInteger, nullable=False, server_default=text("0"))
    post_id = Column(
        UUID(as_uuid=True), ForeignKey("post.id", ondelete="CASCADE"), nullable=False
    )
    activity_post = relationship("Post", back_populates="activity")
