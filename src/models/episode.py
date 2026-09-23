from sqlalchemy import VARCHAR, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from .base import Base


class Episode(Base):
    __tablename__ = "episodes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_imdb: Mapped[str] = mapped_column(VARCHAR(16), index=True)
    imdb_id: Mapped[str] = mapped_column(VARCHAR(16), index=True)
    title: Mapped[str] = mapped_column(VARCHAR(300))
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id"))
    year: Mapped[int | None] = mapped_column(Integer)
    season_number: Mapped[int] = mapped_column(Integer)
    episode_number: Mapped[int] = mapped_column(Integer)
    unique_id: Mapped[str] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(default=datetime_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime_utc_now, onupdate=datetime_utc_now
    )
