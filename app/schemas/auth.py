from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    admin = "admin"
    ml_engineer = "ml_engineer"
    analyst = "analyst"
    consumer = "consumer"


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "email": "ml.engineer@example.com",
                "password": "StrongPassword123!",
                "role": "ml_engineer",
            }
        },
    )


class UserOut(BaseModel):
    id: str
    email: EmailStr
    role: UserRole
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., gt=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example",
                "token_type": "bearer",
                "expires_in": 1800,
            }
        }
    )


class UserMe(BaseModel):
    id: str
    email: EmailStr
    role: UserRole
    model_config = ConfigDict(from_attributes=True)
