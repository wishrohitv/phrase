from sqlalchemy import TIMESTAMP, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.datetime_utc import datetime, datetime_utc_now

from .base import Base
from .enums import SubscriptionStatus


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    plan: Mapped[int] = mapped_column(ForeignKey("plans.id"), nullable=False)
    plan_status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus))
    next_due: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    created_at: [datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc_now
    )
