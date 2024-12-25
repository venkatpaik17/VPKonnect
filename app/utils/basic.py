import base64
from datetime import datetime

import ulid


# function to get time ago for content
def time_ago(post_datetime: datetime):
    current_datetime = datetime.now().astimezone()
    difference = current_datetime - post_datetime
    seconds = difference.total_seconds()

    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m"
    elif seconds < 86400:
        return f"{int(seconds // 3600)}h"
    elif seconds < 604800:
        return f"{int(seconds // 86400)}d"
    else:
        return f"{int(seconds // 604800)}w"


# function to generate ulid and return as uuid (used ulid-py package)
def get_ulid():
    return ulid.new().uuid


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:  # type: ignore
        return base64.b64encode(image_file.read()).decode("utf-8")


# adjust violation scores for manual report action
def adjust_violation_scores(
    curr_final_violation_score: int,
    min_req_violation_score: int,
    curr_score: int,
):
    diff = False

    if curr_final_violation_score < min_req_violation_score:
        new_final_violation_score = min_req_violation_score
        difference_score = min_req_violation_score - curr_final_violation_score
        new_content_score = curr_score + difference_score
        new_last_added_score = difference_score
        diff = True
    else:
        new_final_violation_score = curr_final_violation_score
        new_content_score = curr_score
        new_last_added_score = 0

    return new_final_violation_score, new_content_score, new_last_added_score, diff
