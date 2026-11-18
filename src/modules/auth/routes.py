import random
from logging import getLogger
from typing import Annotated

import bcrypt
import jwt
from fastapi import APIRouter, Body, Cookie, Depends, Header, Response
from redis_fastapi import CacheBackendDep
from sqlalchemy.orm import Session

from database import get_db
from middlewares.auth_middleware import auth_middleware
from models.sessions import Sessions
from models.users import Users
from services.mail_service import send_mail
from settings import settings
from tasks.celery_app import process_data
from utils.errors import (
    BadRequestException,
    HTTPException,
    InternalServerErrorException,
    NotFoundException,
    UnauthorizedException,
)
from utils.jwt_token import create_jwt_token, decode_jwt_token
from utils.success import SuccessSchema

from .pydantic_schema import (
    UserLoginResponseSchema,
    UserLoginSchema,
    UserRefreshTokenResponseSchema,
    UserRegisterResponseSchema,
    UserRegisterSchema,
    UserRequestResetPasswordSchema,
    UserVerifyResetPasswordSchema,
)

logger = getLogger(__name__)

auth = APIRouter(prefix="/auth", tags=["Auth"])


@auth.post("/register", response_model=SuccessSchema, status_code=201)
async def register_user(
    user_data: UserRegisterSchema,
    db: Session = Depends(get_db),  # noqa: B008
):

    user = db.query(Users).filter(Users.email == user_data.email).first()
    if user:
        raise BadRequestException("Email already registered")
    new_user = Users(
        email=user_data.email,
        name=user_data.name,
        password=bcrypt.hashpw(
            user_data.password.encode("utf-8"),
            bcrypt.gensalt(rounds=settings.SALT_ROUNDS),
        ),
        native_language=user_data.native_language,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return SuccessSchema(
        data=UserRegisterResponseSchema(user_id=new_user.id),
        message="Account created successfully",
    )


@auth.post(
    "/login", response_model=SuccessSchema[UserLoginResponseSchema], status_code=200
)
async def login_user(
    user_data: UserLoginSchema,
    response: Response,
    db: Session = Depends(get_db),  # noqa: B008
):
    user = db.query(Users).filter(Users.email == user_data.email).first()
    if not user:
        raise BadRequestException("Invalid email or password")
    if not bcrypt.checkpw(user_data.password.encode("utf-8"), user.password):
        raise BadRequestException("Invalid email or password")
    access_token = create_jwt_token(
        data={"user_id": user.id},
        secret_key=settings.ACCESS_TOKEN_SECRET_KEY.get_secret_value(),
        expire_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    refresh_token = create_jwt_token(
        data={"user_id": user.id},
        secret_key=settings.REFRESH_TOKEN_SECRET_KEY.get_secret_value(),
        expire_in_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
    )

    session = Sessions(user_id=user.id, refresh_token=refresh_token)
    db.add(session)
    db.commit()

    response.set_cookie(
        "access_token",
        access_token,
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
    )
    return SuccessSchema(
        data=UserLoginResponseSchema(
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
        ),
        message="User logged in successfully",
    )


@auth.post("/logout", response_model=SuccessSchema[None], status_code=200)
async def logout(
    response: Response,
    x_refresh_token: str | None = Header(None),  # Mobile
    refresh_token: str | None = Cookie(None),  # Browser
    db: Session = Depends(get_db),  # noqa: B008
    all_devices: bool = False,
    session_user: Users = Depends(auth_middleware),  # noqa: B008
):
    _refresh_token = refresh_token or x_refresh_token
    if not _refresh_token:
        raise BadRequestException("Refresh token required")

    if all_devices:
        db.query(Sessions).filter(
            Sessions.user_id == session_user.id, Sessions.refresh_token != None
        ).update(values={"refresh_token": None}, synchronize_session="evaluate")
    else:
        db.query(Sessions).filter(
            Sessions.user_id == session_user.id,
            Sessions.refresh_token == _refresh_token,
        ).update(values={"refresh_token": None}, synchronize_session="evaluate")
    db.commit()

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return SuccessSchema(message="User logged out successfully")


@auth.post(
    "/refresh-token",
    response_model=SuccessSchema[UserRefreshTokenResponseSchema],
    status_code=200,
)
async def refresh_token(
    response: Response,
    db: Session = Depends(get_db),  # noqa: B008
    x_refresh_token: str = Header(None),
    refresh_token: str = Cookie(None),
):
    try:
        if x_refresh_token:
            scheme, token = x_refresh_token.split(maxsplit=1)
            if scheme.lower() != "bearer":
                raise BadRequestException("Invalid authentication scheme")
        elif refresh_token:
            token = refresh_token
        else:
            raise BadRequestException("Missing authentication credentials")

        decode_token = decode_jwt_token(
            token, settings.REFRESH_TOKEN_SECRET_KEY.get_secret_value()
        )
        session = (
            db.query(Sessions)
            .filter_by(
                refresh_token=token,
                user_id=decode_token.get("data", {}).get("user_id"),
            )
            .first()
        )
        if not session:
            raise UnauthorizedException("Invalid access token")

        user = db.query(Users).filter_by(id=session.user_id).first()
        access_token = create_jwt_token(
            data={"user_id": user.id},
            secret_key=settings.ACCESS_TOKEN_SECRET_KEY.get_secret_value(),
            expire_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        refresh_token = create_jwt_token(
            data={"user_id": user.id},
            secret_key=settings.REFRESH_TOKEN_SECRET_KEY.get_secret_value(),
            expire_in_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
        )

        # Add new token
        new_session = Sessions(user_id=user.id, refresh_token=refresh_token)
        db.add(new_session)
        db.commit()

        # Delete the existing token
        session.refresh_token = None
        db.commit()

        response.set_cookie(
            "access_token",
            access_token,
        )
        response.set_cookie(
            "refresh_token",
            refresh_token,
        )
        return SuccessSchema(
            data=UserRefreshTokenResponseSchema(
                user_id=user.id,
                access_token=access_token,
                refresh_token=refresh_token,
            ),
            message="Token refreshed successfully",
        )
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Access token expired")

    except jwt.InvalidTokenError:
        raise UnauthorizedException("Invalid access token")
    except HTTPException:
        raise
    except Exception as _:
        logger.exception("Error while validating access token")
        raise InternalServerErrorException("Error while validating access token")


@auth.post("/otp", response_model=SuccessSchema[None], status_code=200)
async def generate_opt(
    redis: CacheBackendDep,
    email: Annotated[str, Body(embed=True)],
    db: Session = Depends(get_db),  # noqa: B008
):
    redis_key = f"otp:{email}"
    user = db.query(Users).filter_by(email=email).scalar()

    if not user:
        raise NotFoundException("User not found")

    if user.is_verified:
        return BadRequestException("User is already varified")

    otp = random.randint(100000, 999999)
    # Send this job to queues
    send_mail(email)
    await redis.set(redis_key, otp, ttl=600)
    return SuccessSchema(data=otp)


@auth.post("/otp-validate", response_model=SuccessSchema[None], status_code=200)
async def validate_opt(
    redis: CacheBackendDep,
    email: Annotated[str, Body(embed=True)],
    otp: Annotated[int, Body(embed=True, min_length=6, max_length=6)],
    db: Session = Depends(get_db),  # noqa: B008
):
    redis_key = f"verify-user:otp:{email}"

    redi_otp = await redis.get(redis_key)

    if not otp:
        raise BadRequestException("OTP is expired")

    if otp != redi_otp:
        raise BadRequestException("Invalid OTP")

    user = db.query(Users).filter_by(email=email).scalar()

    if not user:
        raise NotFoundException("User not found")
    if user.is_verified:
        return BadRequestException("User is already varified")

    user.is_verified = True

    db.commit()

    return SuccessSchema(message="User verified successfully")


@auth.post(
    "/request-reset-password", response_model=SuccessSchema[None], status_code=200
)
async def reset_password(
    reset_schema: UserRequestResetPasswordSchema,
    redis: CacheBackendDep,
    db: Session = Depends(get_db),  # noqa: B008
):
    redis_key = f"request-reset-password:otp:{reset_schema.email}"

    user = db.query(Users).filter_by(email=reset_schema.email).scalar()
    if not user:
        raise NotFoundException("User not found")

    otp = random.randint(100000, 999999)
    # Send this job to queues
    send_mail(reset_schema.email)
    await redis.set(redis_key, otp, ttl=600)

    return SuccessSchema(message="OTP generated successfully")


@auth.post(
    "/verify-reset-password", response_model=SuccessSchema[None], status_code=200
)
async def verify_password(
    reset_schema: UserVerifyResetPasswordSchema,
    redis: CacheBackendDep,
    db: Session = Depends(get_db),  # noqa: B008
):
    redis_key = f"request-reset-password:otp:{reset_schema.email}"

    otp = await redis.get(redis_key)

    if not otp:
        raise BadRequestException("OTP is expired")

    if reset_schema.otp != otp:
        raise BadRequestException("Invalid OTP")

    user = db.query(Users).filter_by(email=reset_schema.email).scalar()
    if not user:
        raise NotFoundException("User not found")

    user.password = bcrypt.hashpw(
        reset_schema.password.encode("utf-8"),
        bcrypt.gensalt(rounds=settings.SALT_ROUNDS),
    )

    db.commit()
    return SuccessSchema(message="Password reseted successfully")
