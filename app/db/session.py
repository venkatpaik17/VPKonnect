from app.db.db_sqlalchemy import SessionLocal


# create a session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
