import traceback
from logging import getLogger

import jwt
from fastapi import Cookie, Depends, Header
from sqlalchemy.orm import Session

from database import get_db
from models.users import Users
from settings import settings
from utils.errors import (
    BadRequestException,
    InternalServerErrorException,
    UnauthorizedException,
)
from utils.jwt_token import decode_jwt_token

logger = getLogger(__name__)


def auth_middleware(
    authorization: str | None = Header(None),
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),  # noqa: B008
):

    try:
        if authorization:
            scheme, token = authorization.split(maxsplit=1)
            if scheme.lower() != "bearer":
                raise BadRequestException("Invalid authentication scheme")
        elif access_token:
            token = access_token
        else:
            raise BadRequestException("Missing authentication credentials")

        decode_token = decode_jwt_token(
            token, settings.ACCESS_TOKEN_SECRET_KEY.get_secret_value()
        )

        user = (
            db.query(Users)
            .filter_by(id=decode_token.get("data", {}).get("user_id"))
            .first()
        )
        if not user:
            raise UnauthorizedException("User not found")

        return user

    except jwt.ExpiredSignatureError:
        logger.info("Access token expired")
        raise UnauthorizedException("Access token expired")

    except jwt.InvalidTokenError:
        logger.info("Invalid access token")
        raise UnauthorizedException("Invalid access token")

    except Exception:
        logger.exception("Error while validating access token")
        raise InternalServerErrorException("Error while validating access token")
