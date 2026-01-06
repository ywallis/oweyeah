from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlmodel import Session

from src.authentication import get_current_user
from src.errors import unauthorized_error
from src.models import (
    TransactionPublic,
    User,
)
from src.utils import get_session

router = APIRouter()


@router.get("/transactions/{user_id}/debts", response_model=list[TransactionPublic])
def fetch_user_debts(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_id: int,
    paid: bool = False,
):
    """
    Retrieves the list of debts for a specific user.

    Parameters
    ----------
    session : Session
        The database session.
    current_user : User
        The authenticated user.
    user_id : int
        The ID of the user whose debts are being fetched.
    paid : bool, optional
        Filter by paid status, by default False.

    Returns
    -------
    list[TransactionPublic]
        A list of debt transactions.

    Raises
    ------
    HTTPException
        If the user is not found.
    unauthorized_error
        If the user belongs to a different flat.
    """
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.flat_id != current_user.flat_id:
        raise unauthorized_error
    output = [transaction for transaction in db_user.debts if transaction.paid == paid]
    return output


@router.get("/transactions/{user_id}/credits", response_model=list[TransactionPublic])
def fetch_user_credits(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_id: int,
    paid: bool = False,
):
    """
    Retrieves the list of credits for a specific user.

    Parameters
    ----------
    session : Session
        The database session.
    current_user : User
        The authenticated user.
    user_id : int
        The ID of the user whose credits are being fetched.
    paid : bool, optional
        Filter by paid status, by default False.

    Returns
    -------
    list[TransactionPublic]
        A list of credit transactions.

    Raises
    ------
    HTTPException
        If the user is not found.
    unauthorized_error
        If the user belongs to a different flat.
    """
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.flat_id != current_user.flat_id:
        raise unauthorized_error
    output = [
        transaction for transaction in db_user.credits if transaction.paid == paid
    ]
    return output
