from pydantic import BaseModel, Field, model_validator

from models.enums import PlansStatus


class PlansSchema(BaseModel):
    price: float
    benifit: int
    status: PlansStatus


class EditPlansSchema(BaseModel):
    id: int
    price: float | None = Field(default=None)
    benifit: int | None = Field(default=None)
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
