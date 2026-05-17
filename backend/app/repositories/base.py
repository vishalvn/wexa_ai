from typing import TypeVar, Generic, Type, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        await self.db.flush()  # flush to get the ID without committing yet
        await self.db.refresh(obj)
        return obj

    async def update_by_id(self, id: int, **kwargs: Any) -> Optional[ModelType]:
        await self.db.execute(
            update(self.model).where(self.model.id == id).values(**kwargs)
        )
        return await self.get_by_id(id)

    async def delete_by_id(self, id: int) -> bool:
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0

    async def soft_delete(self, id: int) -> Optional[ModelType]:
        return await self.update_by_id(id, is_deleted=True)
