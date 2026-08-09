from sqlalchemy import ARRAY, JSON, TIMESTAMP, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.datetime_utc import datetime, datetime_utc_now

from .base import Base
from .enums import Language


class Translation(Base):
    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), nullable=False)
    phrase: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[Language] = mapped_column(Enum(Language), nullable=False)
    usage: Mapped[str] = mapped_column(ARRAY(Text))
    explaination: Mapped[JSON] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime_utc_now,
        onupdate=datetime_utc_now,
    )
