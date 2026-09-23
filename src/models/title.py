from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from .base import Base
from .enums import FeatureType


class Title(Base):
    """
    Title is parent table that holds title and parent imdb and content type [movies, series, tvshows]. In case for movies parent imdb will be the same as child
    and its children database that will hold detailed data about content with unique id for each show's translations

    """

    __tablename__ = "titles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type: Mapped[FeatureType] = mapped_column(Enum(FeatureType))
    title: Mapped[str] = mapped_column(String(100))
    imdb: Mapped[str] = mapped_column(String(22), index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime_utc_now, onupdate=datetime_utc_now
    )
