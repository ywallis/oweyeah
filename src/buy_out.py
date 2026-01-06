from datetime import date
from fastapi.exceptions import HTTPException
from sqlmodel import Session

from src.depreciation import depreciate_price
from src.models import (
    Item,
)
from src.models import Transaction
from src.models import User


def item_buy_out(session: Session, user_to_remove: User, item: Item, date: date):
    """
    Calculates and records the buy-out transaction for a user leaving an item ownership.

    Parameters
    ----------
    session : Session
        The database session.
    user_to_remove : User
        The user who is being bought out.
    item : Item
        The item being bought out of.
    date : date
        The date of the buy-out.

    Raises
    ------
    HTTPException
        If the item has 1 or fewer users, or if item/user IDs are undefined.
    """
    if len(item.users) <= 1:
        raise HTTPException(
            status_code=500, detail="Item should have at least one user"
        )
    depreciated_price = depreciate_price(item, date)
    leaving_user_share = depreciated_price / len(item.users)
    buyout_amount = leaving_user_share / (len(item.users) - 1)
    if item.id is None:
        raise HTTPException(status_code=404, detail="Item needs to have a defined id")
    if user_to_remove.id is None:
        raise HTTPException(status_code=404, detail="User needs to have a defined id")

    for existing_user in item.users:
        if existing_user.id == user_to_remove.id:
            continue
        if existing_user.id is None:
            raise HTTPException(
                status_code=404, detail="User needs to have a defined id"
            )
        new_transaction = Transaction(
            creditor_id=user_to_remove.id,
            debtor_id=existing_user.id,
            item_id=item.id,
            amount=buyout_amount,
            paid=False,
        )
        session.add(new_transaction)
