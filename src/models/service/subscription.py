from sqlalchemy import TIMESTAMP, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from ..base import Base
from ..enums import SubscriptionStatus


class Subscription(Base):
    """
    Subcription model

    Args:
        id (int): Auto generated primary key
        user_id (int): Primary key of users
        plan (int): Primary key of plans
        status (Enum(ACITVE|SUSSPENED|EXPIRED)): Subcription status
        next_due (datetime): Next payment due date
    Returns:
    Raises:

    """
    __tablename__ = "subscription"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus))
    next_due: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc_now
    )
