import uuid

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from .base import Base


class LLMUsage(Base):
    __tablename__ = "llm_usage"
    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscription"))
    message_uid: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # request_id
    operation: Mapped[int] = mapped_column(
        ForeignKey("features.id")
    )  # phrase_explanation / sentence_generation ...
    provider: Mapped[str] = mapped_column(String(100))  # OpenRouter / NVIDIA / etc.
    model: Mapped[str] = mapped_column(String(100))
    prompt_tokens: Mapped[int] = mapped_column(Integer)
    completion_tokens: Mapped[int] = mapped_column(Integer)
    reasoning_tokens: Mapped[int] = mapped_column(Integer)
    total_tokens: Mapped[int] = mapped_column(Integer)
    estimated_cost: Mapped[float] = mapped_column(Numeric(scale=2))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc_now
    )
