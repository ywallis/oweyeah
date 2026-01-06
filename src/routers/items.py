from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import HTTPException
from sqlmodel import Session

from src.authentication import get_current_user
from src.buy_in import item_buy_in
from src.buy_out import item_buy_out
from src.errors import unauthorized_error
from src.models import (
    Flat,
    Item,
    ItemCreate,
    ItemPublic,
    ItemPublicWithTransactions,
    ItemPublicWithUsers,
    ItemUpdate,
    User,
)
from src.utils import get_session

router = APIRouter()


@router.post("/items/", response_model=ItemPublicWithUsers)
def add_item(
    *,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    item: ItemCreate,
):
    """
    Adds a new item to the user's flat.

    Parameters
    ----------
    current_user : User
        The authenticated user.
    session : Session
        The database session.
    item : ItemCreate
        The item creation data.

    Returns
    -------
    Item
        The created item, associated with all users in the flat.

    Raises
    ------
    HTTPException
        If the user is not in a flat or the flat cannot be found.
    """
    if current_user.flat is None:
        raise HTTPException(
            status_code=400,
            detail="User must have an assigned flat before adding items",
        )
    flat = session.get(Flat, current_user.flat.id)
    if not flat:
        raise HTTPException(status_code=404, detail="Flat not found")
    db_item = Item.model_validate(item)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    db_item.users = flat.users
    session.commit()
    session.refresh(db_item)
    return db_item


@router.get("/items/{item_id}", response_model=ItemPublicWithUsers)
def fetch_item(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    item_id: str,
):
    """
    Retrieves an item by its ID.

    Parameters
    ----------
    session : Session
        The database session.
    current_user : User
        The authenticated user.
    item_id : str
        The ID of the item to retrieve.

    Returns
    -------
    Item
        The item object.

    Raises
    ------
    HTTPException
        If the item is not found.
    unauthorized_error
        If the item belongs to a different flat than the user.
    """
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.flat_id != current_user.flat_id:
        raise unauthorized_error
    return item


@router.get("/items/{item_id}/transactions/", response_model=ItemPublicWithTransactions)
def fetch_item_with_transactions(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    item_id: str,
):
    """
    Retrieves an item along with its associated transactions.

    Parameters
    ----------
    session : Session
        The database session.
    current_user : User
        The authenticated user.
    item_id : str
        The ID of the item.

    Returns
    -------
    Item
        The item object including transactions.

    Raises
    ------
    HTTPException
        If the item is not found.
    unauthorized_error
        If the item belongs to a different flat than the user.
    """
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.flat_id != current_user.flat_id:
        raise unauthorized_error
    return item


@router.patch("/items/{item_id}", response_model=ItemPublic)
def update_item(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    item_id: str,
    item: ItemUpdate,
):
    """
    Updates an item's details.

    Parameters
    ----------
    session : Session
        The database session.
    current_user : User
        The authenticated user.
    item_id : str
        The ID of the item to update.
    item : ItemUpdate
        The new data for the item.

    Returns
    -------
    Item
        The updated item object.

    Raises
    ------
    HTTPException
        If the item is not found.
    unauthorized_error
        If the item belongs to a different flat than the user.
    """
    db_item = session.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    if db_item.flat_id != current_user.flat_id:
        raise unauthorized_error
    item_data = item.model_dump(exclude_unset=True)
    db_item.sqlmodel_update(item_data)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@router.delete("/items/{item_id}")
def delete_item(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    item_id: str,
):
    """
    Deletes an item.

    Parameters
    ----------
    session : Session
        The database session.
    current_user : User
        The authenticated user.
    item_id : str
        The ID of the item to delete.

    Returns
    -------
    dict
        A confirmation message.

    Raises
    ------
    HTTPException
        If the item is not found.
    unauthorized_error
        If the item belongs to a different flat than the user.
    """
    db_item = session.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    if db_item.flat_id != current_user.flat_id:
        raise unauthorized_error
    session.delete(db_item)
    session.commit()
    return {"ok": True}


@router.patch("/items/{item_id}/add/{user_id}", response_model=ItemPublicWithUsers)
def add_user_to_item(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    item_id: str,
    user_id: str,
    date: date = Query(...),
):
    """
    Adds a user to an item and creates the associated credits/debts.

    Parameters
    ----------
    session : Session
        The database session.
    current_user : User
        The authenticated user.
    item_id : str
        The ID of the item.
    user_id : str
        The ID of the user to add.
    date : date
        The effective date of the addition (buy-in).

    Returns
    -------
    Item
        The updated item object.

    Raises
    ------
    HTTPException
        If item/user not found, user already in item, or unauthorized.
    """
    db_item = session.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    if db_item.flat_id != current_user.flat_id:
        raise unauthorized_error
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user in db_item.users:
        raise HTTPException(status_code=409, detail="User is already assigned to item")

    item_buy_in(session, db_user, db_item, date)
    db_item.users.append(db_user)

    session.commit()
    session.refresh(db_item)
    return db_item


@router.patch("/items/{item_id}/remove/{user_id}", response_model=ItemPublicWithUsers)
def remove_user_from_item(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    item_id: str,
    user_id: str,
    date: date,
):
    """
    Removes a user from an item and creates the associated credits/debts (buy-out).

    Parameters
    ----------
    session : Session
        The database session.
    current_user : User
        The authenticated user.
    item_id : str
        The ID of the item.
    user_id : str
        The ID of the user to remove.
    date : date
        The effective date of removal.

    Returns
    -------
    Item
        The updated item object.

    Raises
    ------
    HTTPException
        If item/user not found, user not in item, or unauthorized.
    """
    db_item = session.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    if db_item.flat_id != current_user.flat_id:
        raise unauthorized_error
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user in db_item.users:
        item_buy_out(session, db_user, db_item, date)
        db_item.users.remove(db_user)
    else:
        raise HTTPException(status_code=404, detail="User was not item owner")

    session.commit()
    session.refresh(db_item)
    return db_item
