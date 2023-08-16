import ulid
from sqlalchemy import Column, String, insert, select
from sqlalchemy.dialects.postgresql import UUID

from app.db.db_sqlalchemy import Base, engine


# function to generate ulid and return as uuid (used ulid-py package)
def get_ulid():
    return ulid.new().uuid


# this is user orm model to create user table, here id is ulid generated client side and then added into table
class User(Base):
    __tablename__ = "user"
    id = Column(UUID(as_uuid=True), primary_key=True, default=get_ulid)
    name = Column(String(length=50), nullable=False)


# inserting a entry, id will be default generated
stmt = insert(User).values(name="vpk")

# connection and execution
with engine.connect() as conn:
    result = conn.execute(stmt)

# getting all users from user table
stmt = select(User)
with engine.connect() as conn:
    result = conn.execute(stmt).all()

    # getting the uuid from first entry
    print(result[0][0])
    # getting all rows
    print(result)
