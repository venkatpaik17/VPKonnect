# define dictionaries for search and map

from fastapi import HTTPException, status

report_reasons_code_dict = {
    "IDONTLIKE": "I just don't like it",
    "ITSSPAM": "It's spam",
    "EXCSVPROM": "Excessive promotion",
    "SELLPETANI": "Selling pets/animals",
    "IPVIOLN": "Intellectual property violation",
    "SCAMFRAUD": "Scam or fraud",
    "VIOLTHRT": "Violent Threat",
    "VIODANORG": "Violence or dangerous organisations",
    "BULLYHRSMT": "Bullying or Harrassment",
    "SILRG-DAT": "Sale of illegal or regulated goods - Selling drugs, alcohol or tobacco",
    "SILRG-FA": "Sale of illegal or regulated goods - Selling firearms",
    "SILRG-FHD": "Sale of illegal or regulated goods - Fake health documents",
    "SILRG-WLDT": "Sale of illegal or regulated goods - Wildlife trade (endangered/protected species)",
    "ANIABUSE": "Animal Abuse",
    "HATESPHSYM": "Hate speech or symbols",
    "FALINF-HL": "False Information - Health",
    "FALINF-PLT": "False Information - Politics",
    "FALINF-SOC": "False Information - Social Issue",
    "FALINF-SE": "False Information - Something else",
    "PVTIMGTHRT": "Threatening to share private images",
    "NUDSXAC-CH": "Nudity or sexual activity - Child",
    "NUDSXAC-AD": "Nudity or sexual activity - Adult",
    "SUIINJETD": "Suicide or self-injury or eating diorders",
    "PRBNOTLIST": "The problem isn't listed",
    "ACCNTHACK": "Account may have been hacked",
    "PRTND-ME": "They are pretending to be someone else - Me",
    "PRTND-SIF": "They are pretending to be someone else - Someone I follow",
    "PRTND-CBPF": "They are pretending to be someone else - Celebrity or Public figure",
    "PRTND-BUSS": "They are pretending to be someone else - Business or Organisation",
}


report_reasons_severity_group_dict = {
    "IDONTLIKE": "MN",
    "ITSSPAM": "MD",
    "EXCSVPROM": "MD",
    "SELLPETANI": "MS",
    "IPVIOLN": "MS",
    "SCAMFRAUD": "MS",
    "VIOLTHRT": "SV",
    "VIODANORG": "SV",
    "BULLYHRSMT": "SV",
    "SILRG-DAT": "SV",
    "SILRG-FA": "SV",
    "SILRG-FHD": "SV",
    "SILRG-WLDT": "SV",
    "ANIABUSE": "SV",
    "HATESPHSYM": "SV",
    "FALINF-HL": "SN",
    "FALINF-PLT": "SN",
    "FALINF-SOC": "SN",
    "FALINF-SE": "SN",
    "PVTIMGTHRT": "SN",
    "NUDSXAC-CH": "SN",
    "NUDSXAC-AD": "SN",
    "SUIINJETD": "HS",
    "PRBNOTLIST": "MN",
    "ACCNTHACK": "SV",
    "PRTND-ME": "CMD",
    "PRTND-SIF": "CMD",
    "PRTND-CBPF": "CMD",
    "PRTND-BUSS": "CMD",  # CMD means Content Moderator Decision
}

severity_groups_scores_dict = {
    "SV": 375,
    "HS": 325,
    "SN": 300,
    "MS": 175,
    "MD": 75,
    "MN": 1,
}

content_weigths_dict = {
    "post": 0.5,
    "comment": 0.35,
    "message": 0.15,
}


def get_action_duration_final_violation_score(violation_score: int):
    match violation_score:
        case score if 0 <= score < 150:
            return ("NA", 0)
        case score if 150 <= score < 250:
            return ("RSP", 24)
        case score if 250 <= score < 300:
            return ("RSP", 72)
        case score if 300 <= score < 350:
            return ("RSP", 168)
        case score if 350 <= score < 400:
            return ("RSF", 24)
        case score if 400 <= score < 500:
            return ("RSF", 72)
        case score if 500 <= score < 600:
            return ("RSF", 168)
        case score if 600 <= score < 650:
            return ("TBN", 72)
        case score if 650 <= score < 750:
            return ("TBN", 168)
        case score if 750 <= score < 850:
            return ("TBN", 504)
        case score if score >= 850:
            return ("PBN", 99999)
        case _:
            return ("UND", -1)


def create_violation_moderator_notes(
    username: str,
    moderator_note: str,
    case_number: int,
    content_type: str,
    report_reason: str,
):
    violation_moderator_notes_dict = {
        "RS": {
            "message": f"We have reviewed {username}'s {content_type} and found that it goes against our Community Guidelines",
            "detail": f"""Case number: {case_number} 
            To keep our review process as fair as possible, we use the same set of Community Guidelines to review all reports.
            We've found that this {content_type} does go against our Community Guidelines on {report_reason}.
            We've let {username} know that their {content_type} has been removed, but not who reported it. 
            Report like yours are an important part of making VPKonnect a safe and welcoming place for everyone.""",
        },
        "RF": {
            "message": f"We have reviewed {username}'s {content_type} and found that it doesn't go against our Community Guidelines",
            "detail": f"""Case number: {case_number}
            To keep our review process as fair as possible, we use the same set of Community Guidelines to review all reports.
            We've found that this {content_type} doesn't go against our Community Guidelines on {report_reason}.
            We understand that this might be upsetting. If you want to see less of {username} on VPKonnect, you can unfollow them.""",
        },
        "RNB": {
            "message": f"We have reviewed {username}'s {content_type}, but it appears that the {content_type} has already been reviewed and banned.",
            "detail": f"""Case number: {case_number}
            The {content_type} in review has been found to violate our Community Guidelines as a result of a previous report review.
            Your vigilance is appreciated, and while your report may not have directly led to this action, we thank you for your commitment to making VPKonnect a safe and welcoming platform for all.""",
        },
        "RNF": {
            "message": f"We have reviewed {username}'s {content_type}, but it appears that the {content_type} has already been reviewed and flagged to be banned in future.",
            "detail": f"""Case number: {case_number}
            The {content_type} in review has been found to violate our Community Guidelines as a result of a previous report review.
            Your vigilance is appreciated, and while your report may not have directly led to this action, we thank you for your commitment to making VPKonnect a safe and welcoming platform for all.""",
        },
        "RND": {
            "message": f"We have reviewed {username}'s {content_type}, but it appears that the {content_type} could not be found.",
            "detail": f"""Case number: {case_number}
            Upon investigation, it appears that the {content_type} in review has either been deleted or is no longer accessible.
            Your vigilance is appreciated, and while we were unable to directly assess the reported content, we thank you for your commitment to making VPKonnect a safe and welcoming platform for all.""",
        },
        "RNU": {
            "message": f"We could not review {username}'s {content_type} because the {username}'s account could not be found.",
            "detail": f"""Case number: {case_number}
            Upon investigation, it appears that the {username}'s account is either deleted or is no longer accessible.
            Your vigilance is appreciated, and while we were unable to review this report, we thank you for your commitment to making VPKonnect a safe and welcoming platform for all.""",
        },
        "SE": {
            "message": "We encountered a system error while processing the report.",
            "detail": f"""Case number: {case_number}
            Unfortunately, a system error occurred while attempting to process the report for {username}'s {content_type}. 
            As a result, we are unable to complete the review at this time. 
            Our technical team has been notified and will work to resolve the issue. 
            We appreciate your patience and understanding as we work to fix this problem. Please try submitting the report again later.
            We apologize for any inconvenience.""",
        },  # system error
        "UD": {
            "message": f"Report closed due to {username} account deletion after inactivity",
            "detail": f"""Case number: {case_number}
            User inactivity time surpassed duration set by {username}. So this report submmited by user is hence closed.
            """,
        },
    }

    return violation_moderator_notes_dict.get(moderator_note)


action_entry_score_dict: dict[tuple[str, int], int] = {
    ("RSP", 24): 150,
    ("RSP", 72): 250,
    ("RSP", 168): 300,
    ("RSF", 24): 350,
    ("RSF", 72): 400,
    ("RSF", 168): 500,
    ("TBN", 72): 600,
    ("TBN", 168): 650,
    ("TBN", 504): 750,
    ("PBN", 99999): 850,
}


def create_appeal_moderator_notes(
    username: str, moderator_note: str, case_number: int, content_type: str
):
    appeal_moderator_notes_dict = {
        "AF1": {
            "message": f"We have reviewed the appeal for {username}'s account, but it cannot be processed due to the rejection of a related post appeal in the past.",
            "detail": f"""Case number: {case_number}
            The appeal to revoke the restriction/ban on {username}'s account was rejected because an earlier appeal to revoke ban on one of the posts associated with this account restriction/ban was already reviewed and rejected. 
            We understand that this might be upsetting and apologize for any inconvenience. Thank you for your understanding.
            Please refer to our Appeal Policy for more details.""",
        },
        "AF2": {
            "message": f"We have reviewed the appeal for {username}'s account, but it cannot be processed due to the rejection of a related {content_type} appeal in the past.",
            "detail": f"""Case number: {case_number}
            The appeal to revoke the restriction on {username}'s account was rejected because an earlier appeal to revoke ban on the {content_type} associated with this account restriction/ban was already reviewed and rejected. 
            We understand that this might be upsetting and apologize for any inconvenience. Thank you for your understanding.
            Please refer to our Appeal Policy for more details.""",
        },
        "AF3": {
            "message": f"We have reviewed the appeal for {username}'s post, but it cannot be processed due to the rejection of related account restriction appeal.",
            "detail": f"""Case number: {case_number}
            The appeal to revoke the ban on post was rejected because an earlier appeal to revoke restriction on {username}'s account involving this post ban was already reviewed and rejected. 
            We understand that this might be upsetting and apologize for any inconvenience. Thank you for your understanding.
            Please refer to our Appeal Policy for more details.""",
        },
        "AF4": {
            "message": f"We have reviewed the appeal for {username}'s {content_type}, but it cannot be processed due to the rejection of related account restriction/ban appeal.",
            "detail": f"""Case number: {case_number}
            The appeal to revoke the ban on {content_type} was rejected because an earlier appeal to revoke the restriction/ban on {username}'s account, involving this {content_type} was already reviewed and rejected. 
            We understand that this might be upsetting and apologize for any inconvenience. Thank you for your understanding.
            Please refer to our Appeal Policy for more details.""",
        },
        "AF0": {
            "message": f"We have reviewed the appeal for {username}'s {content_type}, but the restriction/ban associated with it was confirmed as fair.",
            "detail": f"""Case number: {case_number}
            To keep our review process as fair as possible, we use the same set of Community Guidelines to review all appeals.
            The appeal was rejected after a thorough review, and we have confirmed that the restriction/ban on the associated {content_type} was applied correctly. 
            We understand that this might be upsetting and apologize for any inconvenience. Thank you for your understanding.""",
        },
        "ANU": {
            "message": f"We could not process the appeal for {username}'s {content_type} because the account could not be found.",
            "detail": f"""Case number: {case_number}
            We could not locate the user account associated with this appeal. This may be due to account deletion or inaccessibility. 
            Hence we could not review this appeal.""",
        },  # appeal no action user not found
        "ANPC": {
            "message": f"We could not process the appeal for {username}'s {content_type} because{content_type} could not be found.",
            "detail": f"""Case number: {case_number}
            Upon investigation, it appears that the post/comment in question has either been deleted or is no longer accessible.
            Since we could not access the post/comment, we were unable to review you appeal.""",
        },  # appeal no action post/comment
        "AE": {
            "message": "The appeal has expired due to inaction within the appeal process timeframe.",
            "detail": f"""Case number: {case_number}
            The appeal for {username}'s {content_type} has expired because the required actions were not taken within the designated timeframe. 
            As a result, the appeal can no longer be reviewed or processed.
            Please refer to our Appeal Policy for information on the appeal process and timeframes for future reference. 
            We are committed to resolving these issues and appreciate your patience during this process""",
        },  # appeal expired
        "SE": {
            "message": "We encountered a system error while processing the appeal.",
            "detail": f"""Case number: {case_number}
            Unfortunately, a system error occurred while attempting to process the appeal for {username}'s {content_type}. 
            As a result, we are unable to complete the review at this time. 
            Our technical team has been notified and will work to resolve the issue. 
            We appreciate your patience and understanding as we work to fix this problem. Please try submitting the appeal again later.
            We apologize for any inconvenience.""",
        },  # system error
        "AS": {
            "message": f"The appeal for {username}'s {content_type} has been accepted.",
            "detail": f"""Case number: {case_number}
            We are pleased to inform you that your appeal has been reviewed and accepted. The restriction/ban on {username}'s {content_type} has been revoked accordingly.
            Thank you for your patience and understanding. 
            Please refer to our Appeal Policy for further details on what this decision entails and any next steps that may be required.
            If you have any further questions or concerns, feel free to reach out to our support team.""",
        },
    }

    return appeal_moderator_notes_dict.get(moderator_note)


def transform_status(value: str):
    status_map = {
        "open": ["OPN"],
        "closed": ["CSD"],
        "review": ["URV"],
        "resolved": ["RSD", "RSR"],
        "future_resolved": ["FRS", "FRR"],
        "accepted": ["ACP", "ACR"],
        "rejected": ["REJ", "RJR"],
        "active": "ACT",
        "inactive": "INA",
        "partial_restrict": "RSP",
        "full_restrict": "RSF",
        "deactivated": "DAH",
        "pending_delete": "PDH",
        "temp_ban": "TBN",
        "perm_ban": "PBN",
        "pending_delete_ban": "PDB",
        "pending_delete_inactive": "PDI",
        "deleted": "DEL",
        "active_regular": "ACR",
        "active_probationary": "ACP",
        "inactive_emp": "INA",
        "terminated": "TER",
        "suspended": "SUP",
        "published": "PUB",
        "draft": "DRF",
        "banned": "BAN",
        "flagged_banned": "FLB",
    }

    if value in status_map:
        return status_map[value]
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid status in request: {value}",
    )


def transform_type(value: str):
    type_map = {
        "full_time": "FTE",
        "part_time": "PTE",
        "contract": "CTE",
    }

    if value in type_map:
        return type_map[value]
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid type in request: {value}",
    )


def transform_access_role(value: str):
    # access_roles dict
    access_roles = {
        "management": [
            "CEO",
            "CTO",
            "CMO",
            "CSO",
            "CFO",
            "COO",
            "DHR",
            "DOP",
            "DOM",
        ],
        "software_dev": [
            "SDE1F",
            "SDE2F",
            "SDE3F",
            "SDE4F",
            "SDE1B",
            "SDE2B",
            "SDE3B",
            "SDE4B",
            "SDET1",
            "SDET2",
            "SDET3",
            "SDET4",
            "SDM1F",
            "SDM2F",
            "SDM1B",
            "SDM2B",
        ],
        "hr": ["HR1", "HR2", "HR3", "HRM1", "HRM2"],
        "content_admin": ["CCA"],
        "content_mgmt": ["CNM", "CMM", "UOA"],
        "busn_govt_user": ["BUS", "GOV"],
        "std_ver_user": ["STD", "VER"],
        "user": ["STD", "VER", "BUS", "GOV"],
        "employee": [
            "CEO",
            "CTO",
            "CMO",
            "CSO",
            "CFO",
            "COO",
            "SDE1F",
            "SDE2F",
            "SDE3F",
            "SDE4F",
            "SDE1B",
            "SDE2B",
            "SDE3B",
            "SDE4B",
            "SDET1",
            "SDET2",
            "SDET3",
            "SDET4",
            "SDM1F",
            "SDM2F",
            "SDM1B",
            "SDM2B",
            "CCA",
            "CNM",
            "CMM",
            "UOA",
            "HR1",
            "HR2",
            "HR3",
            "HRM1",
            "HRM2",
            "DHR",
            "DOP",
            "DOM",
        ],
    }

    if value in access_roles:
        return access_roles[value]
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Role configuration is invalid",
    )
