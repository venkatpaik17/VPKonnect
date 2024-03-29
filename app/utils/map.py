# define dictionaries for search and map

from math import inf

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
    "PRTND-BUSS": "CMD",
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
            return ("NA", None)
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
            return ("TBN", 74)
        case score if 650 <= score < 750:
            return ("TBN", 168)
        case score if 750 <= score < 850:
            return ("TBN", 504)
        case score if score >= 850:
            return ("PBN", inf)
        case _:
            return (None, None)


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
            "detail": f"Case number: {case_number}\n To keep our review process as fair as possible,\
                        we use the same set of Community Guidelines to review all reports.\n\
                        We've found that this {content_type} does go against our Community Guidelines on {report_reason}.\n\
                        We've let {username} know that their {content_type} has been removed, but not who reported it.\n\
                        Report like yours are an important part of making VPKonnect a safe and welcoming place for everyone.",
        },
        "RF": {
            "message": f"We have reviewed {username}'s {content_type} and found that it doesn't go against our Community Guidelines",
            "detail": f"Case number: {case_number}\n To keep our review process as fair as possible,\
                        we use the same set of Community Guidelines to review all reports.\n\
                        We've found that this {content_type} doesn't go against our Community Guidelines on {report_reason}.\n\
                        We understand that this might be upsetting.\n If you want to see less of {username} on VPKonnect, you can unfollow them.",
        },
    }

    return violation_moderator_notes_dict.get(moderator_note)


action_entry_score_dict = {
    ("RSP", 24): 150,
    ("RSP", 72): 250,
    ("RSP", 168): 300,
    ("RSF", 24): 350,
    ("RSF", 72): 400,
    ("RSF", 168): 500,
    ("TBN", 24): 600,
    ("TBN", 72): 650,
    ("TBN", 168): 750,
    ("PBN", 99999): 850,
}
