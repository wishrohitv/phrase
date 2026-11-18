from uuid import UUID

from sqlalchemy import ARRAY, TIMESTAMP, VARCHAR, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from .base import Base


class Translation(Base):
    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(primary_key=True)
    content_uid: Mapped[UUID] = mapped_column(Uuid, index=True)
    phrase: Mapped[str] = mapped_column(Text)
    language_code: Mapped[str] = mapped_column(VARCHAR(10))

    usage: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    explanation: Mapped[list[str]] = mapped_column(ARRAY(Text),default=list)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime_utc_now,
        onupdate=datetime_utc_now,
    )
