from fastapi import HTTPException


class BadRequestException(HTTPException):
    def __init__(self, error: str = "Bad Request"):
        super().__init__(status_code=400, detail={"error": error})


class UnauthorizedException(HTTPException):
    def __init__(self, error: str = "Unauthorized"):
        super().__init__(status_code=401, detail={"error": error})


class ForbiddenException(HTTPException):
    def __init__(self, error: str = "Forbidden"):
        super().__init__(status_code=403, detail={"error": error})


class NotFoundException(HTTPException):
    def __init__(self, error: str = "Not Found"):
        super().__init__(status_code=404, detail={"error": error})


class ConflictException(HTTPException):
    def __init__(self, error: str = "Conflict"):
        super().__init__(status_code=409, detail={"error": error})


class InternalServerErrorException(HTTPException):
    def __init__(self, error: str = "Internal Server Error"):
        super().__init__(status_code=500, detail={"error": error})
