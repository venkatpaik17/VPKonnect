import json
import logging
from http import HTTPStatus

from fastapi import Request, Response
from typing_extensions import override

logger = logging.getLogger("my_app")
status_reasons = {x.value: x.name for x in list(HTTPStatus)}


def get_logger():
    return logger


def get_extra_info(request: Request, response: Response):
    return {
        "req": {
            "url": request.url.path,
            "headers": {
                "host": request.headers["host"],
                "user-agent": request.headers["user-agent"],
                "accept": request.headers["accept"],
            },
            "method": request.method,
            "httpVersion": request.scope["http_version"],
            "originalUrl": request.url.path,
            "query": dict(request.query_params),
        },
        "res": {
            "statusCode": response.status_code,
            "body": {
                "statusCode": response.status_code,
                "status": status_reasons.get(response.status_code),
            },
        },
    }


def write_log_data(request, response):
    logger.info(
        request.method + " " + request.url.path,
        extra={"extra_info": get_extra_info(request, response)},
    )


def get_app_log(record):
    json_obj = {
        "logRecord": {
            "log": {
                "level": record.levelname,
                "type": "app",
                "timestamp": record.asctime,
                #'filename': record.filename,
                "pathname": record.pathname,
                "line": record.lineno,
                "threadId": record.thread,
                "message": record.message,
            }
        }
    }

    return json_obj


def get_access_log(record):
    json_obj = {
        "logRecord": {
            "log": {
                "level": record.levelname,
                "type": "access",
                "timestamp": record.asctime,
                "message": record.message,
                "exception": record.exc_info if record.exc_info else None,
            },
            "req": record.extra_info["req"],
            "res": record.extra_info["res"],
        }
    }

    return json_obj


class CustomFormatter(logging.Formatter):
    def __init__(self):
        super().__init__("%(asctime)s", datefmt="%Y-%m-%dT%H:%M:%S%z")

    @override
    def format(self, record):
        super().format(record)
        if not hasattr(record, "extra_info"):
            return json.dumps(get_app_log(record))
        else:
            return json.dumps(get_access_log(record))
