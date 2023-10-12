import shutil
from datetime import datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from PIL import Image, UnidentifiedImageError
from pyfa_converter import FormDepends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.app import settings
from app.db.session import get_db
from app.models import auth as auth_model
from app.models import user as user_model
from app.schemas import admin as admin_schema
from app.schemas import auth as auth_schema
from app.schemas import user as user_schema
from app.services import auth as auth_service
from app.services import user as user_service
from app.utils import auth as auth_utils
from app.utils import email as email_utils
from app.utils import enum as enum_utils
from app.utils import image as image_utils
from app.utils import password as password_utils

router = APIRouter(prefix="/users", tags=["Users"])

MAX_SIZE = 5 * 1024 * 1024


@router.post("/register", response_model=user_schema.UserRegisterResponse)
def create_user(
    request: user_schema.UserRegister = FormDepends(user_schema.UserRegister),  # type: ignore
    db: Session = Depends(get_db),
    image: UploadFile | None = None,
):
    # check both entered passwords are same
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
        )

    del request.confirm_password

    username_check = user_service.check_username_exists(request.username, db)
    if username_check:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username {request.username} is already taken",
        )
    user_check = user_service.check_user_exists(request.email, db)
    if user_check:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{request.email} already exists in the system",
        )

    hashed_password = password_utils.get_hash(request.password)
    request.password = hashed_password

    # image related code
    # if there is image uploaded, create a subfolder for profile pics, if folder exists get it. Upload the image in this folder.
    if image:
        # handling image validatity and unsupported types
        try:
            # we try to open the image, raises UnidentifiedImageError when image doesn't open
            with Image.open(image.file) as img:
                # verifies the image for any tampering/corruption, raises exception if verification fails
                img.verify()

            # move file pointer to the beginning of the file
            image.file.seek(0)

            # read the image file and check file size
            # img_read = image.file.read()
            # print(len(img_read))

            # Move to the end of the file, get image size, no need to read the file
            image.file.seek(0, 2)
            image_size = image.file.tell()

            # move file pointer to the beginning of the file
            image.file.seek(0)
            print(image_size)

            # if len(img_read) > MAX_SIZE: if image is read, we need to get the size using len()
            if image_size > MAX_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image too large, you can upload upto 5 MiB",
                )
        except UnidentifiedImageError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image format"
            ) from exc
        except HTTPException as exc:
            raise exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Error processing image"
            ) from exc

        # db transaction, we flush the user with customized image filename and use user id as name for user subfolder
        # If everything goes right then only we commit. Any exceptions, rollback.
        try:
            upload_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
            image_name = f"{request.username}_{upload_datetime}_{image.filename}"

            add_user = user_model.User(**request.dict(), profile_picture=image_name)  # type: ignore
            db.add(add_user)
            db.flush()

            # create a subfolder for user specific uploads, if folder exists get it.
            user_subfolder = image_utils.get_or_create_user_image_subfolder(
                str(add_user.id)
            )

            # create a subfolder for profile images, if folder exists get it.
            profile_subfolder = image_utils.get_or_create_user_profile_image_subfolder(
                user_subfolder
            )

            image_path = profile_subfolder / image_name

            with open(image_path, "wb+") as f:
                shutil.copyfileobj(image.file, f)

            db.commit()
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error registering user",
            ) from exc

    else:
        add_user = user_model.User(**request.dict())
        db.add(add_user)
        db.commit()

    # store image directly in the DB
    # add_user = user_model.User(**request.dict(), profile_picture=image.file.read())

    db.refresh(add_user)

    return add_user


# password change routes
# password reset when forgot password
@router.post("/password/reset")
def reset_password(
    background_tasks: BackgroundTasks,
    user_email: str = Form(),
    db: Session = Depends(get_db),
):
    reset_user = user_schema.UserPasswordReset(email=user_email)
    # check if user is valid using email
    user = user_service.get_user_by_email(
        reset_user.email, [enum_utils.UserStatusEnum.DELETED], db
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.status in [
        enum_utils.UserStatusEnum.TEMPORARY_BAN,
        enum_utils.UserStatusEnum.PERMANENT_BAN,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to process your request at this time. Please contact support for assistance.",
        )

    # generate a token
    claims = {"sub": user.email, "role": user.type}
    reset_token, reset_token_id = auth_utils.create_reset_token(claims)

    # generate reset link
    reset_link = f"https://vpkonnect.in/accounts/password/change/?token={reset_token}"

    email_subject = "VPKonnect - Password Reset Request"

    # send mail with reset link if user is valid, we will using mailtrap dummy server for testing
    try:
        email_details = admin_schema.SendEmail(
            template="password_reset_email.html",
            email=[reset_user.email],
            body_info={"username": user.username, "link": reset_link},
        )
        email_utils.send_email(email_subject, email_details, background_tasks)
    except Exception as exc:
        auth_utils.blacklist_token(reset_token)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error in sending email",
        ) from exc

    # add the token id to user password reset token table
    add_reset_token_id = auth_model.UserPasswordResetToken(
        reset_token_id=reset_token_id, user_id=user.id
    )
    db.add(add_reset_token_id)
    db.commit()

    return {
        "message": f"An email will be sent to {reset_user.email} if an account is registered under it."
    }


# password change using reset link
@router.post("/password/change")
def change_password_reset(
    password: str = Form(),
    confirm_password: str = Form(),
    reset_token: str = Form(),
    db: Session = Depends(get_db),
):
    reset = user_schema.UserPasswordChangeReset(
        password=password, confirm_password=confirm_password, reset_token=reset_token
    )

    # check both entered passwords
    if reset.password != reset.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
        )

    del confirm_password

    # get the token, decode it, verify it
    token_claims = auth_utils.verify_reset_token(reset.reset_token)

    # check token blacklist
    reset_token_blacklist_check = auth_utils.is_token_blacklisted(token_claims.token_id)
    if reset_token_blacklist_check:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Paswword reset failed, Token invalid/revoked",
        )

    # get the user
    user_query = user_service.get_user_by_email_query(
        token_claims.email, [enum_utils.UserStatusEnum.DELETED], db
    )
    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.status in [
        enum_utils.UserStatusEnum.TEMPORARY_BAN,
        enum_utils.UserStatusEnum.PERMANENT_BAN,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to process your request at this time. Please contact support for assistance.",
        )

    # get query to fetch all reset token ids related to the user
    user_password_reset_tokens_query = (
        auth_service.get_user_password_reset_tokens_query(str(user.id), db)
    )

    # check if token id of token got in form request exists
    token_id_check = user_password_reset_tokens_query.filter(
        auth_model.UserPasswordResetToken.reset_token_id == token_claims.token_id,
        auth_model.UserPasswordResetToken.is_deleted == False,
    ).first()
    if not token_id_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Password reset failed, Reset token not found",
        )
    try:
        # update is_deleted to True for all reset tokens and blacklist all token ids
        user_password_reset_tokens_query.update(
            {"is_deleted": True}, synchronize_session=False
        )
        reset_token_ids = [
            item.reset_token_id for item in user_password_reset_tokens_query.all()
        ]
        for token_id in reset_token_ids:
            auth_utils.blacklist_token(token_id)

        # hash the new password and update the password field in user table
        hashed_password = password_utils.get_hash(reset.password)
        user_query.update({"password": hashed_password}, synchronize_session=False)

        # add an entry to password change history table
        add_password_change_history_entry = user_model.PasswordChangeHistory(
            user_id=user.id
        )
        db.add(add_password_change_history_entry)

        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing change password request",
        ) from exc

    return {"message": "Password change successful"}


@router.post("/{username}/password/change")
def change_password_update(
    username: str,
    old_password: str = Form(),
    new_password: str = Form(),
    confirm_new_password: str = Form(),
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    update = user_schema.UserPasswordChangeUpdate(
        old_password=old_password,
        new_password=new_password,
        confirm_new_password=confirm_new_password,
    )

    # get the user using username
    user_query = user_service.get_user_by_username_query(
        username, [enum_utils.UserStatusEnum.DELETED], db
    )

    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.status in [
        enum_utils.UserStatusEnum.DEACTIVATED_HIDE,
        enum_utils.UserStatusEnum.DEACTIVATED_KEEP,
        enum_utils.UserStatusEnum.PENDING_DELETE_HIDE,
        enum_utils.UserStatusEnum.PENDING_DELETE_KEEP,
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    if user.status in [
        enum_utils.UserStatusEnum.TEMPORARY_BAN,
        enum_utils.UserStatusEnum.PERMANENT_BAN,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to process your request at this time. Please contact support for assistance.",
        )

    # check user identity
    if current_user.email != user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    # check both old password and new password
    if update.old_password == update.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be same as Old Password",
        )

    # check old password
    old_password_check = password_utils.verify_password(
        update.old_password, user.password
    )
    if not old_password_check:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Old password invalid"
        )

    # check both newly entered passwords
    if update.new_password != update.confirm_new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
        )

    del confirm_new_password

    try:
        # hash the new password and update the password field in user table
        hashed_password = password_utils.get_hash(update.new_password)
        user_query.update({"password": hashed_password}, synchronize_session=False)

        # add an entry to password change history table
        add_password_change_history_entry = user_model.PasswordChangeHistory(
            user_id=user.id
        )
        db.add(add_password_change_history_entry)

        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing change password request",
        ) from exc

    return {"message": "Password change successful"}


# follow/unfollow users
@router.post("/follow")
def follow_user(
    followed_user: user_schema.UserFollow,
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get the user to be followed
    user_followed = user_service.get_user_by_username(
        followed_user.username,
        [enum_utils.UserStatusEnum.PERMANENT_BAN, enum_utils.UserStatusEnum.DELETED],
        db,
    )
    if not user_followed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User to be followed not found",
        )

    if user_followed.status in [
        enum_utils.UserStatusEnum.DEACTIVATED_HIDE,
        enum_utils.UserStatusEnum.DEACTIVATED_KEEP,
        enum_utils.UserStatusEnum.PENDING_DELETE_HIDE,
        enum_utils.UserStatusEnum.PENDING_DELETE_KEEP,
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile to be followed not found",
        )

    # get follower user
    follower_user = user_service.get_user_by_email(
        current_user.email,
        [enum_utils.UserStatusEnum.PERMANENT_BAN, enum_utils.UserStatusEnum.DELETED],
        db,
    )

    # user cannot follow/unfollow him/herself
    if followed_user.username == follower_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User cannot follow/unfollow itself",
        )

    # get followed user's followers
    following_usernames = [
        follower_association.follower.username
        for follower_association in user_followed.followers
    ]

    # follow a user
    if followed_user.action == "follow":
        # check if already follows the user
        if follower_user.username in following_usernames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You already are following {user_followed.username}",
            )

        # if user is private then send request orelse follow directly
        if user_followed.account_visibility == enum_utils.UserAccountVisibilityEnum.PRIVATE:  # type: ignore
            # check if follow request already sent
            check_request_sent = user_service.get_user_follow_association_entry_query(
                str(follower_user.id),
                str(user_followed.id),
                enum_utils.UserFollowAssociationStatusEnum.PENDING,
                db,
            )
            if check_request_sent.first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Follow request is already sent",
                )

            follow_request = user_model.UserFollowAssociation(
                status=enum_utils.UserFollowAssociationStatusEnum.PENDING,
                follower=follower_user,
                followed=user_followed,
            )
            db.add(follow_request)
            db.commit()

            return {"message": f"Follow request sent to {followed_user.username}"}
        else:
            follow = user_model.UserFollowAssociation(
                status=enum_utils.UserFollowAssociationStatusEnum.ACCEPTED,
                follower=follower_user,
                followed=user_followed,
            )
            db.add(follow)
            db.commit()

            print(user_followed.followers)
            return {"message": f"Following {followed_user.username}"}

    # unfollow a user
    elif followed_user.action == "unfollow":
        # check if follows the user
        if follower_user.username not in following_usernames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You are not following {user_followed.username}",
            )
        # get user follow entry query
        user_follow_query = user_service.get_user_follow_association_entry_query(
            str(follower_user.id),
            str(user_followed.id),
            enum_utils.UserFollowAssociationStatusEnum.ACCEPTED,
            db,
        )
        if not user_follow_query.first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User follow entry not found",
            )

        # update the status to unfollowed
        user_follow_query.update(
            {"status": enum_utils.UserFollowAssociationStatusEnum.UNFOLLOWED},
            synchronize_session=False,
        )
        db.commit()

        following_usernames = [
            follower_association.follower.username
            for follower_association in user_followed.followers
        ]
        print(following_usernames)
        return {"message": f"Unfollowed {followed_user.username}"}


# accept/reject follow request
@router.put("/follow/requests/{username}")
def manage_follow_request(
    username: str,
    follow_request: user_schema.UserFollowRequest,
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # check for user using username
    follower_user = user_service.get_user_by_username(
        username,
        [enum_utils.UserStatusEnum.PERMANENT_BAN, enum_utils.UserStatusEnum.DELETED],
        db,
    )
    if not follower_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Follower user not found"
        )
    if follower_user.status in [
        enum_utils.UserStatusEnum.DEACTIVATED_HIDE,
        enum_utils.UserStatusEnum.DEACTIVATED_KEEP,
        enum_utils.UserStatusEnum.PENDING_DELETE_HIDE,
        enum_utils.UserStatusEnum.PENDING_DELETE_KEEP,
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follower user profile not found",
        )

    # get current user object
    user = user_service.get_user_by_email(
        current_user.email,
        [enum_utils.UserStatusEnum.PERMANENT_BAN, enum_utils.UserStatusEnum.DELETED],
        db,
    )

    # check for user follow entry with status pending
    user_follow_query = user_service.get_user_follow_association_entry_query(
        str(follower_user.id),
        str(user.id),
        enum_utils.UserFollowAssociationStatusEnum.PENDING,
        db,
    )
    if not user_follow_query.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User follow entry not found"
        )

    # accept the follow request
    if follow_request.action == "accept":
        user_follow_query.update(
            {
                "status": enum_utils.UserFollowAssociationStatusEnum.ACCEPTED,
                "follower_user_id": follower_user.id,
                "followed_user_id": user.id,
            },
            synchronize_session=False,
        )
        db.commit()

        return {"message": f"Following {user.username}"}

    # reject the follow request
    elif follow_request.action == "reject":
        user_follow_query.update(
            {
                "status": enum_utils.UserFollowAssociationStatusEnum.REJECTED,
                "follower_user_id": follower_user.id,
                "followed_user_id": user.id,
            },
            synchronize_session=False,
        )
        db.commit()

        return {"message": f"Rejected the request to follow {user.username}"}


# get all followers/following of a user
@router.get(
    "/{username}/follow",
    response_model=list[user_schema.UserFollowersFollowingResponse],
)
def get_user_followers_following(
    username: str,
    request_info: user_schema.UserFollowersFollowing,
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get user from username
    user = user_service.get_user_by_username(
        username,
        [enum_utils.UserStatusEnum.PERMANENT_BAN, enum_utils.UserStatusEnum.DELETED],
        db,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.status in [
        enum_utils.UserStatusEnum.DEACTIVATED_HIDE,
        enum_utils.UserStatusEnum.DEACTIVATED_KEEP,
        enum_utils.UserStatusEnum.PENDING_DELETE_HIDE,
        enum_utils.UserStatusEnum.PENDING_DELETE_KEEP,
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    # get current user
    curr_auth_user = user_service.get_user_by_email(
        str(current_user.email),
        [enum_utils.UserStatusEnum.PERMANENT_BAN, enum_utils.UserStatusEnum.DELETED],
        db,
    )

    # get details only if owner or public account or follower
    follower_check = user_service.check_user_follower_or_not(
        str(curr_auth_user.id), str(user.id), db
    )

    if (username != curr_auth_user.username) and (user.account_visibility == enum_utils.UserAccountVisibilityEnum.PRIVATE and not follower_check):  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    # check the fetch
    followers_list = []
    following_list = []
    curr_auth_user_following_usernames = [
        following_association.followed.username
        for following_association in curr_auth_user.following
    ]
    if request_info.fetch == "followers":
        user_followers = [
            follower_association.follower for follower_association in user.followers
        ]
        for follower in user_followers:
            if follower.username in curr_auth_user_following_usernames:
                followers_list.append(
                    {
                        "profile_picture": follower.profile_picture,
                        "username": follower.username,
                        "follows_user": True,
                    }
                )
            else:
                if follower.username == curr_auth_user.username:
                    followers_list.append(
                        {
                            "profile_picture": follower.profile_picture,
                            "username": follower.username,
                            "follows_user": None,
                        }
                    )
                else:
                    followers_list.append(
                        {
                            "profile_picture": follower.profile_picture,
                            "username": follower.username,
                            "follows_user": False,
                        }
                    )

        return followers_list

    elif request_info.fetch == "following":
        user_following = [
            following_association.followed for following_association in user.following
        ]
        for following in user_following:
            if following.username in curr_auth_user_following_usernames:
                following_list.append(
                    {
                        "profile_picture": following.profile_picture,
                        "username": following.username,
                        "follows_user": True,
                    }
                )
            else:
                if following.username == curr_auth_user.username:
                    following_list.append(
                        {
                            "profile_picture": following.profile_picture,
                            "username": following.username,
                            "follows_user": None,
                        }
                    )
                else:
                    following_list.append(
                        {
                            "profile_picture": following.profile_picture,
                            "username": following.username,
                            "follows_user": False,
                        }
                    )

        return following_list

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error processing request"
        )


# get all follow requests of a user
@router.get(
    "/{username}/follow/requests",
    response_model=list[user_schema.UserGetFollowRequestsResponse],
)
def get_follow_requests(
    username: str,
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get user from username
    user = user_service.get_user_by_username(
        username,
        [enum_utils.UserStatusEnum.PERMANENT_BAN, enum_utils.UserStatusEnum.DELETED],
        db,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.status in [
        enum_utils.UserStatusEnum.DEACTIVATED_HIDE,
        enum_utils.UserStatusEnum.DEACTIVATED_KEEP,
        enum_utils.UserStatusEnum.PENDING_DELETE_HIDE,
        enum_utils.UserStatusEnum.PENDING_DELETE_KEEP,
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    # get current user
    curr_auth_user = user_service.get_user_by_email(
        current_user.email,
        [enum_utils.UserStatusEnum.PERMANENT_BAN, enum_utils.UserStatusEnum.DELETED],
        db,
    )

    # check user identity
    if username != curr_auth_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    # get all follow requests
    user_follow_requests_entries = user_service.get_user_follow_requests(
        str(user.id), enum_utils.UserFollowAssociationStatusEnum.PENDING, db
    )

    requests_user_ids = [
        entry.follower_user_id for entry in user_follow_requests_entries
    ]
    requests_users = (
        db.query(user_model.User.profile_picture, user_model.User.username)
        .filter(
            user_model.User.id.in_(requests_user_ids),
            user_model.User.status.in_(
                [
                    enum_utils.UserStatusEnum.ACTIVE,
                    enum_utils.UserStatusEnum.RESTRICTED_FULL,
                    enum_utils.UserStatusEnum.RESTRICTED_PARTIAL,
                    enum_utils.UserStatusEnum.TEMPORARY_BAN,
                ]
            ),
        )
        .all()
    )
    print(requests_users)
    return requests_users


# update username
@router.post("/{username}/username/change")
def username_change(
    username: str,
    new_username: str = Form(),
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    update = user_schema.UserUsernameChange(new_username=new_username)

    # get user from username
    user_query = user_service.get_user_by_username_query(
        username,
        [enum_utils.UserStatusEnum.PERMANENT_BAN, enum_utils.UserStatusEnum.DELETED],
        db,
    )
    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.status in [
        enum_utils.UserStatusEnum.DEACTIVATED_HIDE,
        enum_utils.UserStatusEnum.DEACTIVATED_KEEP,
        enum_utils.UserStatusEnum.PENDING_DELETE_HIDE,
        enum_utils.UserStatusEnum.PENDING_DELETE_KEEP,
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    # check user identity
    if current_user.email != user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    # check if new username matches old username
    if update.new_username == username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New username cannot be same as old username",
        )

    # check if new username already taken
    username_exists = user_service.check_username_exists(update.new_username, db)
    if username_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username {update.new_username} is already taken",
        )

    try:
        # update username
        user_query.update({"username": update.new_username}, synchronize_session=False)

        # add entry to username change history table
        add_username_change_history_entry = user_model.UsernameChangeHistory(
            previous_username=username, user_id=user.id
        )
        db.add(add_username_change_history_entry)

        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing username change request",
        ) from exc

    return {"message": "Username change successful"}


# soft-delete the user account
@router.patch("/{username}/remove")
def soft_delete_user(
    username: str,
    background_tasks: BackgroundTasks,
    password: str = Form(None),
    hide_interactions: bool = Form(),
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # check for password in the request
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Password required"
        )

    # create object
    delete_request = user_schema.UserDeletion(
        password=password, hide_interactions=hide_interactions
    )

    # get user from username
    user_query = user_service.get_user_by_username_query(
        username,
        [enum_utils.UserStatusEnum.PERMANENT_BAN, enum_utils.UserStatusEnum.DELETED],
        db,
    )
    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.status in [
        enum_utils.UserStatusEnum.DEACTIVATED_HIDE,
        enum_utils.UserStatusEnum.DEACTIVATED_KEEP,
        enum_utils.UserStatusEnum.PENDING_DELETE_HIDE,
        enum_utils.UserStatusEnum.PENDING_DELETE_KEEP,
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    # check if password is right
    password_check = password_utils.verify_password(
        delete_request.password, user.password
    )
    if not password_check:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )

    # get current user
    curr_auth_user = user_service.get_user_by_email(
        current_user.email,
        [enum_utils.UserStatusEnum.PERMANENT_BAN, enum_utils.UserStatusEnum.DELETED],
        db,
    )

    # check user identity
    if username != curr_auth_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action",
        )

    # send mail informing user about the account deletion, we will using mailtrap dummy server for testing
    try:
        email_subject = "Your VPKonnect account is scheduled for deletion"
        email_details = admin_schema.SendEmail(
            template="account_deletion_email.html",
            email=[user.email],
            body_info={"username": user.username},
        )
        email_utils.send_email(email_subject, email_details, background_tasks)

        # update status to pending_deletion_(hide/keep)
        if delete_request.hide_interactions:
            user_query.update(
                {"status": enum_utils.UserStatusEnum.PENDING_DELETE_HIDE},
                synchronize_session=False,
            )
        else:
            user_query.update(
                {"status": enum_utils.UserStatusEnum.PENDING_DELETE_KEEP},
                synchronize_session=False,
            )
        db.commit()
    except Exception as exc:
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error in processing delete user request",
        ) from exc

    return {
        "message": f"Your account deletion request is accepted. {user.username} account will be deleted after a deactivation period of 30 days. An email for the same has been sent to {user.email}"
    }
