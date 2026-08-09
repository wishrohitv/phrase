import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from middlewares.auth_middleware import auth_middleware
from models.enums import PlansStatus
from models.plans import Plans
from models.users import UserRole, Users
from utils.errors import BadRequestException, InternalServerErrorException
from utils.success import Success

from .pydantic_schema import EditPlansSchema, PlansSchema

subscription = APIRouter(prefix="/subscription")

logger = logging.getLogger(__name__)


@subscription.get("/plans")
def subscription_plans(db: Session = Depends(get_db)):  # noqa: B008
    plans = db.query(Plans).filter_by(status=PlansStatus.ACTIVE).all()
    data = [
        {
            "id": plan.id,
            "user_id": plan.user_id,
            "price": plan.price,
            "benifit": plan.benifit,
            "created_at": plan.created_at.isoformat(),
        }
        for plan in plans
    ]
    return Success(data, message="Fetched plans successfully")


@subscription.post("/plans")
def subscription_plans_new(
    plans_data: PlansSchema,
    db: Session = Depends(get_db),  # noqa: B008
    session_user: Users = Depends(auth_middleware),  # noqa: B008
):
    try:
        if session_user.role != UserRole.ADMIN:
            raise BadRequestException("Invalid route")
        new_plan = Plans(
            user_id=session_user.id,
            price=plans_data.price,
            benifit=plans_data.benifit,
            status=plans_data.status,
        )

        db.add(new_plan)
        db.commit()
    except Exception:
        logger.exception("Error while adding data")
        raise InternalServerErrorException("Error while adding data")
    return Success(data=new_plan, message="Plans added successfully", status_code=201)


@subscription.patch("/plans")
def subscription_plans_edit(
    plans_data: EditPlansSchema,
    db: Session = Depends(get_db),  # noqa: B008
    session_user: Users = Depends(auth_middleware),  # noqa: B008
):
    if session_user.role != UserRole.ADMIN:
        raise BadRequestException("Invalid route")
    try:
        plan = db.query(Plans).filter_by(id=plans_data.id).scalar()
        if plans_data.price is not None:
            plan.price = plans_data.price
        if plans_data.benifit is not None:
            plan.benifit = plans_data.benifit
        if plans_data.status:
            plan.status = plans_data.status

        db.commit()
    except Exception:
        logger.exception("Error wile chaching data")
        raise InternalServerErrorException("Error while changing data")
    return Success(message="Plans updated successfully", status_code=200)
