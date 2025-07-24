# =============================================
# app/repositories/user_repository.py
# =============================================
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from uuid import UUID

from app.database.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, user_data: UserCreate) -> User:
        # Hash da senha
        hashed_password = get_password_hash(user_data.password)
        
        # Criar user
        db_user = User(
            user_name=user_data.user_name,
            password=hashed_password,
            user_email=user_data.user_email,
            is_work=user_data.is_work,
            user_type=user_data.user_type,
            birth_day=user_data.birth_day
        )
        
        self.db.add(db_user)
        try:
            await self.db.commit()
            await self.db.refresh(db_user)
            return db_user
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("Email já existe")
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        stmt = select(User).where(
            and_(User.user_id == user_id, User.deleted_date.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(
            and_(User.user_email == email, User.deleted_date.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        stmt = select(User).where(
            User.deleted_date.is_(None)
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update(self, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        # Pegar dados apenas dos campos preenchidos
        update_data = user_data.model_dump(exclude_unset=True)
        
        if not update_data:
            return await self.get_by_id(user_id)
        
        stmt = update(User).where(
            and_(User.user_id == user_id, User.deleted_date.is_(None))
        ).values(**update_data)
        
        await self.db.execute(stmt)
        await self.db.commit()
        return await self.get_by_id(user_id)
    
    async def soft_delete(self, user_id: UUID) -> bool:
        from datetime import datetime
        
        stmt = update(User).where(
            and_(User.user_id == user_id, User.deleted_date.is_(None))
        ).values(deleted_date=datetime.utcnow())
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0