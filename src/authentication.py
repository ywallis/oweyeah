import os
import secrets
from datetime import datetime, timedelta

import jwt
from dotenv import load_dotenv
from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jwt.exceptions import InvalidTokenError
from sqlmodel import Session, select

from src.models import RefreshToken, ResetPasswordRequest, TokenData, User
from src.utils import get_session

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10

load_dotenv()
secret_key = os.getenv("SECRET_KEY")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
google_client_id = os.getenv("GOOGLE_CLIENT_ID")
google_redirect_url = os.getenv("GOOGLE_REDIRECT_URI")

if secret_key is None:
    raise Exception("You need to set SECRET_KEY as an environment variable")

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="Bearer Token Authentication")


def create_opaque_token() -> str:
    return secrets.token_urlsafe(64)


def create_refresh_token(user_email: str, user_id: int) -> RefreshToken:
    opaque_token = create_opaque_token()
    refresh_token_expiration = datetime.now() + timedelta(days=30)
    refresh_token = RefreshToken(
        token=opaque_token,
        user_email=user_email,
        user_id=user_id,
        expiration=refresh_token_expiration,
        valid=True,
    )

    return refresh_token


def create_access_token(data: dict, expires: timedelta | None = None):
    to_encode = data.copy()
    if expires:
        expiration = datetime.now() + expires
    else:
        expiration = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expiration})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def extract_user(reset_data: ResetPasswordRequest):
    payload = jwt.decode(reset_data.token, secret_key, algorithms=[ALGORITHM])
    email = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=404, detail="No user found")

    return email


async def get_current_user(
    *,
    session: Session = Depends(get_session),
    http_token: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if not http_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated: Missing Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = http_token.credentials

    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        id = payload.get("sub")
        if id is None:
            raise HTTPException(
                status_code=401, detail="Could not validate credentials"
            )
        token_data = TokenData(id=id)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Could not validate credentials 2")

    statement = select(User).where(User.id == token_data.id)
    user = session.exec(statement).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Could not validate credentials 3")
    return user
