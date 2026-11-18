from sqlalchemy import TIMESTAMP, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from ..base import Base


class PlanFeature(Base):
    """
    Represents a feature that is included in a plan.
    Args:
        - id (int): The unique identifier for this plan feature.
        - plan_id (int): The ID of the plan that this feature belongs to.
        - feature_id (int): The ID of the feature that is included in the plan.
        - usage_limit (int): The maximum number of times this feature can be used.
        - created_at (datetime): The timestamp when this feature was added to the plan.
    """

    __tablename__ = "plan_features"

    id: Mapped[int] = mapped_column(primary_key=True)

    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), index=True
    )

    feature_id: Mapped[int] = mapped_column(ForeignKey("features.id"), index=True)

    usage_limit: Mapped[int] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc_now
    )
