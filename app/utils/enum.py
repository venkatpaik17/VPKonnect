# not used
from enum import Enum


class UserStatusEnum(str, Enum):
    """
    Enum for user status values 'active', 'inactive', 'restricted_partial', 'restricted_full',
    'deactivated_hide', 'pending_delete_hide', 'pending_delete_ban', 'pending_delete_inactive',
    'temporary_ban', 'permanent_ban', 'deleted'
    """

    ACTIVE = "ACT"
    INACTIVE = "INA"
    RESTRICTED_PARTIAL = "RSP"
    RESTRICTED_FULL = "RSF"
    DEACTIVATED_HIDE = "DAH"
    PENDING_DELETE_HIDE = "PDH"
    PENDING_DELETE_BAN = "PDB"
    PENDING_DELETE_INACTIVE = "PDI"
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
    Enum for user type values 'standard', 'verified', 'business', 'government'
    """

    STANDARD = "STD"
    VERIFIED = "VER"
    BUSINESS = "BUS"
    GOVERNMENT = "GOV"


class PostStatusEnum(str, Enum):
    """
    Enum for post status values 'published', 'draft', 'hidden', 'banned', 'removed',
    'flagged_to_be_banned', 'flagged_deleted'
    """

    PUBLISHED = "PUB"
    DRAFT = "DRF"
    HIDDEN = "HID"
    BANNED = "BAN"
    REMOVED = "RMV"
    FLAGGED_TO_BE_BANNED = "FLB"
    FLAGGED_DELETED = "FLD"


class PostLikeStatusEnum(str, Enum):
    """
    Enum for postlike status values 'active', 'hidden', 'removed'
    """

    ACTIVE = "ACT"
    HIDDEN = "HID"
    REMOVED = "RMV"


class CommentStatusEnum(str, Enum):
    """
    Enum for comment status values 'published', 'hidden', 'banned', 'removed'
    'flagged_to_be_banned', 'flagged_deleted'
    """

    PUBLISHED = "PUB"
    HIDDEN = "HID"
    BANNED = "BAN"
    REMOVED = "RMV"
    FLAGGED_TO_BE_BANNED = "FLB"
    FLAGGED_DELETED = "FLD"


class CommentLikeStatusEnum(str, Enum):
    """
    Enum for commentlike status values 'active', 'hidden', 'removed'
    """

    ACTIVE = "ACT"
    HIDDEN = "HID"
    REMOVED = "RMV"


class UserFollowAssociationStatusEnum(str, Enum):
    """
    Enum for userfollowassociation status values 'accepted', 'rejected', 'pending', 'unfollowed'
    'removed', 'hidden'
    """

    ACCEPTED = "ACP"
    REJECTED = "REJ"
    PENDING = "PND"
    UNFOLLOWED = "UNF"
    REMOVED = "RMV"
    HIDDEN = "HID"


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


class UserContentReportDetailStatusEnum(str, Enum):
    """
    Enum for usercontentreportdetail status values 'open', 'under_review', 'future_resolved', 'future_resolved_related'
    'closed', 'resolved', 'resolved_related'
    """

    OPEN = "OPN"
    UNDER_REVIEW = "URV"
    FUTURE_RESOLVED = "FRS"
    FUTURE_RESOLVED_RELATED = "FRR"
    CLOSED = "CSD"
    RESOLVED = "RSD"
    RESOLVED_RELATED = "RSR"


class UserContentAppealDetailStatusEnum(str, Enum):
    """
    Enum for usercontentappealdetail status values 'open', 'under_review', 'accepted', 'accepted_related'
    'rejected', 'rejected_related', 'closed'
    """

    OPEN = "OPN"
    UNDER_REVIEW = "URV"
    ACCEPTED = "ACP"
    ACCEPTED_RELATED = "ACR"
    REJECTED = "REJ"
    REJECTED_RELATED = "RJR"
    CLOSED = "CSD"


class UserAccountHistoryEventTypeEnum(str, Enum):
    """
    Enum for useraccounthistory event_type values 'changed', 'removed', 'created', 'deactivated', 'deactivated_delete_scheduled',
    'restricted_partial', 'restricted_full', 'banned_permanent', 'banned_temporary', 'inactivated_delete_scheduled',
    'banned_delete_scheduled', 'deleted', 'reactivated', 'restored', 'unrestricted_partial', 'unrestricted_full'
    'unbanned_temporary', 'unbanned_permanent'
    """

    CHANGED = "CNG"
    REMOVED = "RMV"  # dp/bio removed
    CREATED = "CRT"
    INACTIVATED = "IAV"
    DEACTIVATED = "DAV"
    DEACTIVATED_DELETE_SCHEDULED = "DDS"
    RESTRICTED_PARTIAL = "RSP"
    RESTRICTED_FULL = "RSF"
    BANNED_PERMANENT = "BNP"
    BANNED_TEMPORARY = "BNT"
    INACTIVATED_DELETE_SCHEDULED = "IDS"
    BANNED_DELETE_SCHEDULED = "BDS"
    DELETED = "DEL"
    REACTIVATED = "RAV"
    RESTORED = "RST"
    UNRESTRICTED_PARTIAL = "URP"
    UNRESTRICTED_FULL = "URF"
    UNBANNED_TEMPORARY = "UBT"
    UNBANNED_PERMANENT = "UBP"


class EmployeeStatusEnum(str, Enum):
    """
    Enum for employee status values 'active_regular', 'active_probationary', 'inactive', 'terminated', 'suspended'
    """

    ACTIVE_REGULAR = "ACR"
    ACTIVE_PROBATIONARY = "ACP"
    INACTIVE = "INA"
    TERMINATED = "TER"
    SUSPENDED = "SUP"


class EmployeeTypeEnum(str, Enum):
    """
    Enum for employee type values 'full_time_employee', 'part_time_employee', 'contract_employee'
    """

    FULL_TIME_EMPLOYEE = "FTE"
    PART_TIME_EMPLOYEE = "PTE"
    CONTRACT_EMPLOYEE = "CTE"


class EmployeeAuthTrackStatusEnum(str, Enum):
    """
    Enum for employeeauthtrack status values 'active', 'expired', 'invalid'
    """

    ACTIVE = "ACT"
    EXPIRED = "EXP"
    INVALID = "INV"


class EmployeeDesignationEnum(str, Enum):
    """
    Enum for employee designation values 'chief_executive_officer', 'chief_technology_officer', 'chief_sales_officer',
    'chief_marketing_officer', 'chief_financial_officer', 'chief_operating_officer', 'director_of_human_resource',
    'director_of_products', 'director_of_marketting', 'human_resource_1', 'human_resource_2','human_resource_3',
    'human_resource_manager_1', 'human_resource_manager_2', 'software_development_engineer_1_frontend', 'software_development_engineer_2_frontend',
    'software_development_engineer_3_frontend', 'software_development_engineer_4_frontend', 'software_development_manager_1_frontend',
    'software_development_manager_2_frontend', 'software_development_engineer_1_backend', 'software_development_engineer_2_backend',
    'software_development_engineer_3_backend', 'software_development_engineer_4_backend', 'software_development_manager_1_backend'
    'software_development_manager_2_backend', 'software_development_engineer_test_1', 'software_development_engineer_test_2',
    'software_development_engineer_test_3', 'software_development_engineer_test_4', 'content_community_admin', 'content_moderator',
    'community_moderator', 'user_operations_analyst'
    """

    CHIEF_EXECUTIVE_OFFICER = "CEO"
    CHIEF_TECHNOLOGY_OFFICER = "CTO"
    CHIEF_SALES_OFFICER = "CSO"
    CHIEF_MARKETING_OFFICER = "CMO"
    CHIEF_FINANCIAL_OFFICER = "CFO"
    CHIEF_OPERATING_OFFICER = "COO"
    DIRECTOR_OF_HUMAN_RESOURCE = "DHR"
    DIRECTOR_OF_PRODUCTS = "DOP"
    DIRECTOR_OF_MARKETTING = "DOM"
    HUMAN_RESOURCE_1 = "HR1"
    HUMAN_RESOURCE_2 = "HR2"
    HUMAN_RESOURCE_3 = "HR3"
    HUMAN_RESOURCE_MANAGER_1 = "HRM1"
    HUMAN_RESOURCE_MANAGER_2 = "HRM2"
    SOFTWARE_DEVELOPMENT_ENGINEER_1_FRONTEND = "SDE1F"
    SOFTWARE_DEVELOPMENT_ENGINEER_2_FRONTEND = "SDE2F"
    SOFTWARE_DEVELOPMENT_ENGINEER_3_FRONTEND = "SDE3F"
    SOFTWARE_DEVELOPMENT_ENGINEER_4_FRONTEND = "SDE4F"
    SOFTWARE_DEVELOPMENT_MANAGER_1_FRONTEND = "SDM1F"
    SOFTWARE_DEVELOPMENT_MANAGER_2_FRONTEND = "SDM2F"
    SOFTWARE_DEVELOPMENT_ENGINEER_1_BACKEND = "SDE1B"
    SOFTWARE_DEVELOPMENT_ENGINEER_2_BACKEND = "SDE2B"
    SOFTWARE_DEVELOPMENT_ENGINEER_3_BACKEND = "SDE3B"
    SOFTWARE_DEVELOPMENT_ENGINEER_4_BACKEND = "SDE4B"
    SOFTWARE_DEVELOPMENT_MANAGER_1_BACKEND = "SDM1B"
    SOFTWARE_DEVELOPMENT_MANAGER_2_BACKEND = "SDM2B"
    SOFTWARE_DEVELOPMENT_ENGINEER_TEST_1 = "SDET1"
    SOFTWARE_DEVELOPMENT_ENGINEER_TEST_2 = "SDET2"
    SOFTWARE_DEVELOPMENT_ENGINEER_TEST_3 = "SDET3"
    SOFTWARE_DEVELOPMENT_ENGINEER_TEST_4 = "SDET4"
    CONTENT_COMMUNITY_ADMIN = "CCA"
    CONTENT_MODERATOR = "CNM"
    COMMUNITY_MODERATOR = "CMM"
    USER_OPERATIONS_ANALYST = "UOA"
