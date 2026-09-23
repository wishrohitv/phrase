import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from redis_fastapi import FastAPIRedis

from database import engine
from models.base import Base
from modules.auth.routes import auth
from modules.billing.routes import billing
from modules.chat.routes import chats
from modules.subscription.routes import subscription
from modules.title.routes import title
from modules.user.routes import user
from utils import BadRequestException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app: FastAPI = FastAPI()

FastAPIRedis(app).lifespan().caching()

app.include_router(user, prefix="/api")
app.include_router(auth, prefix="/api")
app.include_router(title, prefix="/api")
app.include_router(subscription, prefix="/api")
app.include_router(chats, prefix="/api")
app.include_router(billing, prefix="/api")


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
