from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Users
from models.service import FeatureUsage, LLMUsage, PlanFeature, Subscription
from utils.errors import ForbiddenException

from .auth_middleware import auth_middleware
from .subscription_middleware import subscription_middleware


def chat_usage_middleware(
        subscription: Subscription = Depends(subscription_middleware),  # noqa: B008
    user: Users = Depends(auth_middleware),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Check allowed chat usage limit based on user's current plan

    Steps:
        - Check user's active plan (free | Paid)
        - Check chat limit token
        - Return True if under limit else False
    """
    # feature_id is chat: should be clear
    feature = (
        db.query(PlanFeature).filter_by(plan_id=subscription.plan_id, feature_id=2).first()
    )

    # Sum all token used
    total_chat_token = (
        db.query(func.sum(FeatureUsage.id))
        .filter_by(user_id=user.id, feature_id=2)
        .scalar()
    )

    llm_usage = (
        db.query(func.coalesce(func.sum(LLMUsage.total_tokens), 0))
        .filter_by(subscription_id=subscription.id)
        .scalar()
    )

    print("feature limit: ", feature.usage_limit)
    print("total_chat: ", total_chat_token)
    print("llm: ", llm_usage)

    if feature.usage_limit < llm_usage:
        raise ForbiddenException("Chat qouta used, please upgrade your plan")
