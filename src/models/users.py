from sqlalchemy import TIMESTAMP, Boolean, Enum, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.datetime_utc import datetime, datetime_utc_now

from .base import Base
from .enums import AccountStatus, ProviderType, UserRole


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=True)
    password: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)
    provider: Mapped[ProviderType] = mapped_column(
        Enum(ProviderType), default=ProviderType.LOCAL
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    account_status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus), default=AccountStatus.ACTIVE
    )
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    suspension_start_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    suspension_reason: Mapped[str] = mapped_column(String(255), nullable=True)
    suspension_end_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime_utc_now,
        onupdate=datetime_utc_now,
    )
