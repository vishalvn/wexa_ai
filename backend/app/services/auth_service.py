import re
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, generate_api_key
)
from app.core.config import settings
from app.models.user import User, Organization, UserRole
from app.repositories.user_repo import UserRepository, OrganizationRepository
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse


def _slugify(name: str) -> str:
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[\s_-]+', '-', slug).strip('-')
    return slug


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.org_repo = OrganizationRepository(db)

    async def signup(self, data: SignupRequest) -> tuple[User, str, str]:

        # Check email uniqueness
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists"
            )

        # Create organization
        base_slug = _slugify(data.organization_name)
        slug = base_slug
        counter = 1
        while await self.org_repo.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        org = Organization(
            name=data.organization_name,
            slug=slug,
            api_key=generate_api_key(),
        )
        org = await self.org_repo.create(org)

        # Create user as org owner
        user = User(
            email=data.email.lower(),
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=UserRole.OWNER,
            organization_id=org.id,
            is_verified=True,  # skip email verification for now
        )
        user = await self.user_repo.create(user)

        # Generate tokens
        extra = {"org_id": org.id, "role": user.role.value}
        access_token = create_access_token(user.id, extra_claims=extra)
        refresh_token = create_refresh_token(user.id)

        return user, access_token, refresh_token

    async def login(self, data: LoginRequest) -> tuple[User, str, str]:

        user = await self.user_repo.get_by_email(data.email)

        # Always run verify_password even if user not found
        # This prevents timing attacks that reveal valid emails
        password_valid = verify_password(
            data.password,
            user.hashed_password if user else "$2b$12$placeholder-hash-for-timing"
        )

        if not user or not password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been deactivated"
            )

        # Update last login timestamp
        await self.user_repo.update_by_id(
            user.id, last_login=datetime.now(timezone.utc)
        )

        extra = {"org_id": user.organization_id, "role": user.role.value}
        access_token = create_access_token(user.id, extra_claims=extra)
        refresh_token = create_refresh_token(user.id)

        return user, access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> str:
        from jose import JWTError
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError("Not a refresh token")
            user_id = int(payload["sub"])
        except (JWTError, ValueError, KeyError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        extra = {"org_id": user.organization_id, "role": user.role.value}
        return create_access_token(user.id, extra_claims=extra)

    async def rotate_api_key(self, org_id: int) -> str:
        new_key = generate_api_key()
        await self.org_repo.update_by_id(org_id, api_key=new_key)
        return new_key
