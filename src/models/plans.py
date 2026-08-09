from sqlalchemy import TIMESTAMP, Enum, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from .base import Base
from .enums import PlansStatus


class Plans(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    benifit: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PlansStatus] = mapped_column(Enum(PlansStatus))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime_utc_now,
        onupdate=datetime_utc_now,
    )
