from logging import getLogger

import jwt
from fastapi import Cookie, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


async def auth_middleware(
    authorization: str | None = Header(None),
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Users:

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

        user = await db.scalar(
            select(Users).filter_by(id=decode_token.get("data", {}).get("user_id"))
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
    except HTTPException:
        raise

    except Exception:
        logger.exception("Error while validating access token")
        raise InternalServerErrorException("Error while validating access token")
