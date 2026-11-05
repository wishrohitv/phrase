import json
from typing import TypeVar
from warnings import deprecated

from fastapi import Response
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

T = TypeVar("T")


class SuccessSchema[T](BaseModel):
    data: T | None = None
    message: str = "Request successful"


@deprecated("New implementation added. Use SuccessSchema")
class Success(Response):
    def __init__(
        self,
        data: BaseModel | list[BaseModel] | str | dict | list | None = None,
        status_code=200,
        message="Request successfull",
    ):
        content = jsonable_encoder(
            {
                "data": data,
                "message": message,
            }
        )

        super().__init__(
            content=json.dumps(content),
            status_code=status_code,
            media_type="application/json",
        )
