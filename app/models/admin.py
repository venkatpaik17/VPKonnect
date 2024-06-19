from sqlalchemy import (
    ARRAY,
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    Date,
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


class ActivityDetail(Base):
    __tablename__ = "activity_detail"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    metric = Column(String(length=20), nullable=False)
    count = Column(BigInteger, nullable=False, server_default=text("0"))
    date = Column(Date, nullable=False, server_default=func.now())

    # for keeping day wise total count. no two rows will have same metric and date combined
    UniqueConstraint(metric, date, name="activity_detail_metric_date_unique")


class UserRestrictBanDetail(Base):
    __tablename__ = "user_restrict_ban_detail"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.generate_ulid(),
    )
    status = Column(String(length=3), nullable=False)
    duration = Column(Integer, nullable=False)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCASE"), nullable=False
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )
    is_deleted = Column(Boolean, nullable=False, server_default=text("False"))
    # is_violation = Column(Boolean, nullable=False, server_default=text("True"))
    is_active = Column(Boolean, nullable=False, server_default=text("True"))
    content_type = Column(String, nullable=False)
    content_id = Column(UUID(as_uuid=True), nullable=False)
    report_id = Column(
        UUID(as_uuid=True), ForeignKey("user_content_report_detail.id"), nullable=False
    )
    enforce_action_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    post = relationship(
        "Post",
        foreign_keys=[content_id],
        primaryjoin="and_(UserRestrictBanDetail.content_type=='post', UserRestrictBanDetail.content_id==Post.id)",
        single_parent=True,
        cascade="all, delete-orphan",
    )

    comment = relationship(
        "Comment",
        foreign_keys=[content_id],
        primaryjoin="and_(UserRestrictBanDetail.content_type=='comment', UserRestrictBanDetail.content_id==Comment.id)",
        overlaps="post",
        single_parent=True,
        cascade="all, delete-orphan",
    )
    account = relationship(
        "User",
        foreign_keys=[content_id],
        primaryjoin="and_(UserRestrictBanDetail.content_type=='account', UserRestrictBanDetail.content_id==User.id)",
        overlaps="post, comment",
        single_parent=True,
        cascade="all, delete-orphan",
    )


class UserContentReportDetail(Base):
    __tablename__ = "user_content_report_detail"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.generate_ulid(),
    )
    reporter_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    reported_item_id = Column(UUID(as_uuid=True), nullable=False)
    reported_item_type = Column(String(), nullable=False)
    reported_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_number = Column(
        BigInteger(),
        nullable=False,
        server_default=func.get_next_value_from_sequence(),
        unique=True,
    )
    report_reason = Column(String(length=10), nullable=False)
    report_reason_user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=True
    )
    status = Column(
        String(length=3),
        nullable=False,
        server_default=text("'OPN'"),
    )
    moderator_note = Column(String(), nullable=True)
    is_deleted = Column(Boolean(), nullable=False, server_default=text("False"))
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, onupdate=func.now())
    moderator_id = Column(
        UUID(as_uuid=True),
        ForeignKey("employee.id", ondelete="CASCADE"),
        nullable=True,
    )

    post = relationship(
        "Post",
        foreign_keys=[reported_item_id],
        primaryjoin="and_(UserContentReportDetail.reported_item_type=='post', UserContentReportDetail.reported_item_id==Post.id)",
        single_parent=True,
        cascade="all, delete-orphan",
    )

    comment = relationship(
        "Comment",
        foreign_keys=[reported_item_id],
        primaryjoin="and_(UserContentReportDetail.reported_item_type=='comment', UserContentReportDetail.reported_item_id==Comment.id)",
        overlaps="post",
        single_parent=True,
        cascade="all, delete-orphan",
    )

    account = relationship(
        "User",
        foreign_keys=[reported_item_id],
        primaryjoin="and_(UserContentReportDetail.reported_item_type=='account', UserContentReportDetail.reported_item_id==User.id)",
        overlaps="comment, post",
        single_parent=True,
        cascade="all, delete-orphan",
    )

    reporter_user = relationship("User", foreign_keys=[reporter_user_id])
    reported_user = relationship("User", foreign_keys=[reported_user_id])
    report_reason_user = relationship("User", foreign_keys=[report_reason_user_id])
    moderator = relationship("Employee", foreign_keys=[moderator_id])


class GuidelineViolationScore(Base):
    __tablename__ = "guideline_violation_score"
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.generate_ulid()
    )
    post_score = Column(Integer(), nullable=False, server_default=text("0"))
    comment_score = Column(Integer(), nullable=False, server_default=text("0"))
    message_score = Column(Integer(), nullable=False, server_default=text("0"))
    final_violation_score = Column(Integer(), nullable=False, server_default=text("0"))
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True, onupdate=func.now())
    # last_added_score = Column(Integer(), nullable=False, server_default=text("0"))

    last_added_scores = relationship(
        "GuidelineViolationLastAddedScore", back_populates="score"
    )


class UserContentRestrictBanAppealDetail(Base):
    __tablename__ = "user_content_restrict_ban_appeal_detail"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.generate_ulid(),
    )
    case_number = Column(
        BigInteger(),
        unique=True,
        nullable=False,
        server_default=func.get_next_value_from_sequence_ban_appeal_table(),
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    report_id = Column(
        UUID(as_uuid=True), ForeignKey("user_content_report_detail.id"), nullable=False
    )
    content_type = Column(String(), nullable=False)
    content_id = Column(UUID(as_uuid=True), nullable=False)
    appeal_detail = Column(String(), nullable=False)
    attachment = Column(String(), nullable=True)
    status = Column(String(length=3), nullable=False, server_default=text("'OPN'"))
    moderator_id = Column(
        UUID(as_uuid=True), ForeignKey("employee.id", ondelete="CASCADE"), nullable=True
    )
    moderator_note = Column(String(), nullable=True)
    is_deleted = Column(Boolean(), nullable=False, server_default=text("False"))
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

    post = relationship(
        "Post",
        foreign_keys=[content_id],
        primaryjoin="and_(UserContentRestrictBanAppealDetail.content_type=='post', UserContentRestrictBanAppealDetail.content_id==Post.id)",
        single_parent=True,
        cascade="all, delete-orphan",
    )

    comment = relationship(
        "Comment",
        foreign_keys=[content_id],
        primaryjoin="and_(UserContentRestrictBanAppealDetail.content_type=='comment', UserContentRestrictBanAppealDetail.content_id==Comment.id)",
        overlaps="post",
        single_parent=True,
        cascade="all, delete-orphan",
    )
    account = relationship(
        "User",
        foreign_keys=[content_id],
        primaryjoin="and_(UserContentRestrictBanAppealDetail.content_type=='account', UserContentRestrictBanAppealDetail.content_id==User.id)",
        overlaps="post, comment",
        single_parent=True,
        cascade="all, delete-orphan",
    )


class AppealRestrictJoinView(Base):
    __tablename__ = "appeal_restrict_join_view"
    id = Column(BigInteger(), primary_key=True)
    user_id = Column(UUID(as_uuid=True))
    report_id = Column(UUID(as_uuid=True))
    appeal_content_type = Column(String())
    appeal_content_id = Column(UUID(as_uuid=True))
    appeal_status = Column(String(length=3))
    user_restrict_ban_status = Column(String(length=3))
    user_restrict_ban_duration = Column(Integer())
    user_restrict_ban_is_deleted = Column(Boolean())
    user_restrict_ban_is_active = Column(Boolean())
    user_restrict_ban_content_type = Column(String())
    user_restrict_ban_content_id = Column(UUID(as_uuid=True))


class GuidelineViolationLastAddedScore(Base):
    __tablename__ = "guideline_violation_last_added_score"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.generate_ulid(),
    )
    last_added_score = Column(Integer(), nullable=False)
    is_removed = Column(Boolean(), nullable=False, server_default=text("False"))
    is_deleted = Column(Boolean(), nullable=False, server_default=text("False"))
    score_id = Column(
        UUID(as_uuid=True),
        ForeignKey("guideline_violation_score.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_content_report_detail.id", ondelete="CASCADE"),
        nullable=False,
    )
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
    is_added = Column(Boolean(), nullable=False, server_default=text("True"))

    score = relationship("GuidelineViolationScore", back_populates="last_added_scores")


class AccountReportFlaggedContent(Base):
    __tablename__ = "account_report_flagged_content"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.generate_ulid(),
    )
    valid_flagged_content = Column(UUID(as_uuid=True), nullable=False)
    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_content_report_detail.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_deleted = Column(Boolean(), nullable=False, server_default=text("False"))
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
