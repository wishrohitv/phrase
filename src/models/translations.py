from uuid import UUID

from sqlalchemy import ARRAY, TIMESTAMP, Enum, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from .base import Base
from .enums import Language


class Translation(Base):
    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(primary_key=True)
    content_uid: Mapped[UUID] = mapped_column(Uuid, index=True)
    phrase: Mapped[str] = mapped_column(Text)
    language: Mapped[Language] = mapped_column(Enum(Language))

    usage: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    explanation: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime_utc_now,
        onupdate=datetime_utc_now,
    )
