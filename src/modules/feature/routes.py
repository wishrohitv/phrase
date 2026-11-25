"""
This route is for app's service and to manage feature

"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middlewares.auth_middleware import auth_middleware
from models import PlansBillingType, PlansStatus, UserRole, Users
from models.service import Feature, PlanFeature, Plans, ProviderProduct
from utils.errors import BadRequestException, NotFoundException
from utils.success import SuccessSchema

from .pydantic_schema import (
    EditPlansSchema,
    FeatureResponseSchema,
    FeatureSchema,
    PlanFeaturePlanFeatureResponseSchema,
    PlanFeatureResponseSchema,
    PlanFeatureSchema,
    PlanProviderResponseSchema,
    PlanProviderSchema,
    PlansResponseSchema,
    PlansSchema,
)

feature = APIRouter(tags=["Feature"])
logger = logging.getLogger(__name__)


@feature.get(
    "/feature",
    response_model=SuccessSchema[list[FeatureResponseSchema]],
    status_code=200,
)
async def get_feature(
    db: AsyncSession = Depends(get_db),  # noqa: B008
    session_user: Users = Depends(auth_middleware),  # noqa: B008
):
    """
    Feature route which lists all registered application's feature
    The feature going to be consumed by users
    """
    if session_user.role != UserRole.ADMIN:
        raise BadRequestException("Invalid route")
    _features = await db.scalars(select(Feature))

    return SuccessSchema(
        data=[FeatureResponseSchema.model_validate(_feature) for _feature in _features]
    )


@feature.post(
    "/feature",
    response_model=SuccessSchema[FeatureSchema],
    status_code=201,
)
async def register_feature(
    feature_data: FeatureSchema,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    session_user: Users = Depends(auth_middleware),  # noqa: B008
):
    """
    Feature register route,The Feature to be registered by admin

    Args:
        - feature_data( FeatureSchema ): Feature schema has feature_name(str), description(str), quantity(int), unit(Enum)
    Returns:
        - FeatureSchema: feature_name(str), description(str), quantity(int), unit(Enum), created_at
    """
    if session_user.role != UserRole.ADMIN:
        raise BadRequestException("Invalid route")
    new_feature = Feature(
        name=feature_data.name,
        description=feature_data.description,
        quantity=feature_data.quantity,
        unit=feature_data.unit,
    )
    db.add(new_feature)
    await db.commit()
    await db.refresh(new_feature)
    return SuccessSchema(data=FeatureSchema.model_validate(new_feature))


@feature.get(
    "/plan",
    response_model=SuccessSchema[list[PlansResponseSchema]],
    status_code=200,
)
async def get_plans(
    status: PlansStatus = PlansStatus.ACTIVE,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    session_user: Users = Depends(auth_middleware),  # noqa: B008
):
    """
    List all registered active or discontinued plans

    Args:
        - status (Enum(active|discountinued)): default is `active`
    Returns:
        - SuccessSchema[list[PlansResponseSchema]:
    """
    if session_user.role != UserRole.ADMIN:
        raise BadRequestException("Invalid route")
    plans = await db.scalars(select(Plans).filter_by(status=status))
    data = [PlansResponseSchema.model_validate(plan) for plan in plans]

    return SuccessSchema(data=data, message="Fetched plans successfully")


@feature.post(
    "/plan",
    response_model=SuccessSchema[PlansResponseSchema],
    status_code=201,
)
async def new_plan(
    plans_data: PlansSchema,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    session_user: Users = Depends(auth_middleware),  # noqa: B008
):
    if session_user.role != UserRole.ADMIN:
        raise BadRequestException("Invalid route")
    new_plan = Plans(
        name=plans_data.name,
        author_id=session_user.id,
        price_amount=plans_data.price_amount,
        benefit=plans_data.benefit,
        status=plans_data.status,
        plan_billing_type=plans_data.plan_billing_type,
    )

    db.add(new_plan)
    await db.commit()
    return SuccessSchema(
        data=PlansResponseSchema.validate(new_plan),
        message="Plans added successfully",
    )


@feature.patch("/plan", response_model=SuccessSchema, status_code=201)
async def edit_plan(
    plans_data: EditPlansSchema,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    session_user: Users = Depends(auth_middleware),  # noqa: B008
):
    if session_user.role != UserRole.ADMIN:
        raise BadRequestException("Invalid route")

    plan = await db.scalar(select(Plans).filter_by(id=plans_data.id))
    if not plan:
        raise NotFoundException("Plan not found")
    if plans_data.price_amount is not None:
        plan.price_amount = plans_data.price_amount
    if plans_data.benefit is not None:
        plan.benefit = plans_data.benefit
    if plans_data.status:
        plan.status = plans_data.status

    await db.commit()
    return SuccessSchema(
        message="Plans updated successfully",
    )


@feature.delete("/plan/{plan_id}", response_model=SuccessSchema, status_code=200)
async def delete_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    session_user: Users = Depends(auth_middleware),  # noqa: B008
):
    """
    Delete plan,
    NOTE: Plan row can only be deleted if it is not used by subscription rows

    Plan row and associated plan_feature row will be deleted
    Args:
        - plan_id(int): Plans id
    Returns:
        - SuccessSchema
    """
    if session_user.role != UserRole.ADMIN:
        raise BadRequestException("Invalid route")

    plan = await db.scalar(select(Plans).filter_by(id=plan_id))

    if not plan:
        raise NotFoundException("Plan not found")

    await db.delete(plan)
    await db.commit()

    return SuccessSchema(message="Plans deleted successfully")


@feature.get(
    "/plan/feature",
    response_model=SuccessSchema[list[PlanFeaturePlanFeatureResponseSchema]],
    status_code=200,
)
async def get_plan_feature(
    plan_status: PlansStatus | None = None,
    billing_type: PlansBillingType | None = None,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    session_user: Users = Depends(auth_middleware),  # noqa: B008
):
    if session_user.role != UserRole.ADMIN:
        raise BadRequestException("Invalid route")
    # process_data.delay(
    #     2, 4
    # )  # push task to the redis queue without blocking main thread
    stmt = (
        select(PlanFeature, Plans, Feature)
        .join(Plans, Plans.id == PlanFeature.plan_id)
        .join(Feature, Feature.id == PlanFeature.feature_id)
        .order_by(PlanFeature.plan_id.desc())
    )
    plan_features = await db.execute(stmt)
    if plan_status:
        plan_features = plan_features.filter(Plans.status == plan_status)
    if billing_type:
        plan_features = plan_features.filter(Plans.plan_billing_type == billing_type)

    plan_features = plan_features.all()

    # Dictionary to group plans by plan ID
    grouped_data = {}

    for _planfeature, _plans, _feature in plan_features:
        _planfeature: PlanFeature
        _plans: Plans
        _feature: Feature
        plan_id = _plans.id

        # If this plan isn't in our dictionary yet, add it with a base structure
        if plan_id not in grouped_data:
            grouped_data[plan_id] = {
                "plan_id": _plans.id,
                "author_id": _plans.author_id,
                "name": _plans.name,
                "price_amount": _plans.price_amount,
                "benefit": _plans.benefit,
                "status": _plans.status,
                "plan_billing_type": _plans.plan_billing_type,
                "created_at": _plans.created_at,
                "update_at": _plans.updated_at,
                "features": [],
            }

        # Append the feature to this plan's 'feat' list
        grouped_data[plan_id]["features"].append(
            {
                "plan_feature_id": _planfeature.id,
                "id": _feature.id,
                "name": _feature.name,
                "description": _feature.description,
                "quantity": _feature.quantity,
                "unit": _feature.unit,
                "created_at": _feature.created_at,
            }
        )

    # Convert the dictionary values into a final list
    results = [
        PlanFeaturePlanFeatureResponseSchema.model_validate(result)
        for result in grouped_data.values()
    ]

    return SuccessSchema(data=results)


@feature.post(
    "/plan/feature",
    response_model=SuccessSchema[PlanFeatureResponseSchema],
    status_code=201,
)
async def register_plan_feature(
    plan_feature_data: PlanFeatureSchema,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    session_user: Users = Depends(auth_middleware),  # noqa: B008
):
    if session_user.role != UserRole.ADMIN:
        raise BadRequestException("Invalid route")
    new_plan_feature = PlanFeature(
        plan_id=plan_feature_data.plan_id,
        feature_id=plan_feature_data.feature_id,
        usage_limit=plan_feature_data.usage_limit,
    )
    db.add(new_plan_feature)
    await db.commit()
    await db.refresh(new_plan_feature)
    return SuccessSchema(
        data=PlanFeatureResponseSchema.model_validate(new_plan_feature)
    )


@feature.delete(
    "/plan/feature/{plan_feature_id}",
    response_model=SuccessSchema[None],
    status_code=201,
)
async def delete_plan_feature(
    plan_feature_id: int,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    session_user: Users = Depends(auth_middleware),  # noqa: B008
):
    if session_user.role != UserRole.ADMIN:
        raise BadRequestException("Invalid route")
    plan_feature = await db.scalar(select(PlanFeature).filter_by(id=plan_feature_id))

    if not plan_feature:
        raise NotFoundException("Plan feature not found")

    await db.delete(plan_feature)

    await db.commit()

    return SuccessSchema(message="Feature removed from plan feature successfully")


@feature.post(
    "/plan/provider",
    response_model=SuccessSchema[PlanProviderResponseSchema],
    status_code=201,
)
async def plan_provider(
    plan_provider_data: PlanProviderSchema,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    session_user: Users = Depends(auth_middleware),  # noqa: B008
):
    if session_user.role != UserRole.ADMIN:
        raise BadRequestException("Invalid route")
    print(plan_provider_data.dict(), "test")
    plan = await db.scalar(select(Plans).filter_by(id=plan_provider_data.plan_id))

    if not plan:
        raise NotFoundException("Plan not found")

    # TODO: before storing validate plan(product) from provider to ensure admin has entered correct product_id

    existing_provider_product = await db.scalar(
        select(ProviderProduct).filter_by(
            product_id=plan_provider_data.product_id,
        ),
    )

    return SuccessSchema(
        data=PlanProviderResponseSchema.model_validate(existing_provider_product)
    )

    provider_product = ProviderProduct(
        provider=plan_provider_data.provider,
        plan_id=plan_provider_data.plan_id,
        product_id=plan_provider_data.product_id,
    )

    db.add(provider_product)
    await db.commit()
    await db.refresh(provider_product)

    return SuccessSchema(
        data=PlanProviderResponseSchema.model_validate(provider_product)
    )
