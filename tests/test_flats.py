from fastapi.testclient import TestClient
from sqlmodel import Session

from src.models import Flat, Item, User


def test_add_flat(client: TestClient, session: Session, user_1: User):
    session.add(user_1)
    session.commit()
    session.refresh(user_1)

    response = client.post(
        "/flats/", json={"name": "Olympus", "first_user_id": user_1.id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Olympus"
    print(data)
    assert data["users"][0]["id"] == user_1.id


def test_get_flats(client: TestClient, flat_and_user_1: tuple[Flat, User]):
    flat_1, user_1 = flat_and_user_1
    response = client.get("/flats/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == flat_1.name


def test_get_flat(client: TestClient, flat_and_user_1: tuple[Flat, User]):
    flat_1, user_1 = flat_and_user_1
    response = client.get(f"/flats/{flat_1.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == flat_1.name
    assert data["users"][0]["first_name"] == user_1.first_name


def test_update_flat(client: TestClient, flat_and_user_1: tuple[Flat, User]):
    flat_1, user_1 = flat_and_user_1

    response = client.patch(f"/flats/{flat_1.id}", json={"name": "Elysium"})

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Elysium"


def test_move_in_no_exclusion(
    client: TestClient,
    session: Session,
    flat_user_item: tuple[Flat, User, Item],
    user_2: User,
):
    flat, user_1, item_1 = flat_user_item
    assert len(flat.users) == 1
    assert len(flat.items) == 1
    session.add(user_2)
    session.commit()
    session.refresh(user_2)

    response = client.post(
        f"/flats/{flat.id}/move_in/{user_2.id}?date=2026-01-01", json=[]
    )
    assert response.status_code == 200

    db_user_2 = session.get(User, user_2.id)
    if not db_user_2:
        raise Exception("Coudn't find user")
    assert db_user_2.flat_id == flat.id
    assert len(db_user_2.debts) == 1

    db_flat = session.get(Flat, flat.id)
    if not db_flat:
        raise Exception("Couldn't find flat")
    assert db_user_2 in db_flat.users

    db_item = session.get(Item, item_1.id)
    if not db_item:
        raise Exception("Couldn't load item from DB")
    assert db_user_2 in db_item.users


def test_move_in_with_exclusion(
    client: TestClient,
    session: Session,
    flat_user_item: tuple[Flat, User, Item],
    user_2: User,
):
    flat, user_1, item_1 = flat_user_item
    assert len(flat.users) == 1
    assert len(flat.items) == 1
    session.add(user_2)
    session.commit()
    session.refresh(user_2)

    response = client.post(
        f"/flats/{flat.id}/move_in/{user_2.id}?date=2026-01-01", json=[item_1.id]
    )
    assert response.status_code == 200

    db_user_2 = session.get(User, user_2.id)
    if not db_user_2:
        raise Exception("Coudn't find user")
    assert db_user_2.flat_id == flat.id
    assert len(db_user_2.debts) == 0

    db_flat = session.get(Flat, flat.id)
    if not db_flat:
        raise Exception("Couldn't find flat")
    assert db_user_2 in db_flat.users

    db_item = session.get(Item, item_1.id)
    if not db_item:
        raise Exception("Couldn't load item from DB")
    assert db_user_2 not in db_item.users


def test_move_out(
    client: TestClient,
    session: Session,
    flat_2_users_item: tuple[Flat, User, User, Item],
):
    flat, user_1, user_2, item = flat_2_users_item
    assert len(flat.users) == 2
    assert len(flat.items) == 1
    response = client.post(f"/flats/{flat.id}/move_out/{user_2.id}?date=2026-01-01")
    assert response.status_code == 200

    db_user_2 = session.get(User, user_2.id)
    if not db_user_2:
        raise Exception("Couldn't find user")
    assert db_user_2.flat_id is None
    assert len(db_user_2.credits) == 1

    db_flat = session.get(Flat, flat.id)
    if not db_flat:
        raise Exception("Couldn't find flat")
    assert db_user_2 not in db_flat.users
