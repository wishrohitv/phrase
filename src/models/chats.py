import uuid

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from .base import Base


class Chats(Base):
    __tablename__ = "chats"

    uid: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str | None] = mapped_column(String(70))  # title for very first time
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime_utc_now, onupdate=datetime_utc_now
    )
