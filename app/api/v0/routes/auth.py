from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import auth as auth_model
from app.models import user as user_model
from app.schemas import auth as auth_schema
from app.services import user as user_service
from app.utils import auth as auth_utils
from app.utils import password as password_utils

router = APIRouter(tags=["Authentication"])


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

    claims = {"sub": user.email, "role": user.type}
    user_access_token = auth_utils.create_access_token(claims)
    user_refresh_token = auth_utils.create_refresh_token(claims)

    token_data = auth_schema.AccessToken(
        access_token=user_access_token, token_type="bearer"
    )

    response = JSONResponse(content=jsonable_encoder(token_data))
    response.set_cookie(
        key="refresh_token", value=user_refresh_token, httponly=True, secure=True
    )
    # print(user_device_info)

    try:
        add_user_session = user_model.UserSession(
            device_info=user_device_info, user_id=user.id
        )
        add_user_auth_track = auth_model.UserAuthTrack(
            refresh_token_id=auth_utils.REFRESH_TOKEN_UNIQUE_ID,
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
