from pydantic import BaseModel, Field


class UserLoginSchema(BaseModel):
    email: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=20)


class UserRegisterSchema(BaseModel):
    email: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=20)
    name: str | None = Field(default=None, max_length=20)
