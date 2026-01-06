from datetime import datetime, timezone

from sqlalchemy import event
from sqlmodel import Field, Session, SQLModel


class TimestampMixin(SQLModel):
    """
    Mixin that provides created_at and updated_at timestamps.

    Attributes
    ----------
    created_at : datetime
        The timestamp when the record was created.
    updated_at : datetime
        The timestamp when the record was last updated.
    """

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )


@event.listens_for(Session, "before_flush")
def update_timestamp(session, _flush_context, _instances):
    """
    SQLAlchemy event listener to update the `updated_at` field before flush.

    Parameters
    ----------
    session : Session
        The database session.
    _flush_context
        The flush context (unused).
    _instances
        The instances (unused).
    """
    for obj in session.dirty:
        if isinstance(obj, SQLModel) and hasattr(obj, "updated_at"):
            obj.updated_at = datetime.now(timezone.utc)
