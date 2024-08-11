import base64
from datetime import datetime

import ulid


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
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
