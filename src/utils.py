import subprocess
from typing import Generator

import bcrypt
from sqlmodel import Session, SQLModel, create_engine

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args, echo=False)


def get_session() -> Generator[Session, None, None]:
    """
    Creates a new database session.

    Yields
    ------
    Session
        A SQLModel session connected to the database.
    """
    with Session(engine) as session:
        yield session


def fake_hash(_password: str) -> str:
    """
    Returns a fake hash for testing purposes.

    Parameters
    ----------
    _password : str
        The password to mock hash (unused).

    Returns
    -------
    str
        A fixed string "pw".
    """
    return "pw"


def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt.

    Parameters
    ----------
    password : str
        The plain text password to hash.

    Returns
    -------
    str
        The hashed password.
    """
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed_pw.decode()


def check_hash(password: str, hashed_password: str) -> bool:
    """
    Verifies a password against a hash.

    Parameters
    ----------
    password : str
        The plain text password.
    hashed_password : str
        The hashed password to verify against.

    Returns
    -------
    bool
        True if the password matches the hash, False otherwise.
    """
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def create_db_and_tables():
    """
    Creates the database and tables defined in SQLModel metadata.
    """
    SQLModel.metadata.create_all(engine)


def get_git_version(default: str = "0.0.0") -> str:
    """
    Retrieves the current git version (tag).

    Parameters
    ----------
    default : str, optional
        The default version string to return if git command fails, by default "0.0.0".

    Returns
    -------
    str
        The git version tag or the default value.
    """
    try:
        version = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"])
        return version.decode().strip()
    except Exception:
        return default
