from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from ..base import Base
from ..enums import SubscriptionStatus


class Subscription(Base):
    """
    Subcription model

    Args:
        user_id (int):
        plan_id (int):
        provider (str):
        provider_sub_id (str):
        status (SubscriptionStatus):
        quantity (int):
        current_period_start (datetime):
        current_period_end (datetime):
        cancel_at_period_end (bool):
        canceled_at (datetime):
        version (int):
        created_at (datetime):
        updated_at (datetime):
    Returns:
    Raises:

    """

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    provider: Mapped[str] = mapped_column(String)
    provider_sub_id: Mapped[str] = mapped_column(String)
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    current_period_start: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    current_period_end: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    cancel_at_period_end: Mapped[int] = mapped_column(Boolean)
    canceled_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)  # bumped on every change
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc_now
    )

    __table_args__ = (
        UniqueConstraint("provider", "provider_sub_id", name="unique_provider_sub_id"),
    )
