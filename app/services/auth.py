from sqlalchemy.orm import Session

from app.models import auth as auth_model


# get the entry with specific refresh token id and active status
def check_refresh_token_id_in_user_auth_track(
    token_id: str, status: str, db_session: Session
):
    return get_auth_track_entry_by_token_id_query(token_id, status, db_session).first()


# get the query for user auth track entry
def get_auth_track_entry_by_token_id_query(
    token_id: str, status: str, db_session: Session
):
    return db_session.query(auth_model.UserAuthTrack).filter(
        auth_model.UserAuthTrack.refresh_token_id == token_id,
        auth_model.UserAuthTrack.status == status,
    )


def get_all_user_auth_track_entries_by_user_id(
    user_id: str, status: str, db_session: Session
):
    return (
        db_session.query(auth_model.UserAuthTrack)
        .filter(
            auth_model.UserAuthTrack.user_id == user_id,
            auth_model.UserAuthTrack.status == status,
        )
        .all()
    )


# get the query for fetching all codes/tokens of a user
def get_user_verification_codes_tokens_query(
    user_id: str, _type: str, db_session: Session
):
    return db_session.query(auth_model.UserVerificationCodeToken).filter(
        auth_model.UserVerificationCodeToken.user_id == user_id,
        auth_model.UserVerificationCodeToken.type == _type,
    )
