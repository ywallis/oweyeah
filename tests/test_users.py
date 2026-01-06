from fastapi.testclient import TestClient
from sqlmodel import Session

from src.models import Flat, Item, Transaction, User


def test_add_user(client: TestClient):
    """
    Tests adding a new user.

    Parameters
    ----------
    client : TestClient
        The test client.
    """
    response = client.post(
        "/users/",
        json={
            "first_name": "Yann",
            "last_name": "Wallis",
            "email": "y.w@g.c",
            "flat_id": "0",
            "password": "pw",
        },
    )
    data = response.json()

    assert response.status_code == 200
    assert data["first_name"] == "Yann"
    assert data["last_name"] == "Wallis"
    assert data["email"] == "y.w@g.c"
    assert data["flat_id"] == "0"


def test_fetch_user(client: TestClient, session: Session, user_1: User):
    """
    Tests retrieving a user by ID.

    Parameters
    ----------
    client : TestClient
        The test client.
    session : Session
        The database session.
    user_1 : User
        The user to fetch.
    """
    session.add(user_1)
    session.commit()
    session.refresh(user_1)
    db_user = session.get(User, user_1.id)
    if not db_user:
        raise Exception("User not found")
    assert db_user.first_name == "Yann"

    response = client.get(f"/users/{user_1.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Yann"
    assert data["last_name"] == "Wallis"
    assert data["email"] == "y.w@g.c"
    assert data["flat_id"] is None


def test_fetch_user_no_transactions(client: TestClient, session: Session, user_1: User):
    """
    Tests fetching a user's transactions when there are none.

    Parameters
    ----------
    client : TestClient
        The test client.
    session : Session
        The database session.
    user_1 : User
        The user to check.
    """
    session.add(user_1)
    session.commit()
    session.refresh(user_1)

    response = client.get(f"/users/{user_1.id}/transactions")

    assert response.status_code == 200
    data = response.json()

    assert len(data["debts"]) == 0
    assert len(data["credits"]) == 0


def test_fetch_user_transactions(
    client: TestClient,
    session: Session,
    user_1: User,
    user_2: User,
    flat_1: Flat,
    item_1: Item,
):
    """
    Tests fetching a user's transactions when they exist.

    Parameters
    ----------
    client : TestClient
        The test client.
    session : Session
        The database session.
    user_1 : User
        The first user (creditor).
    user_2 : User
        The second user (debtor).
    flat_1 : Flat
        The shared flat.
    item_1 : Item
        The shared item.
    """
    session.add(user_1)
    session.add(user_2)
    session.add(flat_1)
    session.commit()
    session.refresh(user_1)
    session.refresh(user_2)
    user_1.flat_id = flat_1.id
    user_2.flat_id = flat_1.id
    session.commit()
    session.refresh(user_1)
    session.refresh(user_2)
    assert user_1.flat_id == flat_1.id
    assert user_2.flat_id == flat_1.id

    item_1.flat_id = flat_1.id
    item_1.users = flat_1.users
    session.add(item_1)
    session.commit()
    session.refresh(item_1)

    assert len(item_1.users) == 2
    if user_1.id is None or user_2.id is None or item_1.id is None:
        raise Exception("Issue creating ids")
    transaction = Transaction(
        creditor_id=user_1.id,
        debtor_id=user_2.id,
        item_id=item_1.id,
        amount=50,
        paid=False,
    )
    session.add(transaction)
    session.commit()

    response = client.get(f"/users/{user_1.id}/transactions")
    assert response.status_code == 200
    data = response.json()
    assert len(data["credits"]) == 1
    assert len(data["debts"]) == 0


def test_update_user(client: TestClient, session: Session, user_1: User):
    """
    Tests updating a user's profile.

    Parameters
    ----------
    client : TestClient
        The test client.
    session : Session
        The database session.
    user_1 : User
        The user to update.
    """
    session.add(user_1)
    session.commit()
    session.refresh(user_1)
    db_user = session.get(User, user_1.id)
    if not db_user:
        raise Exception("User not found")
    assert db_user.first_name == "Yann"

    response = client.patch(
        f"/users/{user_1.id}",
        json={
            "first_name": "John",
        },
    )
    print(user_1.id)
    print(response)
    assert response.status_code == 200

    data = response.json()

    assert data["first_name"] == "John"
    assert data["last_name"] == "Wallis"


def test_delete_user(client: TestClient, session: Session, user_1: User):
    """
    Tests deleting a user.

    Parameters
    ----------
    client : TestClient
        The test client.
    session : Session
        The database session.
    user_1 : User
        The user to delete.
    """
    session.add(user_1)
    session.commit()
    session.refresh(user_1)
    db_user = session.get(User, user_1.id)
    if not db_user:
        raise Exception("User not found")
    assert db_user.first_name == "Yann"

    response = client.delete(f"/users/{user_1.id}")

    assert response.status_code == 200

    data = response.json()

    assert data == {"ok": True}

    deleted_user = session.get(User, user_1.id)
    assert deleted_user is None
