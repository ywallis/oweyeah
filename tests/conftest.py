from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.authentication import get_current_user
from src.main import app
from src.models import Flat, Item, User
from src.utils import get_session


@pytest.fixture(name="session")
def session_fixture():
    """
    Fixture creating an in-memory SQLite session for testing.
    """
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session, user_1: User):
    """
    Fixture creating a TestClient with overridden dependencies for session and current_user.
    """
    def get_session_override():
        return session

    def get_current_user_override():
        return user_1

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_current_user_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def user_1():
    """
    Fixture creating the first test user (Yann).
    """
    user = User(
        first_name="Yann",
        last_name="Wallis",
        email="y.w@g.c",
        flat_id=None,
        hashed_password="pw",
    )
    return user


@pytest.fixture
def user_2():
    """
    Fixture creating the second test user (Ilias).
    """
    user = User(
        first_name="Ilias",
        last_name="Trichopoulos",
        email="i.t@g.c",
        flat_id=None,
        hashed_password="pw",
    )
    return user


@pytest.fixture
def flat_1():
    """
    Fixture creating a test flat (Olympus).
    """
    flat = Flat(name="Olympus", users=[], items=[])
    return flat


@pytest.fixture
def item_1():
    """
    Fixture creating a test item (TV).
    """
    item = Item(
        name="TV",
        flat_id=None,
        is_bill=False,
        initial_value=1000.0,
        purchase_date=datetime.strptime("2025-01-01", "%Y-%m-%d").date(),
        yearly_depreciation=0.2,
        minimum_value=None,
        minimum_value_pct=None,
    )
    return item


@pytest.fixture
def item_2():
    """
    Fixture creating a test item with a minimum value.
    """
    item = Item(
        name="TV",
        flat_id=None,
        is_bill=False,
        initial_value=1000.0,
        purchase_date=datetime.strptime("2025-01-01", "%Y-%m-%d").date(),
        yearly_depreciation=0.2,
        minimum_value=900,
        minimum_value_pct=None,
    )
    return item


@pytest.fixture
def item_3():
    """
    Fixture creating a test item with a minimum value percentage.
    """
    item = Item(
        name="TV",
        flat_id=None,
        is_bill=False,
        initial_value=1000.0,
        purchase_date=datetime.strptime("2025-01-01", "%Y-%m-%d").date(),
        yearly_depreciation=0.2,
        minimum_value=None,
        minimum_value_pct=0.95,
    )
    return item


@pytest.fixture
def flat_and_user_1(session: Session, flat_1: Flat, user_1: User):
    """
    Fixture associating user_1 with flat_1 in the database.
    """
    session.add(user_1)
    session.commit()
    session.refresh(user_1)
    flat_1.users.append(user_1)
    session.add(flat_1)
    session.commit()
    session.refresh(flat_1)
    return flat_1, user_1


@pytest.fixture
def flat_user_item(session: Session, flat_1: Flat, user_1: User, item_1: Item):
    """
    Fixture associating user_1 and item_1 with flat_1 in the database.
    """
    # Add and persist user
    session.add(user_1)
    session.commit()
    session.refresh(user_1)

    # Associate user with flat
    flat_1.users.append(user_1)
    session.add(flat_1)
    session.commit()
    session.refresh(flat_1)

    # Assign all users of the flat to the item
    item_1.flat_id = flat_1.id
    item_1.users = flat_1.users
    session.add(item_1)
    session.commit()
    session.refresh(item_1)

    # Refresh linked objects for consistency
    session.refresh(user_1)

    return flat_1, user_1, item_1


@pytest.fixture
def flat_2_users_item(
    session: Session, flat_1: Flat, user_1: User, user_2: User, item_1: Item
):
    """
    Fixture associating user_1, user_2, and item_1 with flat_1 in the database.
    """
    # Add and persist user
    session.add(user_1)
    session.add(user_2)
    session.commit()
    session.refresh(user_1)
    session.refresh(user_2)

    # Associate user with flat
    flat_1.users.append(user_1)
    flat_1.users.append(user_2)
    session.add(flat_1)
    session.commit()
    session.refresh(flat_1)

    # Assign all users of the flat to the item
    item_1.flat_id = flat_1.id
    item_1.users = flat_1.users
    session.add(item_1)
    session.commit()
    session.refresh(item_1)

    # Refresh linked objects for consistency
    session.refresh(user_1)

    return flat_1, user_1, user_2, item_1
