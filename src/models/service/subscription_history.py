from sqlalchemy import (
    TIMESTAMP,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from ..base import Base
from ..enums import ActorType, EventType, Reason


class SubscriptionHistory(Base):
    __tablename__ = "subscription_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscriptions.id"), index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True)
    )  # when it actually happened at provider
    recorded_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc_now
    )  # when we learned about it
    event_type: Mapped[EventType] = mapped_column(Enum(EventType))

    from_status: Mapped[str | None] = mapped_column(String)
    to_status: Mapped[str | None] = mapped_column(String)
    from_price_id: Mapped[str | None] = mapped_column(String)
    to_price_id: Mapped[str | None] = mapped_column(String)
    from_quantity: Mapped[int | None] = mapped_column(Integer)
    to_quantity: Mapped[int | None] = mapped_column(Integer)
    reason: Mapped[Reason] = mapped_column(Enum(Reason))
    actor_type: Mapped[ActorType] = mapped_column(
        Enum(ActorType), default=ActorType.SYSTEM
    )
    actor_id: Mapped[str | None] = mapped_column(String)
    effective_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True)
    )  # for scheduled changes (cancel at period end)
    provider_event_id: Mapped[str] = mapped_column(
        String
    )  # webhook idempotency, e.g. evt_xxx
    event_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc_now
    )

    __table_args__ = (
        Index("idx_subscription_history_provider_event_id", "provider_event_id"),
    )
