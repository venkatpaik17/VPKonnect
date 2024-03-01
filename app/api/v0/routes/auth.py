import re
from datetime import timedelta
from typing import Optional

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Request,
    status,
)
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.app import settings
from app.db.session import get_db
from app.models import auth as auth_model
from app.models import employee as employee_model
from app.models import user as user_model
from app.schemas import auth as auth_schema
from app.services import admin as admin_service
from app.services import auth as auth_service
from app.services import employee as employee_service
from app.services import user as user_service
from app.utils import auth as auth_utils
from app.utils import password as password_utils

router = APIRouter(tags=["Authentication"])


# login route
@router.post(settings.api_prefix + "/users/login")
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
    # check if username field is email or username
    is_email = auth_utils.check_username_or_email(credentials.username)

    # get user
    if is_email:
        user_query = user_service.get_user_by_email_query(
            credentials.username, ["DEL"], db
        )
    else:
        user_query = user_service.get_user_by_username_query(
            credentials.username, ["DEL"], db
        )

    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials"
        )

    # verify password
    verify_pass = password_utils.verify_password(credentials.password, user.password)
    if not verify_pass:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials"
        )

    # check and get user restrict/ban entry if any
    restrict_ban_entry = admin_service.get_user_active_restrict_ban_entry(
        user_id=user.id, status_in_list=["RSP", "RSF", "TBN", "PBN"], db_session=db
    )

    try:
        # if account is deactivated then it should be activated by updating status to active
        # but if there is any active retrict or ban i.e. RSP, RSF, TBN and PBN then update the status directly to restrict/ban status
        if user.status in [
            "DAH",
            "DAK",
            "PDH",
            "PDK",
            "INA",
        ]:
            print(user.status)
            if restrict_ban_entry and restrict_ban_entry.status in [
                "RSP",
                "RSF",
                "TBN",
                "PBN",
            ]:
                # user_query.update(
                #     {"status": restrict_ban_entry.status}, synchronize_session=False
                # )
                user.status = restrict_ban_entry.status
            else:
                user_query.update({"status": "ACT"}, synchronize_session=False)

        db.commit()
        # print(user.status)

    except SQLAlchemyError as exc:
        db.rollback()
        # print(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing login request",
        ) from exc

    # check if status is TBN or PBN
    if user.status == "TBN" and (
        restrict_ban_entry and restrict_ban_entry.status == "TBN"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your account has been disabled from {restrict_ban_entry.enforce_action_at} to {restrict_ban_entry.enforce_action_at + timedelta(hours=restrict_ban_entry.duration)}. Please contact support for assistance and submit an appeal if our action is unjustified.",
        )

    if user.status == "PBN" and (
        restrict_ban_entry and restrict_ban_entry.status == "PBN"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your account has been banned permanently from {restrict_ban_entry.enforce_action_at}. Please contact support for assistance and submit an appeal if you think our action is not justified.",
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
        key="refresh_token",
        value=user_refresh_token,
        httponly=True,
        secure=True,
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
        # roll back and blacklist tokens
        db.rollback()
        # auth_utils.blacklist_token(user_access_token)
        auth_utils.blacklist_token(refresh_token_unique_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing login request",
        ) from exc

    return response


# token rotation route for user
@router.post(settings.api_prefix + "/token/users/refresh")
def refresh_token_user(
    refresh_token: str = Cookie(None), db: Session = Depends(get_db)
):
    # check for refresh token in the request
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token required"
        )

    # verify refresh token. We verify first and then check blacklist, since we need jti
    token_claims, token_verify = auth_utils.verify_refresh_token(refresh_token)
    # print(token_verify)

    # check token blacklist using jti
    refresh_token_blacklist_check = auth_utils.is_token_blacklisted(
        token_claims.token_id
    )
    if refresh_token_blacklist_check:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied, Token invalid/revoked",
        )

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
            user = user_service.get_user_by_email(
                str(token_claims.email),
                ["PBN", "DEL"],
                db,
            )
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )
            if user.status in [
                "DAH",
                "DAK",
                "PDH",
                "PDK",
            ]:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found",
                )
            if user.status == "TBN":  # type: ignore
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Unable to process the request",
                )

            add_user_auth_track = auth_model.UserAuthTrack(
                refresh_token_id=refresh_token_unique_id,
                device_info=token_claims.device_info,
                user_id=user.id,
            )

            user_auth_entry = auth_service.get_auth_track_entry_by_token_id_query(
                token_claims.token_id, "ACT", db
            )
            if not user_auth_entry.first():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User auth entry not found",
                )

            db.add(add_user_auth_track)
            user_auth_entry.update(
                {"status": "EXP"},
                synchronize_session=False,
            )

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
        token_claims.token_id, "ACT", db
    )
    if not token_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied, Token invalid/revoked",
        )

    return response


# dummy route to test token rotation
@router.get(settings.api_prefix + "/users/dummy")
def dummy_user(
    user: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="user")
    ),
):
    return {"message": f"checking token rotation {user.email}"}


# logout route, Header() fetches "Authorization" parameter
@router.post(settings.api_prefix + "/users/logout")
def user_logout(
    logout_user: auth_schema.UserLogout,
    refresh_token: str = Cookie(None),
    db: Session = Depends(get_db),
    is_api_call: bool = True,
):
    refresh_token_id = None
    if logout_user.flow == "user":
        # check for refresh token cookie in the request
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token required"
            )

        # identify the user,to check whether user is logging out from his/her own account and not others.
        # get user email from access token
        get_user_claims = auth_utils.decode_token_get_user_token_id(refresh_token)
        if not get_user_claims:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        user_email, refresh_token_id = get_user_claims[0], get_user_claims[1]

        # get user from db using email
        user = user_service.get_user_by_email(
            user_email,
            ["DEL"],
            db,
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User to be logged out not found",
            )

        # check username from request with username from user entry
        if user.username != logout_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to perform requested action",
            )

    elif logout_user.flow == "admin":
        user = user_service.get_user_by_username(logout_user.username, ["DEL"], db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User to be logged out not found",
            )

    if logout_user.action == "one":
        # blacklist the refresh token using token id
        if not refresh_token_id:
            refresh_token_id = (
                auth_service.get_all_user_auth_track_entry_by_user_id_device_info(
                    user.id, logout_user.device_info, "ACT", db
                )
            )
            if not refresh_token_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User auth entry not found",
                )

        auth_utils.blacklist_token(refresh_token_id)

        # fetch the active user session entry query
        user_logout_one_query = user_service.get_user_session_one_entry_query(
            str(user.id), logout_user.device_info, True, db
        )
        user_logout_one = user_logout_one_query.first()
        if not user_logout_one:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User Login/Session entry not found",
            )

        # update is_active in user session entry
        user_logout_one_query.update({"is_active": False}, synchronize_session=False)

        db.commit()

    elif logout_user.action == "all":
        # get all user auth entries based on user id
        user_auth_track_entries = (
            auth_service.get_all_user_auth_track_entries_by_user_id(
                str(user.id), "ACT", db
            )
        )
        if not user_auth_track_entries:
            if is_api_call:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User auth track entries not found",
                )
            else:
                print("User is already logged out")
                return

        # fetch all refresh token ids and blacklist them
        all_refresh_token_ids = [
            item.refresh_token_id for item in user_auth_track_entries
        ]
        for token_id in all_refresh_token_ids:
            auth_utils.blacklist_token(token_id)

        # fetch all active user session entries
        user_logout_all_query = user_service.get_user_session_entries_query_by_user_id(
            str(user.id), True, db
        )
        user_logout_all = user_logout_all_query.all()
        if not user_logout_all:
            if is_api_call:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User Login/Session entries not found",
                )
            else:
                print("Check user session for any issues")
                return

        # update is_active in user session entries
        user_logout_all_query.update({"is_active": False}, synchronize_session=False)

        db.commit()

    response_data = {"message": f"{logout_user.username} successfully logged out"}
    response = JSONResponse(content=response_data)

    # delete refresh token cookie
    response.delete_cookie(key="refresh_token")

    # printing the blacklist cache to check token blacklisting
    for key, value in auth_utils.token_blacklist_cache.items():
        print(f"Key: {key}, Value: {value}")

    return response


# employees APIs
@router.post(settings.api_prefix + "/employees/login")
def employee_login(
    employee_credentials: OAuth2PasswordRequestForm = Depends(),
    employee_device_info: str = Form(),
    db: Session = Depends(get_db),
):
    credentials = auth_schema.EmployeeLogin(
        username=employee_credentials.username,
        password=employee_credentials.password,
        device_info=employee_device_info,
    )

    # check the username whether it is email or emp_id
    is_email = auth_utils.check_username_or_email(credentials.username)

    # check username in the db
    if is_email:
        employee = employee_service.get_employee_by_work_email(credentials.username, db)
    else:
        employee = employee_service.get_employee_by_emp_id(credentials.username, db)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials"
        )

    # verify password
    verify_password = password_utils.verify_password(
        credentials.password, employee.password
    )
    if not verify_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials"
        )

    # set the claims for token generation
    access_token_claims = {"sub": employee.work_email, "role": employee.designation}
    refresh_token_claims = {
        "sub": employee.work_email,
        "role": employee.designation,
        "device_info": employee_device_info,
    }

    # create the tokens
    employee_access_token = auth_utils.create_access_token(access_token_claims)
    employee_refresh_token, refresh_token_unique_id = auth_utils.create_refresh_token(
        refresh_token_claims
    )

    # set the response data
    token_data = auth_schema.AccessToken(
        access_token=employee_access_token, token_type="bearer"
    )

    # encode to JSON, set refresh token cookie
    response = JSONResponse(content=jsonable_encoder(token_data))
    response.set_cookie(
        key="refresh_token",
        value=employee_refresh_token,
        httponly=True,
        secure=True,
    )

    # add login session to employee session table and add an entry to employee auth track to track the refresh token wrt to employee and device
    try:
        add_employee_session = employee_model.EmployeeSession(
            device_info=employee_device_info, employee_id=employee.id
        )
        add_employee_auth_track = auth_model.EmployeeAuthTrack(
            refresh_token_id=refresh_token_unique_id,
            device_info=employee_device_info,
            employee_id=employee.id,
        )
        db.add(add_employee_session)
        db.add(add_employee_auth_track)

        db.commit()

    except SQLAlchemyError as exc:
        # roll back and blacklist tokens
        db.rollback()
        auth_utils.blacklist_token(employee_access_token)
        auth_utils.blacklist_token(refresh_token_unique_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing login request",
        ) from exc

    return response


# token rotation route for employee
@router.post(settings.api_prefix + "/token/employees/refresh")
def refresh_token_employee(
    refresh_token: str = Cookie(None), db: Session = Depends(get_db)
):
    # check for refresh token in the request
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token required"
        )

    # verify refresh token. We verify first and then check blacklist, since we need jti
    token_claims, token_verify = auth_utils.verify_refresh_token(refresh_token)
    # print(token_verify)

    # check token blacklist using jti
    refresh_token_blacklist_check = auth_utils.is_token_blacklisted(
        token_claims.token_id
    )
    if refresh_token_blacklist_check:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied, Token invalid/revoked",
        )
    # print(token_claims.type)
    access_token_claims = {"sub": token_claims.email, "role": token_claims.type}
    refresh_token_claims = {
        "sub": token_claims.email,
        "role": token_claims.type,
        "device_info": token_claims.device_info,
    }

    # create a new access token
    new_employee_access_token = auth_utils.create_access_token(access_token_claims)
    access_token_data = auth_schema.AccessToken(
        access_token=new_employee_access_token, token_type="bearer"
    )
    response = JSONResponse(content=jsonable_encoder(access_token_data))

    # if refresh token is expired, generate new refresh token and set as a httponly secure cookie, add new refresh token entry to employee_auth_track
    # update expired token status
    if not token_verify:
        (
            new_employee_refresh_token,
            refresh_token_unique_id,
        ) = auth_utils.create_refresh_token(refresh_token_claims)
        response.set_cookie(
            key="refresh_token",
            value=new_employee_refresh_token,
            httponly=True,
            secure=True,
        )
        try:
            employee = employee_service.get_employee_by_work_email(
                token_claims.email,
                db,
            )
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
                )

            add_employee_auth_track = auth_model.EmployeeAuthTrack(
                refresh_token_id=refresh_token_unique_id,
                device_info=token_claims.device_info,
                employee_id=employee.id,
            )

            employee_auth_entry = (
                auth_service.get_employee_auth_track_entry_by_token_id_query(
                    token_claims.token_id, "ACT", db
                )
            )
            if not employee_auth_entry.first():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee auth entry not found",
                )

            db.add(add_employee_auth_track)
            employee_auth_entry.update(
                {"status": "EXP"},
                synchronize_session=False,
            )

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
    token_active = auth_service.check_refresh_token_id_in_employee_auth_track(
        token_claims.token_id, "ACT", db
    )
    if not token_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied, Token invalid/revoked",
        )

    return response


# logout route, Header() fetches "Authorization" parameter
@router.post(settings.api_prefix + "/employees/logout")
def employee_logout(
    logout_employee: auth_schema.EmployeeLogout,
    refresh_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    refresh_token_id = None
    # check for refresh token cookie in the request
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token required"
        )

    # identify the employee,to check whether employee is logging out from his/her own account and not others.
    # get employee email from access token
    get_employee_claims = auth_utils.decode_token_get_user_token_id(refresh_token)
    if not get_employee_claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    employee_email, refresh_token_id = get_employee_claims[0], get_employee_claims[1]

    # get employee from db using email
    employee = employee_service.get_employee_by_work_email(
        employee_email,
        db,
    )
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )

    # check username from request with username from user entry
    if employee.emp_id != logout_employee.emp_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    if logout_employee.action == "one":
        # blacklist refresh token using token id
        auth_utils.blacklist_token(refresh_token_id)

        # fetch the active user session entry query
        employee_logout_one_query = (
            employee_service.get_employee_session_one_entry_query(
                str(employee.id), logout_employee.device_info, True, db
            )
        )
        employee_logout_one = employee_logout_one_query.first()
        if not employee_logout_one:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee Login/Session entry not found",
            )

        # update is_active in user session entry
        employee_logout_one_query.update(
            {"is_active": False}, synchronize_session=False
        )

        db.commit()

    elif logout_employee.action == "all":
        # get all user auth entries based on user id
        employee_auth_track_entries = (
            auth_service.get_all_employee_auth_track_entries_by_employee_id(
                str(employee.id), "ACT", db
            )
        )
        if not employee_auth_track_entries:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee auth track entries not found",
            )

        # fetch all refresh token ids and blacklist them
        all_refresh_token_ids = [
            item.refresh_token_id for item in employee_auth_track_entries
        ]
        for token_id in all_refresh_token_ids:
            auth_utils.blacklist_token(token_id)

        # fetch all active employee session entries
        employee_logout_all_query = (
            employee_service.get_employee_session_entries_query_by_employee_id(
                str(employee.id), True, db
            )
        )
        if not employee_logout_all_query.all():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee Login/Session entries not found",
            )

        # update is_active in user session entries
        employee_logout_all_query.update(
            {"is_active": False}, synchronize_session=False
        )

        db.commit()

    response_data = {"message": f"{logout_employee.emp_id} successfully logged out"}
    response = JSONResponse(content=response_data)

    # delete refresh token cookie
    response.delete_cookie(key="refresh_token")

    # printing the blacklist cache to check token blacklisting
    for key, value in auth_utils.token_blacklist_cache.items():
        print(f"Key: {key}, Value: {value}")

    return response


# dummy route to test token rotation
@router.get(settings.api_prefix + "/employees/dummy")
def dummy_emp(
    employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="employee")
    ),
):
    return {"message": f"checking token rotation {employee.email}"}
