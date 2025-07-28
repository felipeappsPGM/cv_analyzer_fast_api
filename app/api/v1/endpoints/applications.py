# =============================================
# app/api/v1/endpoints/applications.py
# =============================================
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
from uuid import UUID

from app.config.database import get_db
from app.services.application_service import ApplicationService
from app.schemas.application_job import (
    ApplicationJobCreate,
    ApplicationJobUpdate,
    ApplicationJobResponse,
    ApplicationJobDetail,
    ApplicationJobSummary,
    ApplicationJobSearchFilters,
    ApplicationJobStatistics,
    ApplicationJobRanking,
    ApplicationJobBulkCreate,
    ApplicationJobBulkResponse,
    ApplicationStatusEnum
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
async def get_application_service(db: AsyncSession = Depends(get_db)) -> ApplicationService:
    return ApplicationService(db)

def check_application_ownership_or_admin(current_user: UserResponse, application_user_id: UUID):
    """Helper to check if user owns application or is admin/recruiter"""
    if current_user.user_type in ["admin", "recruiter", "company_owner"]:
        return True
    return current_user.user_id == application_user_id

# =============================================
# APPLICATION CRUD ROUTES
# =============================================

@router.post("/apply", response_model=ApplicationJobResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_job(
    job_id: UUID,
    professional_profile_id: Optional[UUID] = None,
    current_user: UserResponse = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Candidatar-se a uma vaga
    
    **Requer autenticação**
    
    **BR08**: Cada usuário pode se candidatar apenas uma vez por vaga
    
    - **job_id**: ID da vaga
    - **professional_profile_id**: ID do perfil profissional (opcional, usa o principal se não informado)
    
    Se não informado, usará o perfil profissional principal do usuário.
    """
    return await application_service.apply_to_job(
        user_id=current_user.user_id,
        job_id=job_id,
        professional_profile_id=professional_profile_id
    )

@router.post("/bulk-apply", response_model=ApplicationJobBulkResponse)
async def bulk_apply_to_jobs(
    bulk_data: ApplicationJobBulkCreate,
    current_user: UserResponse = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Candidatar-se a múltiplas vagas de uma vez
    
    **Requer autenticação**
    
    - **user_id**: ID do usuário (deve ser o próprio usuário)
    - **job_ids**: Lista de IDs das vagas (máximo 50)
    - **professional_profile_id**: ID do perfil profissional
    
    Retorna quais candidaturas foram criadas com sucesso e quais falharam.
    """
    # Check if user can apply for this user_id
    if current_user.user_type not in ["admin", "recruiter", "company_owner"]:
        if current_user.user_id != bulk_data.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você só pode se candidatar para si mesmo"
            )
    
    return await application_service.bulk_apply_to_jobs(bulk_data)

@router.get("/", response_model=List[ApplicationJobResponse])
async def get_applications(
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Listar todas as candidaturas com paginação
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    - **skip**: Número de registros a pular (padrão: 0)
    - **limit**: Limite de registros retornados (padrão: 100, máximo: 1000)
    """
    return await application_service.get_applications(skip=skip, limit=limit)

@router.get("/search", response_model=List[ApplicationJobSummary])
async def search_applications(
    user_id: Optional[UUID] = Query(None, description="Filtrar por usuário"),
    job_id: Optional[UUID] = Query(None, description="Filtrar por vaga"),
    company_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    professional_profile_id: Optional[UUID] = Query(None, description="Filtrar por perfil profissional"),
    status: Optional[ApplicationStatusEnum] = Query(None, description="Filtrar por status"),
    has_analysis: Optional[bool] = Query(None, description="Filtrar por análise"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Pontuação mínima"),
    max_score: Optional[float] = Query(None, ge=0, le=100, description="Pontuação máxima"),
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Buscar candidaturas com filtros avançados
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Permite filtrar candidaturas por diversos critérios incluindo scores de análise.
    """
    filters = ApplicationJobSearchFilters(
        user_id=user_id,
        job_id=job_id,
        company_id=company_id,
        professional_profile_id=professional_profile_id,
        status=status,
        has_analysis=has_analysis,
        min_score=min_score,
        max_score=max_score
    )
    
    return await application_service.search_applications(filters, skip=skip, limit=limit)

@router.get("/count")
async def get_applications_count(
    user_id: Optional[UUID] = Query(None, description="Filtrar por usuário"),
    job_id: Optional[UUID] = Query(None, description="Filtrar por vaga"),
    company_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    has_analysis: Optional[bool] = Query(None, description="Filtrar por análise"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Contar total de candidaturas que atendem aos filtros
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Retorna o número total de candidaturas sem retornar os dados.
    """
    filters = ApplicationJobSearchFilters(
        user_id=user_id,
        job_id=job_id,
        company_id=company_id,
        has_analysis=has_analysis
    ) if any([user_id, job_id, company_id, has_analysis]) else None
    
    count = await application_service.get_applications_count(filters)
    return {"total": count, "filters_applied": filters is not None}

@router.get("/{application_id}", response_model=ApplicationJobDetail)
async def get_application(
    application_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Obter candidatura por ID
    
    **Requer autenticação**
    
    Usuários podem ver apenas suas próprias candidaturas, exceto admins/recruiters.
    Retorna informações detalhadas incluindo análises.
    """
    application = await application_service.get_application(application_id)
    
    # Check ownership or admin privileges
    if not check_application_ownership_or_admin(current_user, application.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode acessar suas próprias candidaturas"
        )
    
    return application

@router.put("/{application_id}", response_model=ApplicationJobDetail)
async def update_application(
    application_id: UUID,
    application_data: ApplicationJobUpdate,
    current_user: UserResponse = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Atualizar candidatura
    
    **Requer autenticação**
    
    Usuários podem atualizar apenas suas próprias candidaturas, exceto admins/recruiters.
    Permite atualização do perfil profissional associado.
    """
    # First get the application to check ownership
    existing_application = await application_service.get_application(application_id)
    
    if not check_application_ownership_or_admin(current_user, existing_application.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode atualizar suas próprias candidaturas"
        )
    
    return await application_service.update_application(application_id, application_data)

@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def withdraw_application(
    application_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Retirar candidatura (soft delete)
    
    **Requer autenticação**
    
    Usuários podem retirar apenas suas próprias candidaturas.
    Marca a candidatura como retirada sem remover do banco de dados.
    """
    await application_service.withdraw_application(application_id, current_user.user_id)

# =============================================
# USER SPECIFIC ROUTES
# =============================================

@router.get("/user/{user_id}", response_model=List[ApplicationJobSummary])
async def get_user_applications(
    user_id: UUID,
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Listar candidaturas de um usuário específico
    
    **Requer autenticação**
    
    Usuários podem ver apenas suas próprias candidaturas, exceto admins/recruiters.
    """
    if not check_application_ownership_or_admin(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode acessar suas próprias candidaturas"
        )
    
    return await application_service.get_user_applications(user_id, skip=skip, limit=limit)

@router.get("/user/{user_id}/count")
async def get_user_application_count(
    user_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Contar candidaturas de um usuário
    
    **Requer autenticação**
    
    Usuários podem verificar apenas suas próprias candidaturas, exceto admins/recruiters.
    """
    if not check_application_ownership_or_admin(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode acessar suas próprias candidaturas"
        )
    
    count = await application_service.get_user_application_count(user_id)
    return {"user_id": user_id, "total_applications": count}

@router.get("/user/{user_id}/statistics")
async def get_user_application_statistics(
    user_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Obter estatísticas de candidaturas do usuário
    
    **Requer autenticação**
    
    Retorna estatísticas detalhadas incluindo total, analisadas, pendentes e score médio.
    """
    if not check_application_ownership_or_admin(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode acessar suas próprias estatísticas"
        )
    
    stats = await application_service.get_user_application_statistics(user_id)
    
    return {
        "user_id": user_id,
        **stats
    }

# =============================================
# JOB SPECIFIC ROUTES
# =============================================

@router.get("/job/{job_id}", response_model=List[ApplicationJobSummary])
async def get_job_applications(
    job_id: UUID,
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Listar candidaturas de uma vaga específica
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Retorna todas as candidaturas para a vaga especificada.
    """
    return await application_service.get_job_applications(job_id, skip=skip, limit=limit)

@router.get("/job/{job_id}/count")
async def get_job_application_count(
    job_id: UUID,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Contar candidaturas de uma vaga
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Retorna o número total de candidaturas para a vaga.
    """
    count = await application_service.get_job_application_count(job_id)
    return {"job_id": job_id, "total_applications": count}

# =============================================
# VALIDATION AND BUSINESS RULES ROUTES
# =============================================

@router.get("/can-apply/{job_id}")
async def check_can_apply_to_job(
    job_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Verificar se usuário pode se candidatar à vaga
    
    **Requer autenticação**
    
    Verifica BR08 (uma candidatura por vaga) e outros requisitos.
    Retorna se pode se candidatar e os motivos caso não possa.
    """
    result = await application_service.can_apply_to_job(current_user.user_id, job_id)
    
    return {
        "user_id": current_user.user_id,
        "job_id": job_id,
        "can_apply": result["can_apply"],
        "reasons": result.get("reasons", []),
        "warnings": result.get("warnings", []),
        "job_name": result.get("job_name"),
        "has_profile": result.get("has_profile", False),
        "has_curriculum": result.get("has_curriculum", False),
        "message": "Pode se candidatar" if result["can_apply"] else "Não pode se candidatar"
    }

@router.get("/user/{user_id}/applied-to/{job_id}")
async def check_user_applied_to_job(
    user_id: UUID,
    job_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Verificar se usuário já se candidatou à vaga (BR08)
    
    **Requer autenticação**
    
    Usuários podem verificar apenas suas próprias candidaturas, exceto admins/recruiters.
    """
    if not check_application_ownership_or_admin(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode verificar suas próprias candidaturas"
        )
    
    has_applied = await application_service.user_has_applied_to_job(user_id, job_id)
    
    return {
        "user_id": user_id,
        "job_id": job_id,
        "has_applied": has_applied,
        "message": "Usuário já se candidatou para esta vaga" if has_applied else "Usuário não se candidatou para esta vaga"
    }

@router.get("/{application_id}/exists")
async def check_application_exists(
    application_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Verificar se candidatura existe
    
    **Requer autenticação**
    
    Retorna se a candidatura existe sem retornar seus dados.
    """
    exists = await application_service.application_exists(application_id)
    
    return {
        "exists": exists,
        "application_id": application_id
    }

# =============================================
# ANALYTICS AND STATISTICS ROUTES
# =============================================

@router.get("/analytics/statistics", response_model=ApplicationJobStatistics)
async def get_application_statistics(
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Obter estatísticas gerais de candidaturas
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Retorna estatísticas abrangentes do sistema de candidaturas.
    """
    return await application_service.get_application_statistics()

@router.get("/analytics/trends")
async def get_application_trends(
    months: int = Query(12, ge=1, le=24, description="Número de meses para análise"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Obter tendências de candidaturas ao longo do tempo
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Retorna dados de candidaturas por mês para análise de tendências.
    """
    trends = await application_service.get_application_trends(months=months)
    
    return {
        "period_months": months,
        "trends": trends,
        "total_applications_in_period": sum(trend.get("applications", 0) for trend in trends)
    }

# =============================================
# CONVENIENCE ROUTES
# =============================================

@router.get("/my-applications", response_model=List[ApplicationJobSummary])
async def get_my_applications(
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Listar minhas candidaturas (endpoint de conveniência)
    
    **Requer autenticação**
    
    Retorna as candidaturas do usuário atual.
    """
    return await application_service.get_user_applications(current_user.user_id, skip=skip, limit=limit)

@router.get("/my-statistics")
async def get_my_application_statistics(
    current_user: UserResponse = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Obter minhas estatísticas de candidaturas (endpoint de conveniência)
    
    **Requer autenticação**
    
    Retorna estatísticas das candidaturas do usuário atual.
    """
    stats = await application_service.get_user_application_statistics(current_user.user_id)
    
    return {
        "user_id": current_user.user_id,
        **stats
    }

@router.post("/quick-apply/{job_id}", response_model=ApplicationJobResponse)
async def quick_apply_to_job(
    job_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service)
):
    """
    Candidatura rápida (endpoint de conveniência)
    
    **Requer autenticação**
    
    Se candidata usando o perfil profissional principal do usuário.
    """
    return await application_service.apply_to_job(
        user_id=current_user.user_id,
        job_id=job_id,
        professional_profile_id=None  # Uses primary profile
    )