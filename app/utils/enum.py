from enum import Enum


class UserStatusEnum(str, Enum):
    """
    Enum for user status values 'active', 'inactive', 'restricted_partial', 'restricted_full',
    'deactivated_hide', 'deactivated_keep',  'pending_delete_hide', 'pending_delete_keep',
    'ban_temporary', 'ban_permanent', 'deleted'
    """

    ACTIVE = "ACT"
    INACTIVE = "INA"
    RESTRICTED_PARTIAL = "RSP"
    RESTRICTED_FULL = "RSF"
    DEACTIVATED_HIDE = "DAH"
    DEACTIVATED_KEEP = "DAK"
    PENDING_DELETE_HIDE = "PDH"
    PENDING_DELETE_KEEP = "PDK"
    TEMPORARY_BAN = "TBN"
    PERMANENT_BAN = "PBN"
    DELETED = "DEL"


class UserAccountVisibilityEnum(str, Enum):
    """
    Enum for user account_visibility values 'public', 'private'
    """

    PUBLIC = "PBC"
    PRIVATE = "PRV"


class UserTypeEnum(str, Enum):
    """
    Enum for user type values 'standard', 'admin'
    """

    STANDARD = "STD"
    ADMIN = "ADM"


class PostStatusEnum(str, Enum):
    """
    Enum for post status values 'published', 'draft', 'hidden', 'banned', 'deleted'
    """

    PUBLISHED = "PUB"
    DRAFT = "DRF"
    HIDDEN = "HID"
    BANNED = "BAN"
    DELETED = "DEL"


class PostLikeStatusEnum(str, Enum):
    """
    Enum for postlike status values 'active', 'hidden', 'deleted'
    """

    ACTIVE = "ACT"
    HIDDEN = "HID"
    DELETED = "DEL"


class CommentStatusEnum(str, Enum):
    """
    Enum for comment status values 'published', 'hidden', 'banned', 'deleted'
    """

    PUBLISHED = "PUB"
    HIDDEN = "HID"
    BANNED = "BAN"
    DELETED = "DEL"


class CommentLikeStatusEnum(str, Enum):
    """
    Enum for commentlike status values 'active', 'hidden', 'deleted'
    """

    ACTIVE = "ACT"
    HIDDEN = "HID"
    DELETED = "DEL"


class UserFollowAssociationStatusEnum(str, Enum):
    """
    Enum for userfollowassociation status values 'accepted', 'rejected', 'pending', 'unfollowed'
    """

    ACCEPTED = "ACP"
    REJECTED = "REJ"
    PENDING = "PND"
    UNFOLLOWED = "UNF"


class UserAuthTrackStatusEnum(str, Enum):
    """
    Enum for userauthtrack status values 'active', 'expired', 'invalid'
    """

    ACTIVE = "ACT"
    EXPIRED = "EXP"
    INVALID = "INV"


class UserVerificationCodeTokenTypeEnum(str, Enum):
    """
    Enum for userverificationcodetoken type values 'password_reset', 'user_verify', 'ban_verify'
    """

    PASSWORD_RESET = "PWR"
    USER_VERIFY = "USV"
    BAN_VERIFY = "BNV"
