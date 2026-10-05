from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, load_only

from database import get_db
from middlewares.auth_middleware import auth_middleware
from models import Subscription, Users
from utils.success import Success

user = APIRouter(prefix="/users")


@user.get("/subscription")
def subscription(
    session_user: Users = Depends(auth_middleware),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    subs = db.query(Subscription).filter_by(user_id=session_user.id).all()
    return subs


@user.get("/{user_id}")
def read_user(
    user_id: int,
    db: Session = Depends(get_db),  # noqa: B008
):
    user = (
        db.query(Users)
        .options(
            load_only(
                Users.id,
                Users.account_status,
                Users.name,
                Users.email,
                Users.is_verified,
                Users.provider,
                Users.created_at,
            )
        )
        .filter_by(id=user_id)
        .first()
    )

    return Success(
        data={
            "id": user.id,
            "account_status": user.account_status.value,
            "name": user.name,
            "email": user.email,
            "is_verified": user.is_verified,
            "provider": user.provider,
            "deleted_at": user.created_at.isoformat(),
        },
    )
