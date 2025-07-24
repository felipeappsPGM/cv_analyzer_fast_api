# =============================================
# app/services/user_service.py
# =============================================
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserDetail
from app.core.exceptions import UserNotFoundError, UserAlreadyExistsError

class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        # Verificar se email já existe
        existing_user = await self.user_repo.get_by_email(user_data.user_email)
        if existing_user:
            raise UserAlreadyExistsError("Email já está em uso")
        
        try:
            user = await self.user_repo.create(user_data)
            return UserResponse.model_validate(user)
        except ValueError as e:
            raise UserAlreadyExistsError(str(e))
    
    async def get_user(self, user_id: UUID) -> UserDetail:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("Usuário não encontrado")
        return UserDetail.model_validate(user)
    
    async def get_user_by_email(self, email: str) -> Optional[UserDetail]:
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        return UserDetail.model_validate(user)
    
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        users = await self.user_repo.get_all(skip=skip, limit=limit)
        return [UserResponse.model_validate(user) for user in users]
    
    async def update_user(self, user_id: UUID, user_data: UserUpdate) -> UserDetail:
        user = await self.user_repo.update(user_id, user_data)
        if not user:
            raise UserNotFoundError("Usuário não encontrado")
        return UserDetail.model_validate(user)
    
    async def delete_user(self, user_id: UUID) -> bool:
        success = await self.user_repo.soft_delete(user_id)
        if not success:
            raise UserNotFoundError("Usuário não encontrado")
        return success