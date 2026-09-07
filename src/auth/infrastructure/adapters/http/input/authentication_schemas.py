from pydantic import BaseModel, EmailStr, Field


class LoginSchema(BaseModel):
    dni: str = Field(..., alias="dni", max_length=10)
    password: str = Field(..., alias="password", min_length=8, max_length=50)


class CreateTenantSchema(BaseModel):
    tenant_name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=100, pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., max_length=50)
    dni: str = Field(..., max_length=10)
    email: EmailStr


class ChangePasswordSchema(BaseModel):
    password: str = Field(..., alias="password", min_length=8, max_length=50)
    new_password: str = Field(..., alias="new_password", min_length=8, max_length=50)
    confirmed_password: str = Field(..., alias="confirmed_password", min_length=8, max_length=50)


class RefreshTokenSchema(BaseModel):
    refresh_token: str
