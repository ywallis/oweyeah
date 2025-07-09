import uuid
from datetime import date, datetime

from pydantic import BaseModel
from sqlalchemy import String
from sqlmodel import Field, Relationship, SQLModel

from src.timestamps import TimestampMixin


class AppVersion(BaseModel):
    version: str


class TokenUrl(BaseModel):
    url: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class Token(BaseModel):
    token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    id: str | None = None


class RefreshTokenBase(TimestampMixin, SQLModel):
    token: str
    user_email: str = Field(foreign_key="user.email")
    user_id: str = Field(foreign_key="user.id", sa_type=String)
    expiration: datetime
    valid: bool


class RefreshToken(RefreshTokenBase, table=True):
    id: str | None = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, sa_type=String
    )


class FlatBase(TimestampMixin, SQLModel):
    name: str


class Flat(FlatBase, table=True):
    id: str | None = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, sa_type=String
    )
    users: list["User"] = Relationship(back_populates="flat")
    items: list["Item"] = Relationship(back_populates="flat")


class FlatPublic(FlatBase):
    id: str


class FlatPublicWithUsers(FlatPublic):
    users: list["UserPublic"] | None = Field(default_factory=list)


class FlatCreate(SQLModel):
    name: str
    first_user_id: str


class FlatUpdate(SQLModel):
    name: str | None = None


class UserItems(SQLModel, table=True):
    user_id: str | None = Field(foreign_key="user.id", primary_key=True, sa_type=String)
    item_id: str | None = Field(foreign_key="item.id", primary_key=True, sa_type=String)


class UserItemsPublic(SQLModel):
    user_id: str
    item_id: str


class UserBase(TimestampMixin, SQLModel):
    first_name: str
    last_name: str
    email: str = Field(unique=True)
    flat_id: str | None = Field(default=None, foreign_key="flat.id", sa_type=String)
    active: bool = Field(default=True)


class User(UserBase, table=True):
    id: str | None = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
        sa_type=String,
    )
    hashed_password: str | None = Field(default=None)
    flat: Flat | None = Relationship(back_populates="users")
    items: list["Item"] = Relationship(back_populates="users", link_model=UserItems)
    credits: list["Transaction"] = Relationship(
        back_populates="creditor",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.creditor_id]"},
    )
    debts: list["Transaction"] = Relationship(
        back_populates="debtor",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.debtor_id]"},
    )


class UserPublic(UserBase):
    id: str


class UserPublicWithTransactions(UserBase):
    id: str
    credits: list["Transaction"] | None = Field(default_factory=list)
    debts: list["Transaction"] | None = Field(default_factory=list)


class UserPublicWithItems(UserPublic):
    items: list["Item"] | None = Field(default_factory=list)


class UserCreate(SQLModel):
    first_name: str
    last_name: str
    email: str = Field(unique=True)
    flat_id: str | None = Field(default=None, foreign_key="flat.id", sa_type=String)
    password: str


class UserCreateNP(SQLModel):
    first_name: str
    last_name: str
    email: str = Field(unique=True)
    flat_id: str | None = Field(default=None, foreign_key="flat.id", sa_type=String)


class UserUpdate(SQLModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    password: str | None = None
    flat_id: str | None = Field(default=None, sa_type=String)


class ItemBase(TimestampMixin, SQLModel):
    name: str = Field(schema_extra={"examples": ["TV"]})
    flat_id: str | None = Field(
        default=None,
        foreign_key="flat.id",
        schema_extra={"examples": [1]},
        sa_type=String,
    )
    is_bill: bool
    initial_value: float = Field(schema_extra={"examples": [1000.0]})
    purchase_date: date = Field(schema_extra={"examples": ["2025-01-13"]})
    yearly_depreciation: float = Field(schema_extra={"examples": [0.1]})
    minimum_value: float | None = Field(schema_extra={"examples": [100.0]})
    minimum_value_pct: float | None = Field(schema_extra={"examples": [0.1]})


class Item(ItemBase, table=True):
    id: str | None = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, sa_type=String
    )
    flat: Flat = Relationship(back_populates="items")
    users: list[User] = Relationship(back_populates="items", link_model=UserItems)
    transactions: list["Transaction"] = Relationship(back_populates="item")


class ItemPublic(ItemBase):
    id: str


class ItemPublicWithUsers(ItemPublic):
    users: list[UserPublic] = []


class ItemPublicWithTransactions(ItemPublic):
    transactions: list["TransactionPublic"] = []


class ItemCreate(SQLModel):
    name: str = Field(schema_extra={"examples": ["TV"]})
    flat_id: str | None = Field(
        default=None,
        foreign_key="flat.id",
        schema_extra={"examples": [1]},
        sa_type=String,
    )
    is_bill: bool
    initial_value: float = Field(schema_extra={"examples": [1000.0]})
    purchase_date: date = Field(schema_extra={"examples": ["2025-01-13"]})
    yearly_depreciation: float = Field(schema_extra={"examples": [0.1]})
    minimum_value: float | None = Field(schema_extra={"examples": [100.0]})
    minimum_value_pct: float | None = Field(schema_extra={"examples": [0.1]})


class ItemUpdate(SQLModel):
    name: str | None = None
    is_bill: bool | None = None
    initial_value: float | None = None
    purchase_date: datetime | None = None
    yearly_depreciation: float | None = None
    minimum_value: float | None = None
    minimum_value_pct: float | None = None


class TransactionBase(TimestampMixin, SQLModel):
    creditor_id: str = Field(foreign_key="user.id", sa_type=String)
    debtor_id: str = Field(foreign_key="user.id", sa_type=String)
    item_id: str = Field(foreign_key="item.id", sa_type=String)
    amount: float
    paid: bool


class Transaction(TransactionBase, table=True):
    id: str | None = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, sa_type=String
    )
    creditor: User = Relationship(
        back_populates="credits",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.creditor_id]"},
    )
    debtor: User = Relationship(
        back_populates="debts",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.debtor_id]"},
    )
    item: Item = Relationship(back_populates="transactions")


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(SQLModel):
    paid: bool


class TransactionPublic(TransactionBase):
    id: str


class TransactionPublicWithUsers(TransactionBase):
    id: str
    creditor: UserPublic
    debtor: UserPublic
