from datetime import date
from fastapi.exceptions import HTTPException
from sqlmodel import Session

from src.depreciation import depreciate_price
from src.models import (
    Item,
)
from src.models import Transaction
from src.models import User


def item_buy_in(session: Session, new_user: User, item: Item, date: date):
    """
    Calculates and records the buy-in transaction for a new user joining an item ownership.

    Parameters
    ----------
    session : Session
        The database session.
    new_user : User
        The user who is buying into the item.
    item : Item
        The item being bought into.
    date : date
        The date of the buy-in.

    Raises
    ------
    HTTPException
        If the item has no users, or if item/user IDs are undefined.
    """
    if len(item.users) == 0:
        raise HTTPException(
            status_code=500, detail="Item should have at least one user"
        )
    depreciated_price = depreciate_price(item, date)
    calculated_amount = (depreciated_price / len(item.users)) - (
        depreciated_price / (len(item.users) + 1)
    )
    if item.id is None:
        raise HTTPException(status_code=404, detail="Item needs to have a defined id")
    if new_user.id is None:
        raise HTTPException(status_code=404, detail="User needs to have a defined id")
    for existing_user in item.users:
        if existing_user.id is None:
            raise HTTPException(
                status_code=404, detail="User needs to have a defined id"
            )
        new_transaction = Transaction(
            creditor_id=existing_user.id,
            debtor_id=new_user.id,
            item_id=item.id,
            amount=calculated_amount,
            paid=False,
        )
        session.add(new_transaction)
