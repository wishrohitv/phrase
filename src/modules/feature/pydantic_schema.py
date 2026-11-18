from pydantic import BaseModel, ConfigDict, Field, model_validator

from models import FeatureUnit, PlansBillingType, PlansStatus
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
    price_amount: float = Field()
    benifit: str = Field(min_length=3, max_length=300)
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
    price: float | None = Field(default=None)
    benifit: str | None = Field(default=None)
    status: PlansStatus | None = Field(default=None)

    # Validator to check none value if all value is none
    @model_validator(mode="after")
    def check_price_or_benifit_of_status(self) -> EditPlansSchema:
        # OR condition logic
        if not self.price and not self.benifit and not self.status:
            raise ValueError(
                "You must provide either a 'price' or 'benifit' or 'status'."
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


class PlanFeaturePlanFeatureResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan_id: int
    author_id: int
    name: str
    price_amount: float
    benifit: str | None = None
    status: PlansStatus
    plan_billing_type: PlansBillingType
    created_at: datetime
    update_at: datetime
    features: list[FeatureResponseSchema] = []
