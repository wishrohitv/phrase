from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from .base import Base
from .enums import EntityType


class Title(Base):
    """
    Title is parent table that holds title and parent imdb and content type [movies, series, tvshows]. In case for movies parent imdb will be the same as child
    and its children database that will hold detailed data about content with unique id for each show's translations

    """

    __tablename__ = "titles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type: Mapped[EntityType] = mapped_column(Enum(EntityType))
    name: Mapped[str] = mapped_column(String(100))
    alt_name: Mapped[str] = mapped_column(JSONB(none_as_null=True))
    parent_imdb: Mapped[str] = mapped_column(String(22), index=True)
    # TODO: add language enum
    language: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(default=datetime_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime_utc_now, onupdate=datetime_utc_now
    )
