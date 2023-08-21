from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Date,
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


# orm model for user follow association table. Keeps track of user's followers and following
class UserFollowAssociation(Base):
    __tablename__ = "user_follow_association"
    status = Column(String(length=20), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    follower_user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    )
    followed_user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    )
    follower = relationship(
        "User", back_populates="following", foreign_keys=[follower_user_id]
    )
    followed = relationship(
        "User", back_populates="followers", foreign_keys=[followed_user_id]
    )


# user orm model to create user table, here id is ulid generated db/server side using function and stored as uuid in the table.
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

    # length param is just a hint for db schema, not a enforced restriction, 3MiB is limit
    profile_picture = Column(LargeBinary(length=3145728), nullable=True)
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

    followers = relationship(
        "UserFollowAssociation",
        back_populates="followed",
        primaryjoin=id == UserFollowAssociation.followed_user_id,
    )

    following = relationship(
        "UserFollowAssociation",
        back_populates="follower",
        primaryjoin=id == UserFollowAssociation.follower_user_id,
    )
    usernames = relationship("UsernameChanegHistory", back_populates="username_user")
    passwords = relationship("PasswordChangeHistory", back_populates="password_user")
    sessions = relationship("UserSession", back_populates="session_user")
    posts = relationship("Post", back_populates="post_user")
    post_likes = relationship("PostLike", back_populates="post_like_user")
    comments = relationship("Comment", back_populates="comment_user")
    comment_likes = relationship("CommentLike", back_populates="comment_like_user")


# orm model for username change history table. previous usernames are saved.
class UsernameChangeHistory(Base):
    __tablename__ = "username_change_history"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    previous_username = Column(String(length=30), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    username_user = relationship("User", back_populates="usernames")


# orm model for password change history table. previous passwords are not saved.
class PasswordChangeHistory(Base):
    __tablename__ = "password_change_history"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    password_user = relationship("User", back_populates="passwords")


# orm model for user session table. Keeps track of user's sessions
class UserSession(Base):
    __tablename__ = "user_session"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    device_info = Column(String, nullable=False)
    login_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    logout_at = Column(TIMESTAMP(timezone=True), nullable=True, onupdate=func.now())
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    is_active = Column(Boolean, nullable=False, server_default=text("True"))
    session_user = relationship("User", back_populates="sessions")
