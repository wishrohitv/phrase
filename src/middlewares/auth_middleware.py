import traceback

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
        raise UnauthorizedException("Access token expired")

    except jwt.InvalidTokenError as e:
        print(e)
        raise UnauthorizedException("Invalid access token")

    except Exception as _:  # noqa: BLE001
        traceback.print_exc()
        raise InternalServerErrorException("Error while validating access token")
