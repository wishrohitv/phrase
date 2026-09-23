from sqlalchemy import TIMESTAMP, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from ..base import Base
from ..enums import PlansBillingType, PlansStatus


class Plans(Base):
    """
    Plan table
    store free, medium, pro type
    of plans for users
    """

    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    price_amount: Mapped[float] = mapped_column(Numeric(scale=2))
    price_currency: Mapped[str] = mapped_column(String(20), default="INR")
    benifit: Mapped[str] = mapped_column(String(300))
    billing_type: Mapped[PlansBillingType] = mapped_column(Enum(PlansBillingType))
    status: Mapped[PlansStatus] = mapped_column(Enum(PlansStatus))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime_utc_now,
        onupdate=datetime_utc_now,
    )
