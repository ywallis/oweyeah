import uuid
from datetime import date, datetime

from pydantic import BaseModel
from sqlalchemy import String
from sqlmodel import Field, Relationship, SQLModel

from src.timestamps import TimestampMixin


class AppVersion(BaseModel):
    """
    Represents the application version.

    Attributes
    ----------
    version : str
        The version string of the application.
    """
    version: str


class TokenUrl(BaseModel):
    """
    Represents a URL containing a token.

    Attributes
    ----------
    url : str
        The URL string.
    """
    url: str


class ResetPasswordRequest(BaseModel):
    """
    Represents a request to reset a password.

    Attributes
    ----------
    token : str
        The reset token.
    new_password : str
        The new password to set.
    """
    token: str
    new_password: str


class Token(BaseModel):
    """
    Represents an access token.

    Attributes
    ----------
    token : str
        The access token string.
    token_type : str
        The type of the token (e.g., "bearer").
    """
    token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    """
    Represents a request to refresh an access token.

    Attributes
    ----------
    refresh_token : str
        The refresh token string.
    """
    refresh_token: str


class TokenData(BaseModel):
    """
    Represents data extracted from a token.

    Attributes
    ----------
    id : str | None
        The user ID associated with the token.
    """
    id: str | None = None


class RefreshTokenBase(TimestampMixin, SQLModel):
    """
    Base model for a refresh token.

    Attributes
    ----------
    token : str
        The refresh token string.
    user_email : str
        The email of the user associated with the token.
    user_id : str
        The ID of the user associated with the token.
    expiration : datetime
        The expiration date and time of the token.
    valid : bool
        Whether the token is valid.
    """
    token: str
    user_email: str = Field(foreign_key="user.email")
    user_id: str = Field(foreign_key="user.id", sa_type=String)
    expiration: datetime
    valid: bool


class RefreshToken(RefreshTokenBase, table=True):
    """
    Database model for a refresh token.

    Attributes
    ----------
    id : str | None
        The unique identifier of the refresh token.
    """
    id: str | None = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, sa_type=String
    )


class FlatBase(TimestampMixin, SQLModel):
    """
    Base model for a flat.

    Attributes
    ----------
    name : str
        The name of the flat.
    """
    name: str


class Flat(FlatBase, table=True):
    """
    Database model for a flat.

    Attributes
    ----------
    id : str | None
        The unique identifier of the flat.
    users : list[User]
        List of users belonging to the flat.
    items : list[Item]
        List of items belonging to the flat.
    """
    id: str | None = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, sa_type=String
    )
    users: list["User"] = Relationship(back_populates="flat")
    items: list["Item"] = Relationship(back_populates="flat")


class FlatPublic(FlatBase):
    """
    Public model for a flat.

    Attributes
    ----------
    id : str
        The unique identifier of the flat.
    """
    id: str


class FlatPublicWithUsers(FlatPublic):
    """
    Public model for a flat including its users.

    Attributes
    ----------
    users : list[UserPublic] | None
        List of public user profiles in the flat.
    """
    users: list["UserPublic"] | None = Field(default_factory=list)


class FlatCreate(SQLModel):
    """
    Model for creating a new flat.

    Attributes
    ----------
    name : str
        The name of the flat.
    first_user_id : str
        The ID of the first user to be added to the flat.
    """
    name: str
    first_user_id: str


class FlatUpdate(SQLModel):
    """
    Model for updating a flat.

    Attributes
    ----------
    name : str | None
        The new name of the flat.
    """
    name: str | None = None


class UserItems(SQLModel, table=True):
    """
    Association model between users and items.

    Attributes
    ----------
    user_id : str | None
        The ID of the user.
    item_id : str | None
        The ID of the item.
    """
    user_id: str | None = Field(foreign_key="user.id", primary_key=True, sa_type=String)
    item_id: str | None = Field(foreign_key="item.id", primary_key=True, sa_type=String)


class UserItemsPublic(SQLModel):
    """
    Public model for user-item association.

    Attributes
    ----------
    user_id : str
        The ID of the user.
    item_id : str
        The ID of the item.
    """
    user_id: str
    item_id: str


class UserBase(TimestampMixin, SQLModel):
    """
    Base model for a user.

    Attributes
    ----------
    first_name : str
        The first name of the user.
    last_name : str
        The last name of the user.
    email : str
        The email address of the user.
    flat_id : str | None
        The ID of the flat the user belongs to.
    active : bool
        Whether the user account is active.
    """
    first_name: str
    last_name: str
    email: str = Field(unique=True)
    flat_id: str | None = Field(default=None, foreign_key="flat.id", sa_type=String)
    active: bool = Field(default=True)


class User(UserBase, table=True):
    """
    Database model for a user.

    Attributes
    ----------
    id : str | None
        The unique identifier of the user.
    hashed_password : str | None
        The hashed password of the user.
    flat : Flat | None
        The flat the user belongs to.
    items : list[Item]
        List of items associated with the user.
    credits : list[Transaction]
        List of transactions where the user is the creditor.
    debts : list[Transaction]
        List of transactions where the user is the debtor.
    """
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
    """
    Public model for a user.

    Attributes
    ----------
    id : str
        The unique identifier of the user.
    """
    id: str


class UserPublicWithTransactions(UserBase):
    """
    Public model for a user including their transactions.

    Attributes
    ----------
    id : str
        The unique identifier of the user.
    credits : list[Transaction] | None
        List of transactions where the user is the creditor.
    debts : list[Transaction] | None
        List of transactions where the user is the debtor.
    """
    id: str
    credits: list["Transaction"] | None = Field(default_factory=list)
    debts: list["Transaction"] | None = Field(default_factory=list)


class UserPublicWithItems(UserPublic):
    """
    Public model for a user including their items.

    Attributes
    ----------
    items : list[Item] | None
        List of items associated with the user.
    """
    items: list["Item"] | None = Field(default_factory=list)


class UserCreate(SQLModel):
    """
    Model for creating a new user with password.

    Attributes
    ----------
    first_name : str
        The first name of the user.
    last_name : str
        The last name of the user.
    email : str
        The email address of the user.
    flat_id : str | None
        The ID of the flat the user belongs to.
    password : str
        The password for the user account.
    """
    first_name: str
    last_name: str
    email: str = Field(unique=True)
    flat_id: str | None = Field(default=None, foreign_key="flat.id", sa_type=String)
    password: str


class UserCreateNP(SQLModel):
    """
    Model for creating a new user without a password (No Password).

    Attributes
    ----------
    first_name : str
        The first name of the user.
    last_name : str
        The last name of the user.
    email : str
        The email address of the user.
    flat_id : str | None
        The ID of the flat the user belongs to.
    """
    first_name: str
    last_name: str
    email: str = Field(unique=True)
    flat_id: str | None = Field(default=None, foreign_key="flat.id", sa_type=String)


class UserUpdate(SQLModel):
    """
    Model for updating a user.

    Attributes
    ----------
    first_name : str | None
        The new first name of the user.
    last_name : str | None
        The new last name of the user.
    email : str | None
        The new email address of the user.
    password : str | None
        The new password for the user.
    flat_id : str | None
        The new flat ID for the user.
    """
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    password: str | None = None
    flat_id: str | None = Field(default=None, sa_type=String)


class ItemBase(TimestampMixin, SQLModel):
    """
    Base model for an item.

    Attributes
    ----------
    name : str
        The name of the item.
    flat_id : str | None
        The ID of the flat the item belongs to.
    is_bill : bool
        Whether the item is a bill.
    initial_value : float
        The initial value of the item.
    purchase_date : date
        The date the item was purchased.
    yearly_depreciation : float
        The yearly depreciation rate of the item.
    minimum_value : float | None
        The minimum value of the item.
    minimum_value_pct : float | None
        The minimum value percentage of the item.
    """
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
    """
    Database model for an item.

    Attributes
    ----------
    id : str | None
        The unique identifier of the item.
    flat : Flat
        The flat the item belongs to.
    users : list[User]
        List of users associated with the item.
    transactions : list[Transaction]
        List of transactions associated with the item.
    """
    id: str | None = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, sa_type=String
    )
    flat: Flat = Relationship(back_populates="items")
    users: list[User] = Relationship(back_populates="items", link_model=UserItems)
    transactions: list["Transaction"] = Relationship(back_populates="item")


class ItemPublic(ItemBase):
    """
    Public model for an item.

    Attributes
    ----------
    id : str
        The unique identifier of the item.
    """
    id: str


class ItemPublicWithUsers(ItemPublic):
    """
    Public model for an item including its users.

    Attributes
    ----------
    users : list[UserPublic]
        List of users associated with the item.
    """
    users: list[UserPublic] = []


class ItemPublicWithTransactions(ItemPublic):
    """
    Public model for an item including its transactions.

    Attributes
    ----------
    transactions : list[TransactionPublic]
        List of transactions associated with the item.
    """
    transactions: list["TransactionPublic"] = []


class ItemCreate(SQLModel):
    """
    Model for creating a new item.

    Attributes
    ----------
    name : str
        The name of the item.
    flat_id : str | None
        The ID of the flat the item belongs to.
    is_bill : bool
        Whether the item is a bill.
    initial_value : float
        The initial value of the item.
    purchase_date : date
        The date the item was purchased.
    yearly_depreciation : float
        The yearly depreciation rate of the item.
    minimum_value : float | None
        The minimum value of the item.
    minimum_value_pct : float | None
        The minimum value percentage of the item.
    """
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
    """
    Model for updating an item.

    Attributes
    ----------
    name : str | None
        The new name of the item.
    is_bill : bool | None
        Whether the item is a bill.
    initial_value : float | None
        The new initial value of the item.
    purchase_date : datetime | None
        The new purchase date of the item.
    yearly_depreciation : float | None
        The new yearly depreciation rate of the item.
    minimum_value : float | None
        The new minimum value of the item.
    minimum_value_pct : float | None
        The new minimum value percentage of the item.
    """
    name: str | None = None
    is_bill: bool | None = None
    initial_value: float | None = None
    purchase_date: datetime | None = None
    yearly_depreciation: float | None = None
    minimum_value: float | None = None
    minimum_value_pct: float | None = None


class TransactionBase(TimestampMixin, SQLModel):
    """
    Base model for a transaction.

    Attributes
    ----------
    creditor_id : str
        The ID of the creditor user.
    debtor_id : str
        The ID of the debtor user.
    item_id : str
        The ID of the item associated with the transaction.
    amount : float
        The amount of the transaction.
    paid : bool
        Whether the transaction has been paid.
    """
    creditor_id: str = Field(foreign_key="user.id", sa_type=String)
    debtor_id: str = Field(foreign_key="user.id", sa_type=String)
    item_id: str = Field(foreign_key="item.id", sa_type=String)
    amount: float
    paid: bool


class Transaction(TransactionBase, table=True):
    """
    Database model for a transaction.

    Attributes
    ----------
    id : str | None
        The unique identifier of the transaction.
    creditor : User
        The user who is the creditor.
    debtor : User
        The user who is the debtor.
    item : Item
        The item associated with the transaction.
    """
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
    """
    Model for creating a new transaction.
    """
    pass


class TransactionUpdate(SQLModel):
    """
    Model for updating a transaction.

    Attributes
    ----------
    paid : bool
        Whether the transaction has been paid.
    """
    paid: bool


class TransactionPublic(TransactionBase):
    """
    Public model for a transaction.

    Attributes
    ----------
    id : str
        The unique identifier of the transaction.
    """
    id: str


class TransactionPublicWithUsers(TransactionBase):
    """
    Public model for a transaction including creditor and debtor details.

    Attributes
    ----------
    id : str
        The unique identifier of the transaction.
    creditor : UserPublic
        The creditor user profile.
    debtor : UserPublic
        The debtor user profile.
    """
    id: str
    creditor: UserPublic
    debtor: UserPublic
