from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from src.authentication import get_current_user
from src.errors import unauthorized_error
from src.models import (
    User,
    UserCreate,
    UserPublic,
    UserPublicWithItems,
    UserPublicWithTransactions,
    UserUpdate,
)
from src.utils import get_session, hash_password

router = APIRouter()


@router.post("/users/", response_model=UserPublic)
def add_user(*, session: Session = Depends(get_session), user: UserCreate):
    """
    Creates a new user.

    Parameters
    ----------
    session : Session
        The database session.
    user : UserCreate
        The user creation data.

    Returns
    -------
    User
        The created user object.

    Raises
    ------
    HTTPException
        If the email already exists (IntegrityError).
    """
    hashed_pw = hash_password(user.password)
    extra_data = {"hashed_password": hashed_pw}
    db_user = User.model_validate(user, update=extra_data)
    try:
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")


@router.get("/users/{user_id}", response_model=UserPublicWithItems)
def fetch_user(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_id: str,
):
    """
    Retrieves a user by their ID, including their items.

    Parameters
    ----------
    session : Session
        The database session.
    current_user : User
        The authenticated user.
    user_id : str
        The ID of the user to retrieve.

    Returns
    -------
    User
        The user object.

    Raises
    ------
    HTTPException
        If the user is not found.
    unauthorized_error
        If the user belongs to a different flat.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.flat_id != current_user.flat_id:
        raise unauthorized_error
    return user


@router.get("/users/{user_id}/transactions", response_model=UserPublicWithTransactions)
def fetch_user_with_transactions(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_id: str,
):
    """
    Retrieves a user by their ID, including their transactions.

    Parameters
    ----------
    session : Session
        The database session.
    current_user : User
        The authenticated user.
    user_id : str
        The ID of the user to retrieve.

    Returns
    -------
    User
        The user object with transactions.

    Raises
    ------
    HTTPException
        If the user is not found.
    unauthorized_error
        If the user belongs to a different flat.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.flat_id != current_user.flat_id:
        raise unauthorized_error
    return user


@router.patch("/users/{user_id}", response_model=UserPublic)
def update_user(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_id: str,
    user: UserUpdate,
):
    """
    Updates a user's details.

    Parameters
    ----------
    session : Session
        The database session.
    current_user : User
        The authenticated user.
    user_id : str
        The ID of the user to update.
    user : UserUpdate
        The new data for the user.

    Returns
    -------
    User
        The updated user object.

    Raises
    ------
    HTTPException
        If the user is not found.
    unauthorized_error
        If the user ID does not match the authenticated user.
    """
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.id != current_user.id:
        raise unauthorized_error

    user_data = user.model_dump(exclude_unset=True)

    if user.password:
        user_data["hashed_password"] = hash_password(user.password)
        user_data.pop("password", None)

    db_user.sqlmodel_update(user_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.delete("/users/{user_id}")
def delete_user(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_id: str,
):
    """
    Deletes a user.

    Parameters
    ----------
    session : Session
        The database session.
    current_user : User
        The authenticated user.
    user_id : str
        The ID of the user to delete.

    Returns
    -------
    dict
        A confirmation message.

    Raises
    ------
    HTTPException
        If the user is not found.
    unauthorized_error
        If the user ID does not match the authenticated user.
    """
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.id != current_user.id:
        raise unauthorized_error
    session.delete(db_user)
    session.commit()
    return {"ok": True}
