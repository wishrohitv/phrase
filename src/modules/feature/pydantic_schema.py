from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models import FeatureUnit, PaymentProviderType, PlansBillingType, PlansStatus
from utils.datetime_utc import datetime


class FeatureSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(max_length=100)
    description: str = Field(max_length=255)
    quantity: int
    unit: FeatureUnit


class FeatureResponseSchema(FeatureSchema):
    id: int
    created_at: datetime


class PlansSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(min_length=3, max_length=50)
    price_amount: float
    benefit: str = Field(min_length=3, max_length=300)
    status: PlansStatus
    plan_billing_type: PlansBillingType


class PlansResponseSchema(PlansSchema):
    id: int
    author_id: int
    price_currency: str
    created_at: datetime
    updated_at: datetime


class EditPlansSchema(BaseModel):
    id: int
    price_amount: float | None = Field(default=None)
    benefit: str | None = Field(default=None)
    status: PlansStatus | None = Field(default=None)

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> Self:
        # Fixed: using 'is None' so a price of 0.0 is accepted validly
        if self.price_amount is None and self.benefit is None and self.status is None:
            raise ValueError(
                "You must provide at least 'price_amount', 'benefit', or 'status' to update."
            )
        return self


class PlanFeatureSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    plan_id: int
    feature_id: int
    usage_limit: int


class PlanFeatureResponseSchema(PlanFeatureSchema):
    id: int
    created_at: datetime


class PlanFeatureForPlanFeatureResponseSchema(FeatureResponseSchema):
    plan_feature_id: int


class PlanFeaturePlanFeatureResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan_id: int
    author_id: int
    name: str
    price_amount: float
    benefit: str | None = None
    status: PlansStatus
    plan_billing_type: PlansBillingType
    created_at: datetime
    update_at: datetime
    features: list[PlanFeatureForPlanFeatureResponseSchema] = []


class PlanProviderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan_id: int
    provider: PaymentProviderType
    product_id: str


class PlanProviderResponseSchema(PlanProviderSchema):
    id: int
    created_at: datetime
    updated_at: datetime
