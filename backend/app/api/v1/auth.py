from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.auth import (
    SignupRequest, LoginRequest, RefreshTokenRequest,
    TokenResponse, UserResponse
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    data: SignupRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user, access_token, refresh_token = await service.signup(data)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,       # HTTPS only in production
        samesite="lax",
        max_age=7 * 24 * 3600,  # 7 days
    )
    response.headers["X-Access-Token"] = access_token

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):

    service = AuthService(db)
    user, access_token, refresh_token = await service.login(data)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )

    from app.core.config import settings
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):

    service = AuthService(db)
    new_access_token = await service.refresh_access_token(data.refresh_token)
    from app.core.config import settings
    return TokenResponse(
        access_token=new_access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.post("/rotate-api-key")
async def rotate_api_key(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.deps import require_role
    from app.models.user import UserRole
    if current_user.role not in (UserRole.OWNER, UserRole.ADMIN):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Requires Owner or Admin role")

    service = AuthService(db)
    new_key = await service.rotate_api_key(current_user.organization_id)
    return {"api_key": new_key}
