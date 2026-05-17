from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from app.models.user import UserRole


# ─── Request Schemas ────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    organization_name: str  # Creates org during signup

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Full name cannot be empty")
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class InviteUserRequest(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.ANALYST


# ─── Response Schemas ────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # enables ORM mode

    id: int
    name: str
    slug: str
    api_key: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    organization: OrganizationResponse
