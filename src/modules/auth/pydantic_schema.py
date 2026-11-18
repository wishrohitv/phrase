from pydantic import BaseModel, Field

from models import Language


class UserLoginSchema(BaseModel):
    email: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=20)


class UserRegisterSchema(BaseModel):
    email: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=20)
    name: str | None = Field(default=None, max_length=20)
    native_language: Language = Field(default=Language.ENGLISH)


class UserRegisterResponseSchema(BaseModel):
    user_id: int


class UserLoginResponseSchema(BaseModel):
    user_id: int
    access_token: str
    refresh_token: str


class UserRefreshTokenResponseSchema(UserLoginResponseSchema):
    pass


class UserRequestResetPasswordSchema(BaseModel):
    email: str = Field(min_length=3, max_length=40)


class UserVerifyResetPasswordSchema(UserRequestResetPasswordSchema):
    otp: int = Field(min_length=6, max_length=6)
    password: str = Field(min_length=8, max_length=20)
