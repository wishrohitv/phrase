import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from database import engine
from models.base import Base
from modules.auth.routes import auth
from modules.entity.routes import entity
from modules.subscription.routes import subscription
from modules.users.routes import users
from utils import BadRequestException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


app.include_router(users, prefix="/api")
app.include_router(auth, prefix="/api")
app.include_router(entity, prefix="/api")
app.include_router(subscription, prefix="/api")


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = []

    for err in exc.errors():
        errors.append(
            {
                "location": err["loc"][0],
                "field": ".".join(map(str, err["loc"][1:])),
                "message": err["msg"],
            }
        )

    raise BadRequestException(
        # Send only one error at once
        f"{errors[0]['field']}, {errors[0]['message']}",
    )


Base.metadata.create_all(bind=engine)
