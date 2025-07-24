# =============================================
# app/api/v1/endpoints/users.py (VERSÃO CORRIGIDA)
# =============================================
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.config.database import get_db
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserDetail

# =============================================
# ROUTER INSTANCE
# =============================================
router = APIRouter()

# =============================================
# DEPENDENCIES
# =============================================
async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)

# =============================================
# ROUTES (SEM TRY/EXCEPT - EXCEPTIONS TRATADAS GLOBALMENTE)
# =============================================

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Criar novo usuário
    
    - **user_name**: Nome do usuário
    - **user_email**: Email único do usuário  
    - **password**: Senha (mínimo 8 caracteres)
    - **user_type**: Tipo do usuário
    - **is_work**: Se é usuário de trabalho
    - **birth_day**: Data de nascimento (opcional)
    """
    # Exception handlers globais tratarão UserAlreadyExistsError automaticamente
    return await user_service.create_user(user_data)

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    user_service: UserService = Depends(get_user_service)
):
    """
    Listar usuários com paginação
    
    - **skip**: Número de registros a pular (padrão: 0)
    - **limit**: Limite de registros retornados (padrão: 100, máximo: 1000)
    """
    if limit > 1000:
        limit = 1000
    return await user_service.get_users(skip=skip, limit=limit)

@router.get("/{user_id}", response_model=UserDetail)
async def get_user(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service)
):
    """
    Obter usuário por ID
    
    Retorna informações detalhadas do usuário incluindo relacionamentos.
    """
    # Exception handlers globais tratarão UserNotFoundError automaticamente
    return await user_service.get_user(user_id)

@router.put("/{user_id}", response_model=UserDetail)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Atualizar usuário
    
    Permite atualização parcial dos dados do usuário.
    Apenas os campos fornecidos serão atualizados.
    """
    # Exception handlers globais tratarão UserNotFoundError automaticamente
    return await user_service.update_user(user_id, user_data)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service)
):
    """
    Deletar usuário (soft delete)
    
    Marca o usuário como deletado sem remover do banco de dados.
    """
    # Exception handlers globais tratarão UserNotFoundError automaticamente
    await user_service.delete_user(user_id)

@router.get("/{user_id}/exists", response_model=dict)
async def check_user_exists(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service)
):
    """
    Verificar se usuário existe
    
    Retorna se o usuário existe sem retornar seus dados.
    """
    try:
        await user_service.get_user(user_id)
        return {"exists": True, "user_id": user_id}
    except:
        return {"exists": False, "user_id": user_id}