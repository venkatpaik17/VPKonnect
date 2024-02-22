import re
from datetime import datetime, timedelta
from typing import Any
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
RESET_TOKEN_SECRET_KEY = settings.reset_token_secret_key
RESET_TOKEN_EXPIRE_MINUTES = settings.reset_token_expire_minutes
USER_VERIFY_TOKEN_SECRET_KEY = settings.user_verify_token_secret_key
USER_VERIFY_TOKEN_EXPIRE_MINUTES = settings.user_verify_token_expire_minutes

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


# password reset token
def create_reset_token(claims: dict):
    reset_token_unique_id = get_uuid()
    to_encode = claims.copy()
    expire_time = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire_time, "jti": reset_token_unique_id})
    encoded_jwt_rt = jwt.encode(to_encode, RESET_TOKEN_SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt_rt, reset_token_unique_id


def create_user_verify_token(claims: dict):
    user_verify_token_unique_id = get_uuid()
    to_encode = claims.copy()
    expire_time = datetime.utcnow() + timedelta(
        minutes=USER_VERIFY_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire_time, "jti": user_verify_token_unique_id})
    encoded_jwt_uvt = jwt.encode(
        to_encode, USER_VERIFY_TOKEN_SECRET_KEY, algorithm=ALGORITHM
    )

    return encoded_jwt_uvt, user_verify_token_unique_id


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


def decode_token_get_user(token: str):
    claims = jwt.decode(
        token,
        ACCESS_TOKEN_SECRET_KEY,
        algorithms=[ALGORITHM],
        options={"verify_exp": False},
    )
    user_email = claims.get("sub")
    return user_email if user_email else False


def decode_token_get_token_id(token: str):
    claims = jwt.decode(
        token,
        REFRESH_TOKEN_SECRET_KEY,
        algorithms=[ALGORITHM],
        options={"verify_exp": False},
    )
    token_id = claims.get("jti")
    return token_id if token_id else False


def verify_reset_token(token: str):
    try:
        claims = jwt.decode(
            token,
            RESET_TOKEN_SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False},
        )
        user_email = claims.get("sub")
        token_id = claims.get("jti")
        token_exp = claims.get("exp")
        if not user_email and not token_id and not token_exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password reset failed, Reset token invalid",
            )

        # set token payload object
        token_data = auth_schema.ResetTokenPayload(email=user_email, token_id=token_id)

        # check token expiry
        if token_exp < datetime.now().timestamp():
            # blacklist the token if expired
            blacklist_token(token_data.token_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password reset failed, Reset token expired",
            )
    except HTTPException as exc:
        raise exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc

    return token_data


def verify_user_verify_token(token: str):
    try:
        claims = jwt.decode(
            token,
            USER_VERIFY_TOKEN_SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False},
        )
        user_email = claims.get("sub")
        token_id = claims.get("jti")
        token_exp = claims.get("exp")
        if not user_email and not token_id and not token_exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User verification failed, Verify token invalid",
            )

        # set token payload object
        token_data = auth_schema.UserVerifyTokenPayload(
            email=user_email, token_id=token_id
        )  # type: ignore

        # check token expiry
        if token_exp < datetime.now().timestamp():
            # blacklist the token if expired
            blacklist_token(token_data.token_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User verification failed, Verify token expired",
            )
    except HTTPException as exc:
        raise exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc

    return token_data


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
                detail="Could not validate credentials",
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
                detail="Could not validate credentials",
            )
        # set the token data
        token_data = auth_schema.RefreshTokenPayload(
            email=user_email,
            type=user_type,
            device_info=user_device_info,
            token_id=token_id,
        )

        print(token_exp)
        print(datetime.now().timestamp())
        # check the exp, epoch comparision. token_exp is epoch timezone specific. So we use now() for current time
        if token_exp < datetime.now().timestamp():
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


# access_roles dict
access_roles = {
    "management": ["CEO", "CTO", "CMO", "CSO", "CFO", "COO"],
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
        "CNM",
        "CMM",
        "UOA",
    ],
}


# custom dependency to handle access roles
class AccessRoleDependency:
    def __init__(self, role: str):
        self.role = role

    def __call__(
        self, current_user: auth_schema.AccessTokenPayload = Depends(get_current_user)
    ):
        type_desgn = current_user.type
        if type_desgn not in access_roles[self.role]:
            print("1")
            print(type_desgn)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to perform requested action",
            )

        return current_user


# def get_current_admin(access_token: str = Depends(oauth2_scheme)):
#     access_token_data = get_current_user(access_token)
#     if access_token_data.type != "ADM":
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Could not validate credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     return access_token_data


# # check the role to grant access
# can't use this because it is not possible to send params through Depends
# def check_access_role(
#     role: str, current_user: auth_schema.AccessTokenPayload = Depends(get_current_user)
# ):
#     type_desgn = current_user.type
#     if type_desgn not in access_roles[role]:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not authorized to perform requested action",
#         )

#     return current_user
