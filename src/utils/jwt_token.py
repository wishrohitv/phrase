import jwt
from .datetime_utc import datetime_utc_now, timedelta


def create_jwt_token(data: dict, secret_key: str, expire_in_minutes: int) -> str:
    """
    Create a JWT token.

    Args:
        data (dict): The payload data to encode in the token.
        secret_key (str): The secret key for encoding the token.
        expire_in_minutes (int): The number of minutes until the token expires.

    Returns:
        str: The encoded JWT token.
    """
    timestamp = datetime_utc_now() + timedelta(minutes=expire_in_minutes)
    return jwt.encode(
        {
            "data": data,
            "exp": int(timestamp.timestamp()),
        },  # unix timestamp for expiration
        secret_key,
        algorithm="HS256",
    )


def decode_jwt_token(token: str, secret_key: str) -> dict:
    """
    Decode a JWT token.

    Args:
        token (str): The JWT token to decode.
        secret_key (str): The secret key for decoding the token.

    Returns:
        dict: The decoded payload data.

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token is invalid.
    """
    return jwt.decode(token, secret_key, algorithms=["HS256"])
