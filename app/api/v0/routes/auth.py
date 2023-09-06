from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import auth as auth_model
from app.models import user as user_model
from app.schemas import auth as auth_schema
from app.services import auth as auth_service
from app.services import user as user_service
from app.utils import auth as auth_utils
from app.utils import password as password_utils

router = APIRouter(tags=["Authentication"])


# login route
@router.post("/users/login")
def user_login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    user_device_info: str = Form(),
    db: Session = Depends(get_db),
):
    # check for user in the database
    credentials = auth_schema.UserLogin(
        username=user_credentials.username,
        password=user_credentials.password,
        device_info=user_device_info,
    )
    is_email = auth_utils.check_username_or_email(credentials.username)
    # check if username field is email or username
    if is_email:
        user = user_service.get_user_by_email(credentials.username, db)
    else:
        user = user_service.get_user_by_username(credentials.username, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials"
        )

    verify_pass = password_utils.verify_password(credentials.password, user.password)
    if not verify_pass:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials"
        )

    # set the claims for token generation
    access_token_claims = {"sub": user.email, "role": user.type}
    refresh_token_claims = {
        "sub": user.email,
        "role": user.type,
        "device_info": user_device_info,
    }

    # create the tokens
    user_access_token = auth_utils.create_access_token(access_token_claims)
    user_refresh_token, refresh_token_unique_id = auth_utils.create_refresh_token(
        refresh_token_claims
    )

    # set the response data
    token_data = auth_schema.AccessToken(
        access_token=user_access_token, token_type="bearer"
    )

    # encode to JSON, set refresh token cookie
    response = JSONResponse(content=jsonable_encoder(token_data))
    response.set_cookie(
        key="refresh_token", value=user_refresh_token, httponly=True, secure=True
    )
    # print(user_device_info)

    # add login session to user session table and add an entry to user auth track to track the refresh token wrt to user and device
    try:
        add_user_session = user_model.UserSession(
            device_info=user_device_info, user_id=user.id
        )
        add_user_auth_track = auth_model.UserAuthTrack(
            refresh_token_id=refresh_token_unique_id,
            device_info=user_device_info,
            user_id=user.id,
        )
        db.add(add_user_session)
        db.add(add_user_auth_track)

        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing login request",
        ) from exc

    return response


# token rotation route
@router.post("/token/refresh")
def refresh_token(refresh_token: str = Cookie(), db: Session = Depends(get_db)):
    # check token blacklist
    refresh_token_blacklist_check = auth_utils.is_token_blacklisted(refresh_token)
    if refresh_token_blacklist_check:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied, Token invalid/revoked",
        )

    # verify refresh token
    token_claims, token_verify = auth_utils.verify_refresh_token(refresh_token)
    print(token_verify)
    access_token_claims = {"sub": token_claims.email, "role": token_claims.type}
    refresh_token_claims = {
        "sub": token_claims.email,
        "role": token_claims.type,
        "device_info": token_claims.device_info,
    }

    # create a new access token
    new_user_access_token = auth_utils.create_access_token(access_token_claims)
    access_token_data = auth_schema.AccessToken(
        access_token=new_user_access_token, token_type="bearer"
    )
    response = JSONResponse(content=jsonable_encoder(access_token_data))

    # if refresh token is expired, generate new refresh token and set as a httponly secure cookie, add new refresh token entry to user_auth_track
    # update expired token status
    if not token_verify:
        (
            new_user_refresh_token,
            refresh_token_unique_id,
        ) = auth_utils.create_refresh_token(refresh_token_claims)
        response.set_cookie(
            key="refresh_token",
            value=new_user_refresh_token,
            httponly=True,
            secure=True,
        )
        try:
            user = user_service.get_user_by_email(token_claims.email, db)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )
            add_user_auth_track = auth_model.UserAuthTrack(
                refresh_token_id=refresh_token_unique_id,
                device_info=token_claims.device_info,
                user_id=user.id,
            )

            user_auth_entry = auth_service.get_auth_track_entry_by_token_id_query(
                token_claims.token_id, db
            )
            if not user_auth_entry.first():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User auth entry not found",
                )

            db.add(add_user_auth_track)
            user_auth_entry.update({"status": "expired"}, synchronize_session=False)

            db.commit()

            return response
        except HTTPException as exc:
            raise exc
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing auth",
            ) from exc

    # check refresh token status
    token_active = auth_service.check_refresh_token_id_in_user_auth_track(
        token_claims.token_id, db
    )
    if not token_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied, Token invalid/revoked",
        )

    return response


# dummy route to test token rotation
@router.get("/users/dummy")
def dummy(user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user)):
    return {"message": f"checking token rotation {user.email}"}
