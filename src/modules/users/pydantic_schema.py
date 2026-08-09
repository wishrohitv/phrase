from pydantic import BaseModel


class UserSchema(BaseModel):
    id: int
    email: str
    fullname: str | None = None

    class Config:
        orm_mode = True
