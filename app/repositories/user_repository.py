# =============================================
# app/repositories/user_repository.py - ATUALIZADO
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
        """Create a new user"""
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
        """Get user by ID"""
        stmt = select(User).where(
            and_(User.user_id == user_id, User.deleted_date.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(User).where(
            and_(User.user_email == email, User.deleted_date.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        stmt = select(User).where(
            User.deleted_date.is_(None)
        ).offset(skip).limit(limit).order_by(User.user_name)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update(self, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """Update user"""
        # Pegar dados apenas dos campos preenchidos
        update_data = user_data.model_dump(exclude_unset=True)
        
        if not update_data:
            return await self.get_by_id(user_id)
        
        try:
            stmt = update(User).where(
                and_(User.user_id == user_id, User.deleted_date.is_(None))
            ).values(**update_data)
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            if result.rowcount == 0:
                return None
                
            return await self.get_by_id(user_id)
            
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("Email já está em uso")
    
    async def update_password(self, user_id: UUID, new_password_hash: str) -> Optional[User]:
        """Update user password"""
        try:
            stmt = update(User).where(
                and_(User.user_id == user_id, User.deleted_date.is_(None))
            ).values(password=new_password_hash)
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            if result.rowcount == 0:
                return None
                
            return await self.get_by_id(user_id)
            
        except Exception:
            await self.db.rollback()
            raise ValueError("Erro ao atualizar senha")
    
    async def soft_delete(self, user_id: UUID) -> bool:
        """Soft delete user"""
        from datetime import datetime
        
        try:
            stmt = update(User).where(
                and_(User.user_id == user_id, User.deleted_date.is_(None))
            ).values(deleted_date=datetime.utcnow())
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.rowcount > 0
            
        except Exception:
            await self.db.rollback()
            return False
    
    # =============================================
    # ADDITIONAL METHODS FOR AUTHENTICATION
    # =============================================
    
    async def get_by_user_type(self, user_type: str) -> List[User]:
        """Get users by type"""
        stmt = select(User).where(
            and_(User.user_type == user_type, User.deleted_date.is_(None))
        ).order_by(User.user_name)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_active_users(self) -> List[User]:
        """Get all active (non-deleted) users"""
        stmt = select(User).where(
            User.deleted_date.is_(None)
        ).order_by(User.created_date.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def email_exists(self, email: str, exclude_user_id: Optional[UUID] = None) -> bool:
        """Check if email already exists"""
        stmt = select(User.user_id).where(
            and_(User.user_email == email, User.deleted_date.is_(None))
        )
        
        if exclude_user_id:
            stmt = stmt.where(User.user_id != exclude_user_id)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def get_users_by_company(self, company_id: UUID) -> List[User]:
        """Get users by company ID"""
        stmt = select(User).where(
            and_(
                User.company_id == company_id, 
                User.deleted_date.is_(None)
            )
        ).order_by(User.user_name)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def count_users(self) -> int:
        """Count total active users"""
        from sqlalchemy import func
        stmt = select(func.count(User.user_id)).where(User.deleted_date.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar() or 0
    
    async def count_users_by_type(self, user_type: str) -> int:
        """Count users by type"""
        from sqlalchemy import func
        stmt = select(func.count(User.user_id)).where(
            and_(User.user_type == user_type, User.deleted_date.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0