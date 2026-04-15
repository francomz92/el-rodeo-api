from pydantic import BaseModel, Field


class LoginSchema(BaseModel):
    dni: str = Field(..., alias="dni", max_length=10)
    password: str = Field(..., alias="password", min_length=8, max_length=50)


class RegisterSchema(BaseModel):
    dni: str = Field(..., alias="dni", max_length=10)


class ChangePasswordSchema(BaseModel):
    token: str
    password: str = Field(..., alias="password", min_length=8, max_length=50)
    new_password: str = Field(..., alias="new_password", min_length=8, max_length=50)
    confirmed_password: str = Field(..., alias="confirmed_password", min_length=8, max_length=50)
