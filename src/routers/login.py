from datetime import timedelta

import requests
from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic import EmailStr
from sqlmodel import Session, select

from src.authentication import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ResetPasswordRequest,
    create_access_token,
    create_refresh_token,
    extract_user,
    get_current_user,
    google_client_id,
    google_client_secret,
    google_redirect_url,
)
from src.models import (
    RefreshToken,
    RefreshTokenRequest,
    Token,
    TokenUrl,
    User,
    UserCreateNP,
    UserPublic,
)
from src.utils import check_hash, get_session, hash_password

router = APIRouter()


@router.get(
    "/login/google", summary="Initiate Google OAuth Login", response_model=TokenUrl
)
async def login_google():
    """
    Redirects the user to Google's OAuth consent screen.

    The `scope` parameter requests access to the user's OpenID, profile, and email information.

    Returns
    -------
    TokenUrl
        A JSON object containing the Google OAuth URL.

    Raises
    ------
    HTTPException
        If the Google OAuth configuration (Client ID or Redirect URL) is missing.
    """
    # Ensure google_client_id and google_redirect_url are correctly configured
    if not google_client_id or not google_redirect_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth configuration missing.",
        )

    url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"response_type=code&client_id={google_client_id}&"
        f"redirect_uri={google_redirect_url}&scope=openid%20profile%20email&"
        f"access_type=online"
    )
    return TokenUrl(url=url)


@router.post("/login/password", summary="Login endpoint for email/password")
async def login_for_token(
    *,
    session: Session = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """
    Authenticates a user using email and password.

    The email is used as the username in the OAuth2 form.

    Parameters
    ----------
    session : Session
        The database session.
    form_data : OAuth2PasswordRequestForm
        The form data containing username (email) and password.

    Returns
    -------
    Token
        The refresh token upon successful authentication.

    Raises
    ------
    HTTPException
        If authentication fails (user not found, password mismatch, etc.).
    """
    statement = select(User).where(User.email == form_data.username)
    user = session.exec(statement).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Cannot authenticate")
    if user.hashed_password is None:
        raise HTTPException(status_code=404, detail="Cannot authenticate")
    if not check_hash(form_data.password, user.hashed_password):
        raise HTTPException(status_code=404, detail="Cannot authenticate")

    if user.id is None:
        raise HTTPException(status_code=404, detail="Cannot authenticate")

    # Creating refresh token
    refresh_token = create_refresh_token(user.email, user.id)
    session.add(refresh_token)
    session.commit()

    return Token(token=refresh_token.token, token_type="refresh")


@router.post(
    "/login/refresh",
    response_model=Token,
    summary="Generates an access token from a refresh token",
)
async def get_access_token(
    *,
    refresh_token: RefreshTokenRequest,
    session: Session = Depends(get_session),
):
    """
    Exchanges a valid refresh token for a new access token.

    Parameters
    ----------
    refresh_token : RefreshTokenRequest
        The request body containing the refresh token.
    session : Session
        The database session.

    Returns
    -------
    Token
        The new bearer access token.

    Raises
    ------
    HTTPException
        If the refresh token is invalid or not found.
    """
    statement = select(RefreshToken).where(
        RefreshToken.token == refresh_token.refresh_token
    )
    token = session.exec(statement).one_or_none()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    if not token.valid:
        raise HTTPException(status_code=404, detail="Token has been voided")

    access_token = create_access_token(
        data={"sub": str(token.user_id)},
        expires=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(token=access_token, token_type="bearer")


@router.post(
    "/login/signout", summary="Signs the user out of a single or all locations."
)
async def void_refresh_token(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    single_token: RefreshTokenRequest | None,
):
    """
    Invalidates refresh tokens to sign out the user.

    If a single token is provided, only that token is voided.
    If no token is provided, all refresh tokens for the user are voided.

    Parameters
    ----------
    session : Session
        The database session.
    current_user : User
        The authenticated user.
    single_token : RefreshTokenRequest | None
        The specific token to void, or None to void all.

    Returns
    -------
    dict
        A confirmation message.

    Raises
    ------
    HTTPException
        If no tokens are found to void.
    """
    if single_token is None:
        statement = select(RefreshToken).where(
            RefreshToken.user_email == current_user.email
        )
        tokens = session.exec(statement).all()
    else:
        statement = select(RefreshToken).where(
            RefreshToken.token == single_token.refresh_token
        )
        tokens = session.exec(statement).all()
    if len(tokens) == 0:
        raise HTTPException(status_code=404, detail="No tokens found")
    for token in tokens:
        token.valid = False
        session.add(token)
    session.commit()
    return {"deleted": "ok"}


@router.post("/login/request_password_reset")
async def request_password_reset(
    email: EmailStr,
    session: Session = Depends(get_session),
):
    """
    Generates a password reset token for the given email.

    Parameters
    ----------
    email : EmailStr
        The email address of the user.
    session : Session
        The database session.

    Returns
    -------
    dict
        A JSON object containing the reset token.

    Raises
    ------
    HTTPException
        If the user is not found.
    """
    statement = select(User).where(User.email == email)
    user = session.exec(statement).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token_expiration = timedelta(minutes=5)
    access_token = create_access_token(
        data={"sub": user.email}, expires=token_expiration
    )
    return {"token": access_token}


@router.post("/login/reset_password")
async def reset_password(
    data: ResetPasswordRequest,
    session: Session = Depends(get_session),
):
    """
    Resets the user's password using a valid reset token.

    Parameters
    ----------
    data : ResetPasswordRequest
        The request body containing the token and new password.
    session : Session
        The database session.

    Returns
    -------
    dict
        A confirmation message.

    Raises
    ------
    HTTPException
        If the user is not found.
    """
    email = extract_user(data)

    statement = select(User).where(User.email == email)
    user = session.exec(statement).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(data.new_password)
    session.commit()
    return {"password_change": "ok"}


@router.get("/login/me", response_model=UserPublic)
async def read_me(current_user: User = Depends(get_current_user)):
    """
    Retrieves the current authenticated user's profile.

    Parameters
    ----------
    current_user : User
        The authenticated user.

    Returns
    -------
    User
        The user profile.
    """
    return current_user


@router.get(
    "/auth/google",
    response_model=Token,
    summary="Handle Google OAuth callback and issue internal token. Creates new user if none exists.",
)
async def auth_google(
    code: str, redirect_uri: str | None = None, session: Session = Depends(get_session)
):
    """
    Handles the Google OAuth callback, validates the code, and issues a refresh token.

    If the user does not exist in the database, a new user is created.

    Parameters
    ----------
    code : str
        The authorization code received from Google.
    redirect_uri : str | None, optional
        The redirect URI used in the initial request, by default None.
    session : Session
        The database session.

    Returns
    -------
    Token
        The refresh token.

    Raises
    ------
    HTTPException
        If token exchange fails, token is invalid, or user ID cannot be validated.
    ValueError
        If token verification fails (audience/issuer).
    """
    if redirect_uri is None:
        redirect_uri = google_redirect_url
    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "code": code,
        "client_id": google_client_id,
        "client_secret": google_client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    response = requests.post(token_url, data=data)
    response.raise_for_status()

    tokens = response.json()
    google_access_token = tokens.get("access_token")
    google_id_token = tokens.get("id_token")

    if not google_access_token or not google_id_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing access_token or id_token from Google response.",
        )

    # This only checks the validity of the Google-issued token
    idinfo = id_token.verify_oauth2_token(
        google_id_token, google_requests.Request(), google_client_id
    )
    if idinfo["aud"] != google_client_id:
        raise ValueError("Could not verify audience.")
    if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
        raise ValueError("Wrong issuer.")

    user_email = idinfo.get("email")

    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google ID token did not contain an email address.",
        )

    statement = select(User).where(User.email == user_email)
    user = session.exec(statement).one_or_none()
    if not user:
        headers = {"Authorization": f"Bearer {google_access_token}"}
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo", headers=headers
        )
        user_info = resp.json()
        first_name = user_info.get("given_name")
        last_name = user_info.get("family_name")
        new_User = UserCreateNP(
            first_name=first_name, last_name=last_name, email=user_email
        )
        db_user = User.model_validate(new_User)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        user = db_user

    if user.id is None:
        raise HTTPException(status_code=404, detail="Unvalidated user id")
    # Creating refresh token
    refresh_token = create_refresh_token(user.email, user.id)
    session.add(refresh_token)
    session.commit()

    return Token(token=refresh_token.token, token_type="refresh")
