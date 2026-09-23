from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from ..base import Base
from ..enums import FeatureUnit


class Feature(Base):
    """
    Feature/Services offered by the platform

    (e.g. translations, chat, phrase_explanation, phrase_explanation)
    """

    __tablename__ = "features"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[str] = mapped_column(
        Integer
    )  # e.g. 'request: 1', 'token: 100', 'translation: 500'
    unit: Mapped[FeatureUnit] = mapped_column(ForeignKey("feature_units.name"))
    created_at: Mapped[datetime] = mapped_column(default=datetime_utc_now)
