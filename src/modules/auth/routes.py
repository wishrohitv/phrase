from logging import getLogger

import bcrypt
import jwt
from fastapi import APIRouter, Cookie, Depends, Header
from sqlalchemy.orm import Session

from database import get_db
from middlewares.auth_middleware import auth_middleware
from models.sessions import Sessions
from models.users import Users
from settings import settings
from utils.errors import (
    BadRequestException,
    HTTPException,
    InternalServerErrorException,
    UnauthorizedException,
)
from utils.jwt_token import create_jwt_token, decode_jwt_token
from utils.success import Success

from .pydantic_schema import UserLoginSchema, UserRegisterSchema

logger = getLogger(__name__)

auth = APIRouter(prefix="/auth")


@auth.post("/register")
async def register_user(
    user_data: UserRegisterSchema,
    db: Session = Depends(get_db),  # noqa: B008
):
    try:
        # Check user password length
        if len(user_data.password) < 8:
            raise BadRequestException("Password must be at least 8 characters long")

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
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return Success(
            data={"user_id": new_user.id},
            message="Account created successfully",
            status_code=201,
        )
    except HTTPException:
        raise
    except Exception as _:
        logger.exception("Error while creating user account")
        raise InternalServerErrorException("Error while creating user account")


@auth.post("/login")
async def login_user(
    user_data: UserLoginSchema,
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
    res = Success(
        data={
            "user_id": user.id,
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
        message="User logged in successfully",
    )

    res.set_cookie(
        "access_token",
        access_token,
    )
    res.set_cookie(
        "refresh_token",
        refresh_token,
    )
    return res


@auth.post("/logout")
def logout(
    db: Session = Depends(get_db),  # noqa: B008
    all_devices: bool = False,
    session_user: Users = Depends(auth_middleware),  # noqa: B008
):
    if all_devices:
        db.query(Sessions).filter(Sessions.user_id == session_user.id).delete()
    else:
        db.query(Sessions).filter(Sessions.user_id == session_user.id).delete()
    db.commit()
    res = Success(message="User logged out successfully")
    res.delete_cookie("access_token")
    res.delete_cookie("refresh_token")
    return res


@auth.post("/refresh-token")
def refresh_token(
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

        decode_token = decode_jwt_token(token, settings.REFRESH_TOKEN_SECRET_KEY.get_secret_value())
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
        db.delete(session)
        db.commit()

        res = Success(
            data={
                "user_id": user.id,
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
            message="Token refreshed successfully",
        )
        res.set_cookie(
            "access_token",
            access_token,
        )
        res.set_cookie(
            "refresh_token",
            refresh_token,
        )
        return res
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Access token expired")

    except jwt.InvalidTokenError:
        raise UnauthorizedException("Invalid access token")
    except HTTPException:
        raise
    except Exception as _:
        logger.exception("Error while validating access token")
        raise InternalServerErrorException("Error while validating access token")
