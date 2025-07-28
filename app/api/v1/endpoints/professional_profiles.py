# =============================================
# app/api/v1/endpoints/professional_profiles.py
# =============================================
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
from uuid import UUID

from app.config.database import get_db
from app.services.professional_profile_service import ProfessionalProfileService
from app.schemas.professional_profile import (
    ProfessionalProfileCreate, 
    ProfessionalProfileUpdate, 
    ProfessionalProfileResponse, 
    ProfessionalProfileDetail, 
    ProfessionalProfileSummary,
    ProfessionalProfileSearchFilters,
    ProfessionalProfileStatistics,
    ProfileCompletenessInfo
)
from app.schemas.user import UserResponse
from app.api.v1.endpoints.auth import get_current_user, require_recruiter_or_admin

# =============================================
# ROUTER INSTANCE
# =============================================
router = APIRouter()

# =============================================
# DEPENDENCIES
# =============================================
async def get_profile_service(db: AsyncSession = Depends(get_db)) -> ProfessionalProfileService:
    return ProfessionalProfileService(db)

def check_profile_ownership_or_admin(current_user: UserResponse, profile_user_id: UUID):
    """Helper to check if user owns profile or is admin/recruiter"""
    if current_user.user_type in ["admin", "recruiter", "company_owner"]:
        return True
    return current_user.user_id == profile_user_id

# =============================================
# PROFILE CRUD ROUTES
# =============================================

@router.post("/", response_model=ProfessionalProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: ProfessionalProfileCreate,
    current_user: UserResponse = Depends(get_current_user),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Criar novo perfil profissional
    
    **Requer autenticação**
    
    - **professional_profile_name**: Nome do perfil profissional
    - **professional_profile_description**: Descrição do perfil (opcional)
    - **user_id**: ID do usuário proprietário
    - **academic_background_id**: ID da formação acadêmica (opcional)
    - **professional_experience_id**: ID da experiência profissional (opcional)
    - **professional_courses_id**: ID dos cursos profissionais (opcional)
    
    **BR07**: Permite criação com informações mínimas (apenas nome é obrigatório)
    """
    # Check if user can create profile for this user_id
    if not check_profile_ownership_or_admin(current_user, profile_data.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode criar perfis para si mesmo"
        )
    
    return await profile_service.create_profile(profile_data, create_user_id=current_user.user_id)

@router.get("/", response_model=List[ProfessionalProfileResponse])
async def get_profiles(
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Listar perfis profissionais com paginação
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    - **skip**: Número de registros a pular (padrão: 0)
    - **limit**: Limite de registros retornados (padrão: 100, máximo: 1000)
    """
    return await profile_service.get_profiles(skip=skip, limit=limit)

@router.get("/search", response_model=List[ProfessionalProfileSummary])
async def search_profiles(
    professional_profile_name: Optional[str] = Query(None, description="Filtrar por nome do perfil"),
    user_id: Optional[UUID] = Query(None, description="Filtrar por usuário"),
    user_name: Optional[str] = Query(None, description="Filtrar por nome do usuário"),
    user_email: Optional[str] = Query(None, description="Filtrar por email do usuário"),
    has_academic_background: Optional[bool] = Query(None, description="Filtrar por formação acadêmica"),
    has_professional_experience: Optional[bool] = Query(None, description="Filtrar por experiência profissional"),
    has_professional_courses: Optional[bool] = Query(None, description="Filtrar por cursos profissionais"),
    min_completeness: Optional[float] = Query(None, ge=0, le=100, description="Completude mínima do perfil"),
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Buscar perfis profissionais com filtros avançados
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Permite filtrar perfis por diversos critérios incluindo completude.
    """
    filters = ProfessionalProfileSearchFilters(
        professional_profile_name=professional_profile_name,
        user_id=user_id,
        user_name=user_name,
        user_email=user_email,
        has_academic_background=has_academic_background,
        has_professional_experience=has_professional_experience,
        has_professional_courses=has_professional_courses,
        min_completeness=min_completeness
    )
    
    return await profile_service.search_profiles(filters, skip=skip, limit=limit)

@router.get("/by-completeness", response_model=List[ProfessionalProfileSummary])
async def get_profiles_by_completeness(
    min_completeness: float = Query(..., ge=0, le=100, description="Completude mínima do perfil"),
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Listar perfis por completude mínima
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Retorna perfis que atendem ao critério de completude mínima.
    """
    return await profile_service.get_profiles_by_completeness(min_completeness, skip=skip, limit=limit)

@router.get("/count")
async def get_profiles_count(
    professional_profile_name: Optional[str] = Query(None, description="Filtrar por nome do perfil"),
    user_id: Optional[UUID] = Query(None, description="Filtrar por usuário"),
    user_name: Optional[str] = Query(None, description="Filtrar por nome do usuário"),
    has_academic_background: Optional[bool] = Query(None, description="Filtrar por formação acadêmica"),
    has_professional_experience: Optional[bool] = Query(None, description="Filtrar por experiência profissional"),
    has_professional_courses: Optional[bool] = Query(None, description="Filtrar por cursos profissionais"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Contar total de perfis que atendem aos filtros
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Retorna o número total de perfis sem retornar os dados.
    """
    filters = ProfessionalProfileSearchFilters(
        professional_profile_name=professional_profile_name,
        user_id=user_id,
        user_name=user_name,
        has_academic_background=has_academic_background,
        has_professional_experience=has_professional_experience,
        has_professional_courses=has_professional_courses
    ) if any([professional_profile_name, user_id, user_name, has_academic_background, has_professional_experience, has_professional_courses]) else None
    
    count = await profile_service.get_profiles_count(filters)
    return {"total": count, "filters_applied": filters is not None}

@router.get("/{profile_id}", response_model=ProfessionalProfileDetail)
async def get_profile(
    profile_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Obter perfil profissional por ID
    
    **Requer autenticação**
    
    Usuários podem ver apenas seus próprios perfis, exceto admins/recruiters.
    Retorna informações detalhadas incluindo estatísticas e completude.
    """
    profile = await profile_service.get_profile(profile_id)
    
    # Check ownership or admin privileges
    if not check_profile_ownership_or_admin(current_user, profile.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode acessar seus próprios perfis"
        )
    
    return profile

@router.put("/{profile_id}", response_model=ProfessionalProfileDetail)
async def update_profile(
    profile_id: UUID,
    profile_data: ProfessionalProfileUpdate,
    current_user: UserResponse = Depends(get_current_user),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Atualizar perfil profissional
    
    **Requer autenticação**
    
    Usuários podem atualizar apenas seus próprios perfis, exceto admins/recruiters.
    Permite atualização parcial dos dados do perfil.
    """
    # First get the profile to check ownership
    existing_profile = await profile_service.get_profile(profile_id)
    
    if not check_profile_ownership_or_admin(current_user, existing_profile.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode atualizar seus próprios perfis"
        )
    
    return await profile_service.update_profile(profile_id, profile_data)

@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Deletar perfil profissional (soft delete)
    
    **Requer autenticação**
    
    Usuários podem deletar apenas seus próprios perfis, exceto admins/recruiters.
    Marca o perfil como deletado sem remover do banco de dados.
    """
    # First get the profile to check ownership
    existing_profile = await profile_service.get_profile(profile_id)
    
    if not check_profile_ownership_or_admin(current_user, existing_profile.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode deletar seus próprios perfis"
        )
    
    await profile_service.delete_profile(profile_id)

# =============================================
# USER SPECIFIC ROUTES
# =============================================

@router.get("/user/{user_id}", response_model=List[ProfessionalProfileSummary])
async def get_user_profiles(
    user_id: UUID,
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(get_current_user),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Listar perfis profissionais de um usuário específico
    
    **Requer autenticação**
    
    Usuários podem ver apenas seus próprios perfis, exceto admins/recruiters.
    """
    if not check_profile_ownership_or_admin(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode acessar seus próprios perfis"
        )
    
    return await profile_service.get_user_profiles(user_id, skip=skip, limit=limit)

@router.get("/user/{user_id}/primary", response_model=ProfessionalProfileDetail)
async def get_user_primary_profile(
    user_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Obter perfil profissional principal do usuário
    
    **Requer autenticação**
    
    Retorna o perfil mais recente/principal do usuário.
    """
    if not check_profile_ownership_or_admin(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode acessar seus próprios perfis"
        )
    
    profile = await profile_service.get_user_primary_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não possui perfil profissional"
        )
    
    return profile

@router.post("/user/{user_id}/first-profile", response_model=ProfessionalProfileResponse)
async def create_user_first_profile(
    user_id: UUID,
    profile_name: str = Query(..., description="Nome do perfil profissional"),
    description: Optional[str] = Query(None, description="Descrição do perfil"),
    current_user: UserResponse = Depends(get_current_user),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Criar primeiro perfil profissional do usuário
    
    **Requer autenticação**
    
    **BR07**: Permite criação com informações mínimas.
    Endpoint específico para onboarding de novos usuários.
    """
    if not check_profile_ownership_or_admin(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode criar perfis para si mesmo"
        )
    
    return await profile_service.create_user_first_profile(user_id, profile_name, description)

# =============================================
# PROFILE COMPLETENESS ROUTES
# =============================================

@router.get("/{profile_id}/completeness", response_model=ProfileCompletenessInfo)
async def get_profile_completeness(
    profile_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Obter informações de completude do perfil
    
    **Requer autenticação**
    
    Retorna detalhes sobre a completude do perfil, itens faltando e sugestões.
    """
    # Check ownership
    profile = await profile_service.get_profile(profile_id)
    if not check_profile_ownership_or_admin(current_user, profile.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode acessar seus próprios perfis"
        )
    
    return await profile_service.get_profile_completeness_info(profile_id)

@router.get("/{profile_id}/suggestions")
async def get_improvement_suggestions(
    profile_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Obter sugestões de melhoria do perfil
    
    **Requer autenticação**
    
    Retorna sugestões personalizadas para melhorar o perfil baseadas na análise atual.
    """
    # Check ownership
    profile = await profile_service.get_profile(profile_id)
    if not check_profile_ownership_or_admin(current_user, profile.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode acessar seus próprios perfis"
        )
    
    suggestions = await profile_service.get_improvement_suggestions(profile_id)
    
    return {
        "profile_id": profile_id,
        "suggestions": suggestions,
        "total_suggestions": len(suggestions)
    }

# =============================================
# STATISTICS AND ANALYTICS ROUTES
# =============================================

@router.get("/{profile_id}/statistics", response_model=ProfessionalProfileStatistics)
async def get_profile_statistics(
    profile_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Obter estatísticas do perfil profissional
    
    **Requer autenticação**
    
    Retorna estatísticas detalhadas incluindo:
    - Total de candidaturas
    - Análises realizadas
    - Scores médio, máximo e mínimo
    - Áreas de destaque e melhoria
    """
    # Check ownership
    profile = await profile_service.get_profile(profile_id)
    if not check_profile_ownership_or_admin(current_user, profile.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode acessar seus próprios perfis"
        )
    
    return await profile_service.get_profile_statistics(profile_id)

@router.get("/analytics/top-performers")
async def get_top_performing_profiles(
    min_score: float = Query(80, ge=0, le=100, description="Score mínimo para considerar alto desempenho"),
    limit: int = Query(50, ge=1, le=200, description="Limite de perfis no ranking"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Ranking dos perfis com melhor desempenho
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Retorna os perfis com maior score médio nas análises.
    """
    performers = await profile_service.get_top_performing_profiles(min_score=min_score, limit=limit)
    
    return {
        "min_score": min_score,
        "total_profiles": len(performers),
        "top_performers": performers
    }

# =============================================
# VALIDATION ROUTES
# =============================================

@router.get("/{profile_id}/exists")
async def check_profile_exists(
    profile_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Verificar se perfil profissional existe
    
    **Requer autenticação**
    
    Retorna se o perfil existe sem retornar seus dados.
    """
    exists = await profile_service.profile_exists(profile_id)
    
    return {
        "exists": exists,
        "profile_id": profile_id
    }

@router.get("/user/{user_id}/has-profile")
async def check_user_has_profile(
    user_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Verificar se usuário possui perfil profissional
    
    **Requer autenticação**
    
    Usuários podem verificar apenas seus próprios perfis, exceto admins/recruiters.
    """
    if not check_profile_ownership_or_admin(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode verificar seus próprios perfis"
        )
    
    has_profile = await profile_service.user_has_profile(user_id)
    
    return {
        "user_id": user_id,
        "has_profile": has_profile,
        "message": "Usuário possui perfil profissional" if has_profile else "Usuário não possui perfil profissional"
    }

@router.get("/{profile_id}/ownership/{user_id}")
async def validate_profile_ownership(
    profile_id: UUID,
    user_id: UUID,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Validar propriedade do perfil
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Verifica se o perfil pertence ao usuário especificado.
    """
    is_owner = await profile_service.validate_profile_ownership(profile_id, user_id)
    
    return {
        "profile_id": profile_id,
        "user_id": user_id,
        "is_owner": is_owner,
        "message": "Perfil pertence ao usuário" if is_owner else "Perfil não pertence ao usuário"
    }

@router.get("/{profile_id}/can-delete")
async def check_can_delete_profile(
    profile_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    profile_service: ProfessionalProfileService = Depends(get_profile_service)
):
    """
    Verificar se perfil pode ser deletado
    
    **Requer autenticação**
    
    Verifica se o perfil pode ser deletado e retorna os motivos caso não possa.
    """
    # Check ownership
    profile = await profile_service.get_profile(profile_id)
    if not check_profile_ownership_or_admin(current_user, profile.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode verificar seus próprios perfis"
        )
    
    result = await profile_service.can_delete_profile(profile_id)
    
    return {
        "profile_id": profile_id,
        "can_delete": result["can_delete"],
        "reasons": result.get("reasons", []),
        "profile_name": result.get("profile_name"),
        "message": "Perfil pode ser deletado" if result["can_delete"] else "Perfil não pode ser deletado"
    }