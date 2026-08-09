import json

from fastapi import Response


class Success(Response):
    def __init__(
        self,
        data: str | dict | None = None,
        status_code=200,
        message="Request successfull",
    ):
        super().__init__(
            content=json.dumps({"data": data, "message": message}),
            status_code=status_code,
        )
