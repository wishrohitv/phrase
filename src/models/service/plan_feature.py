from sqlalchemy import TIMESTAMP, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from ..base import Base


class PlanFeature(Base):
    __tablename__ = "plan_features"

    id: Mapped[int] = mapped_column(primary_key=True)

    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), index=True)

    feature_id: Mapped[int] = mapped_column(ForeignKey("features.id"), index=True)

    usage_limit: Mapped[int] = mapped_column(Integer)
