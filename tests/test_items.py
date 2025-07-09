from fastapi.testclient import TestClient
from sqlmodel import Session

from src.buy_in import item_buy_in
from src.models import Flat, Item, User


def test_add_item(
    client: TestClient, session: Session, flat_and_user_1: tuple[Flat, User]
):
    flat, user = flat_and_user_1

    response = client.post(
        "/items/",
        json={
            "name": "TV",
            "flat_id": flat.id,
            "is_bill": False,
            "initial_value": 1000,
            "purchase_date": "2025-01-01",
            "yearly_depreciation": 0.1,
            "minimum_value": 100,
            "minimum_value_pct": 0.1,
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "TV"
    db_item = session.get(Item, data["id"])
    if not db_item:
        raise Exception("Item was not pushed to db")
    assert db_item.id == data["id"]
    assert db_item.name == "TV"
    db_flat = session.get(Flat, flat.id)
    if not db_flat:
        raise Exception("Flat could not be loaded")
    assert db_item in db_flat.items


def test_fetch_item(client: TestClient, flat_user_item: tuple[Flat, User, Item]):
    flat, user, item = flat_user_item

    response = client.get(f"/items/{item.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item.id


def test_update_item(
    client: TestClient, session: Session, flat_user_item: tuple[Flat, User, Item]
):
    flat, user, item = flat_user_item
    new_name = "Toaster"

    response = client.patch(f"/items/{item.id}", json={"name": new_name})

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item.id
    assert data["name"] == new_name

    db_item = session.get(Item, item.id)
    if not db_item:
        raise Exception("Item not found in DB")
    assert db_item.name == new_name


def test_delete_item(
    client: TestClient, session: Session, flat_user_item: tuple[Flat, User, Item]
):
    flat, user, item = flat_user_item

    response = client.delete(f"/items/{item.id}")

    assert response.status_code == 200
    data = response.json()
    assert data == {"ok": True}
    db_item = session.get(Item, item.id)

    assert db_item is None


def test_add_user_to_item(
    client: TestClient,
    session: Session,
    flat_user_item: tuple[Flat, User, Item],
    user_2: User,
):
    flat, user, item = flat_user_item

    session.add(user_2)
    session.commit()
    session.refresh(user_2)
    response = client.patch(
        f"/items/{item.id}/add/{user_2.id}", params={"date": "2026-01-01"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["users"][1]["id"] == user_2.id

    session.refresh(user_2)
    assert item in user_2.items
    assert len(user_2.debts) == 1


def test_remove_user_from_item(
    client: TestClient,
    session: Session,
    flat_2_users_item: tuple[Flat, User, User, Item],
):
    flat, user_1, user_2, item = flat_2_users_item
    response = client.patch(
        f"/items/{item.id}/remove/{user_2.id}", params={"date": "2026-01-01"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 1

    db_user_2 = session.get(User, user_2.id)
    if not db_user_2:
        raise Exception("User could not be loaded form DB")
    assert item not in db_user_2.items
    assert len(db_user_2.items) == 0
    assert len(db_user_2.credits) == 1


def test_fetch_item_with_transactions(
    client: TestClient,
    session: Session,
    flat_user_item: tuple[Flat, User, Item],
    user_2: User,
):
    flat, user_1, item = flat_user_item
    session.add(user_2)
    session.commit()
    session.refresh(user_2)
    item_buy_in(session, user_2, item, item.purchase_date)

    response = client.get(f"/items/{item.id}/transactions/")

    assert response.status_code == 200

    data = response.json()
    assert len(data["transactions"]) == 1
    assert data["transactions"][0]["item_id"] == item.id
