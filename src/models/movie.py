import uuid

from sqlalchemy import VARCHAR, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from .base import Base


class Movie(Base):
    __tablename__ = "movies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_imdb: Mapped[str] = mapped_column(VARCHAR(16), index=True)
    imdb: Mapped[str] = mapped_column(VARCHAR(16), index=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id"))
    unique_id: Mapped[str] = mapped_column(Uuid, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(default=datetime_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime_utc_now, onupdate=datetime_utc_now
    )
