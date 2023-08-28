from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_hash(password: str):
    return pwd_context.hash(password)


def verify_password(entered_password: str, hashed_password: str):
    return pwd_context.verify(entered_password, hashed_password)
