from sqlalchemy.orm import Session

from app.models import auth as auth_model


# get the entry with specific refresh token id and active status
def check_refresh_token_id_in_user_auth_track(token_id: str, db_session: Session):
    return (
        db_session.query(auth_model.UserAuthTrack)
        .filter(
            auth_model.UserAuthTrack.refresh_token_id == token_id,
            auth_model.UserAuthTrack.status == "active",
        )
        .first()
    )


# get the query for user auth track entry
def get_auth_track_entry_by_token_id_query(token_id: str, db_session: Session):
    return db_session.query(auth_model.UserAuthTrack).filter(
        auth_model.UserAuthTrack.refresh_token_id == token_id
    )
