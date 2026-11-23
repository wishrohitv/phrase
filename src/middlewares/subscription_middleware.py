from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


async def subscription_middleware(
    user: Users = Depends(auth_middleware),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Subscription:
    """
    This middleware checks if the user has an active subscription
    """

    subs = await db.scalar(
        select(Subscription).filter_by(
            user_id=user.id, status=SubscriptionStatus.ACTIVE
        )
    )

    if not subs:
        raise ForbiddenException("An active subscription is required")

    return subs
