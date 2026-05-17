from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.repositories.base import BaseRepository
from app.models.user import User, Organization


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User)
            .where(User.email == email.lower())
            .options(selectinload(User.organization))  # load org in same query
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, id: int) -> User | None:
        result = await self.db.execute(
            select(User)
            .where(User.id == id)
            .options(selectinload(User.organization))
        )
        return result.scalar_one_or_none()

    async def get_by_org(self, org_id: int) -> list[User]:
        result = await self.db.execute(
            select(User).where(User.organization_id == org_id, User.is_active == True)
        )
        return list(result.scalars().all())


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, db: AsyncSession):
        super().__init__(Organization, db)

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self.db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_api_key(self, api_key: str) -> Organization | None:
        result = await self.db.execute(
            select(Organization).where(Organization.api_key == api_key)
        )
        return result.scalar_one_or_none()
