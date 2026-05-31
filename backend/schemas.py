from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


Role = Literal["B2C", "B2G"]


class SignupRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=40)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class SelectRoleRequest(BaseModel):
    role: Role


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: Role | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class RouteAnalysisRequest(BaseModel):
    origin: str = Field(min_length=1, max_length=200)
    destination: str = Field(min_length=1, max_length=200)
    disability: str = Field(default="physical", max_length=40)
