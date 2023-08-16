from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config.app import settings

# use env variables
SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"

# engine is responsible for sqlalchemy to connect to a DB
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# this is a session class, each instance will be a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# this returns a base class which we will inherit to create each database models/ORM models
Base = declarative_base()
