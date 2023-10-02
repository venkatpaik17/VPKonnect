from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import user as user_service


def delete_user_after_deactivation_period_expiration(db: Session = next(get_db())):
    delete_entries_query = user_service.check_deactivation_expiration_query(db)
    users_to_be_delete = delete_entries_query.all()
    if users_to_be_delete:
        delete_entries_query.update(
            {"status": "deleted", "is_deleted": True}, synchronize_session=False
        )
        db.commit()
