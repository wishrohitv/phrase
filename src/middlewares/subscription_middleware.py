from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from middlewares import auth_middleware
from models import SubscriptionStatus, Users
from models.service import Subscription
from utils.errors import ForbiddenException

"""
FastAPI caches dependency results per request by default, 
so if both dependencies use the same auth_middleware, 
it normally executes only once for that request.
"""


def subscription_middleware(
    user: Users = Depends(auth_middleware),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> Subscription:
    """
    This middleware checks if the user has an active subscription
    """

    plan = (
        db.query(Subscription)
        .filter_by(user_id=user.id, status=SubscriptionStatus.ACTIVE)
        .first()
    )

    if not plan:
        raise ForbiddenException("An active subscription is required")

    return plan
