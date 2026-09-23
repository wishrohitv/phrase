from sqlalchemy import TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from .base import Base


class Subscription_history(Base):
    __tablename__ = "subscription_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    subscription: [int] = mapped_column(ForeignKey("subscription.id"))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc_now
    )
