import subprocess

import bcrypt
from sqlmodel import Session, SQLModel, create_engine

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args, echo=False)


def get_session():
    with Session(engine) as session:
        yield session


def fake_hash(_password: str) -> str:
    return "pw"


def hash_password(password: str) -> str:
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed_pw.decode()


def check_hash(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_git_version(default: str = "0.0.0") -> str:
    try:
        version = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"])
        return version.decode().strip()
    except Exception:
        return default
