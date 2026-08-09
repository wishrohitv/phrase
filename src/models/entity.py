from sqlalchemy import Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.datetime_utc import datetime, datetime_utc_now

from .base import Base
from .enums import EntityType


class Entity(Base):
    __tablename__ = "entities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[EntityType] = mapped_column(Enum(EntityType))
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    imdb: Mapped[float] = mapped_column(Float(precision=2), nullable=True, index=True)
    os_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    language: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime_utc_now, onupdate=datetime_utc_now
    )
