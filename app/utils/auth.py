import re
import time
from datetime import datetime, timedelta
from uuid import uuid4

from cachetools import TTLCache, keys
from fastapi import Depends, HTTPException, Request, status
from fastapi.security.oauth2 import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt

from app.config.app import settings
from app.db import session
from app.schemas import auth as auth_schema

ACCESS_TOKEN_SECRET_KEY = settings.access_token_secret_key
REFRESH_TOKEN_SECRET_KEY = settings.refresh_token_secret_key
ALGORITHM = settings.token_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_MINUTES = settings.refresh_token_expire_minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

token_blacklist_cache = TTLCache(maxsize=100, ttl=24 * 60 * 60)


def get_uuid():
    return str(uuid4())


def is_token_blacklisted(token: str):
    cache_key = keys.hashkey(token)
    return cache_key in token_blacklist_cache


def blacklist_token(token: str):
    cache_key = keys.hashkey(token)
    token_blacklist_cache[cache_key] = None


def check_username_or_email(credential: str):
    email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    if re.match(email_pattern, credential):
        return True
    else:
        return False


def get_refresh_token_from_cookie(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found in cookie",
        )
    return refresh_token


def create_access_token(claims: dict):
    access_token_unique_id = get_uuid()
    to_encode = claims.copy()
    expire_time = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire_time, "jti": access_token_unique_id})
    encoded_jwt_at = jwt.encode(to_encode, ACCESS_TOKEN_SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt_at


def create_refresh_token(claims: dict):
    refresh_token_unique_id = get_uuid()
    to_encode = claims.copy()
    expire_time = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire_time, "jti": refresh_token_unique_id})
    encoded_jwt_rt = jwt.encode(
        to_encode, REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM
    )

    return encoded_jwt_rt, refresh_token_unique_id


def verify_access_token(access_token: str):
    # decode the token
    try:
        claims = jwt.decode(
            access_token, ACCESS_TOKEN_SECRET_KEY, algorithms=[ALGORITHM]
        )
        # get the claims
        user_email = claims.get("sub")
        user_type = claims.get("role")
        if not user_email and not user_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials 1",
                headers={"WWW-Authenticate": "Bearer"},
            )
    # if token is expired
    except ExpiredSignatureError as exc:
        blacklist_token(access_token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    # other errors
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    # set the token data and return it
    token_data = auth_schema.AccessTokenPayload(email=user_email, type=user_type)
    return token_data


def verify_refresh_token(refresh_token: str):
    # decode the token but do not verify exp
    try:
        claims = jwt.decode(
            refresh_token,
            REFRESH_TOKEN_SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False},
        )
        # get all claims
        token_id = claims.get("jti")
        user_email = claims.get("sub")
        user_type = claims.get("role")
        token_exp = claims.get("exp")
        user_device_info = claims.get("device_info")

        # check the claims
        if (
            not user_email
            and not user_type
            and not user_device_info
            and not token_id
            and not token_exp
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials 1",
            )
        # set the token data
        token_data = auth_schema.RefreshTokenPayload(
            email=user_email,
            type=user_type,
            device_info=user_device_info,
            token_id=token_id,
        )

        # check the exp, epoch comparision. token_exp is epoch timezone specific. So we use now() for current time
        if token_exp < datetime.now().timestamp():
            # blacklist the token if expired
            blacklist_token(refresh_token)
            # return the token data with false flag
            return (token_data, False)
    # other errors
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc

    # return the token data and true flag if token is successfully verified
    return (token_data, True)


# get the active user, authentication and authorization
def get_current_user(
    access_token: str = Depends(oauth2_scheme),
):
    # check access token in the blacklist
    access_token_blacklist_check = is_token_blacklisted(access_token)
    if access_token_blacklist_check:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied, Token invalid/revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # verify access token
    access_token_data = verify_access_token(access_token)

    return access_token_data
