import re
from datetime import datetime, timedelta
from uuid import uuid4

from jose import JWTError, jwt

from app.config.app import settings

ACCESS_TOKEN_SECRET_KEY = settings.access_token_secret_key
REFRESH_TOKEN_SECRET_KEY = settings.refresh_token_secret_key
ALGORITHM = settings.token_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKE_EXPIRE_MINUTES = settings.access_token_expire_minutes

ACCESS_TOKEN_UNIQUE_ID = str(uuid4())
REFRESH_TOKEN_UNIQUE_ID = str(uuid4())


def check_username_or_email(credential: str):
    email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    if re.match(email_pattern, credential):
        return True
    else:
        return False


def create_access_token(claims: dict):
    to_encode = claims.copy()
    expire_time = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire_time, "jti": ACCESS_TOKEN_UNIQUE_ID})
    encoded_jwt_at = jwt.encode(to_encode, ACCESS_TOKEN_SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt_at


def create_refresh_token(claims: dict):
    to_encode = claims.copy()
    expire_time = datetime.utcnow() + timedelta(minutes=REFRESH_TOKE_EXPIRE_MINUTES)
    to_encode.update({"exp": expire_time, "jti": REFRESH_TOKEN_UNIQUE_ID})
    encoded_jwt_rt = jwt.encode(
        to_encode, REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM
    )

    return encoded_jwt_rt
