# =============================================
# app/api/v1/endpoints/jobs.py
# =============================================
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
from uuid import UUID

from app.config.database import get_db
from app.services.job_service import JobService
from app.schemas.job import (
    JobCreate, 
    JobUpdate, 
    JobResponse, 
    JobDetail, 
    JobSummary,
    JobSearchFilters,
    JobStatistics,
    JobCandidateRanking
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
async def get_job_service(db: AsyncSession = Depends(get_db)) -> JobService:
    return JobService(db)

# =============================================
# JOB CRUD ROUTES
# =============================================

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    job_service: JobService = Depends(get_job_service)
):
    """
    Criar nova vaga
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    - **job_name**: Nome da vaga
    - **activities**: Atividades da vaga (opcional)
    - **pre_requisites**: Pré-requisitos obrigatórios (opcional)
    - **differentials**: Diferenciais desejados (opcional)
    - **code_vacancy_job**: Código único da vaga
    - **company_id**: ID da empresa
    """
    return await job_service.create_job(job_data, create_user_id=current_user.user_id)

@router.get("/", response_model=List[JobResponse])
async def get_jobs(
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Listar vagas ativas com paginação
    
    **Requer autenticação**
    
    - **skip**: Número de registros a pular (padrão: 0)
    - **limit**: Limite de registros retornados (padrão: 100, máximo: 1000)
    """
    return await job_service.get_jobs(skip=skip, limit=limit)

@router.get("/search", response_model=List[JobSummary])
async def search_jobs(
    job_name: Optional[str] = Query(None, description="Filtrar por nome da vaga"),
    company_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    company_name: Optional[str] = Query(None, description="Filtrar por nome da empresa"),
    keywords: Optional[str] = Query(None, description="Palavras-chave em atividades, pré-requisitos ou diferenciais"),
    code_vacancy_job: Optional[str] = Query(None, description="Filtrar por código da vaga"),
    is_active: Optional[bool] = Query(True, description="Filtrar vagas ativas"),
    has_applications: Optional[bool] = Query(None, description="Filtrar vagas com candidaturas"),
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Buscar vagas com filtros avançados
    
    **Requer autenticação**
    
    Permite filtrar vagas por diversos critérios incluindo palavras-chave.
    """
    filters = JobSearchFilters(
        job_name=job_name,
        company_id=company_id,
        company_name=company_name,
        keywords=keywords,
        code_vacancy_job=code_vacancy_job,
        is_active=is_active,
        has_applications=has_applications
    )
    
    return await job_service.search_jobs(filters, skip=skip, limit=limit)

@router.get("/search/keywords", response_model=List[JobSummary])
async def search_jobs_by_keywords(
    keywords: str = Query(..., description="Palavras-chave para busca"),
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Buscar vagas por palavras-chave
    
    **Requer autenticação**
    
    Busca palavras-chave no nome da vaga, atividades, pré-requisitos e diferenciais.
    """
    return await job_service.search_jobs_by_keywords(keywords, skip=skip, limit=limit)

@router.get("/count")
async def get_jobs_count(
    job_name: Optional[str] = Query(None, description="Filtrar por nome da vaga"),
    company_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    company_name: Optional[str] = Query(None, description="Filtrar por nome da empresa"),
    keywords: Optional[str] = Query(None, description="Palavras-chave"),
    is_active: Optional[bool] = Query(True, description="Filtrar vagas ativas"),
    has_applications: Optional[bool] = Query(None, description="Filtrar vagas com candidaturas"),
    current_user: UserResponse = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Contar total de vagas que atendem aos filtros
    
    **Requer autenticação**
    
    Retorna o número total de vagas sem retornar os dados.
    """
    filters = JobSearchFilters(
        job_name=job_name,
        company_id=company_id,
        company_name=company_name,
        keywords=keywords,
        is_active=is_active,
        has_applications=has_applications
    ) if any([job_name, company_id, company_name, keywords, is_active, has_applications]) else None
    
    count = await job_service.get_jobs_count(filters)
    return {"total": count, "filters_applied": filters is not None}

@router.get("/{job_id}", response_model=JobDetail)
async def get_job(
    job_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Obter vaga por ID
    
    **Requer autenticação**
    
    Retorna informações detalhadas da vaga incluindo estatísticas.
    """
    return await job_service.get_job(job_id)

@router.get("/{job_id}/details", response_model=JobDetail)
async def get_job_details(
    job_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Obter detalhes completos da vaga
    
    **Requer autenticação**
    
    Retorna informações detalhadas da vaga com todos os relacionamentos carregados.
    """
    return await job_service.get_job_details(job_id)

@router.put("/{job_id}", response_model=JobDetail)
async def update_job(
    job_id: UUID,
    job_data: JobUpdate,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    job_service: JobService = Depends(get_job_service)
):
    """
    Atualizar vaga
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Permite atualização parcial dos dados da vaga.
    Apenas os campos fornecidos serão atualizados.
    """
    return await job_service.update_job(job_id, job_data)

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def close_job(
    job_id: UUID,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    job_service: JobService = Depends(get_job_service)
):
    """
    Fechar vaga (soft delete)
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Marca a vaga como fechada sem remover do banco de dados.
    Vagas fechadas não aceitam mais candidaturas.
    """
    await job_service.close_job(job_id)

# =============================================
# COMPANY SPECIFIC ROUTES
# =============================================

@router.get("/company/{company_id}", response_model=List[JobSummary])
async def get_company_jobs(
    company_id: UUID,
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Listar vagas de uma empresa específica
    
    **Requer autenticação**
    
    Retorna todas as vagas (ativas e fechadas) de uma empresa.
    """
    return await job_service.get_company_jobs(company_id, skip=skip, limit=limit)

# =============================================
# APPLICATION AND RANKING ROUTES
# =============================================

@router.get("/{job_id}/applications")
async def get_job_applications(
    job_id: UUID,
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    job_service: JobService = Depends(get_job_service)
):
    """
    Listar candidaturas de uma vaga
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Retorna todas as candidaturas para a vaga especificada.
    """
    applications = await job_service.get_job_applications(job_id, skip=skip, limit=limit)
    
    return {
        "job_id": job_id,
        "total_applications": len(applications),
        "applications": applications,
        "page_info": {
            "skip": skip,
            "limit": limit,
            "has_more": len(applications) == limit
        }
    }

@router.get("/{job_id}/ranking", response_model=List[JobCandidateRanking])
async def get_job_ranking(
    job_id: UUID,
    limit: int = Query(50, ge=1, le=200, description="Limite de candidatos no ranking"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    job_service: JobService = Depends(get_job_service)
):
    """
    Obter ranking de candidatos da vaga
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Retorna os candidatos ordenados por score total de compatibilidade.
    Apenas candidatos com análise concluída são incluídos.
    """
    return await job_service.get_job_ranking(job_id, limit=limit)

# =============================================
# STATISTICS AND ANALYTICS ROUTES
# =============================================

@router.get("/{job_id}/statistics", response_model=JobStatistics)
async def get_job_statistics(
    job_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Obter estatísticas da vaga
    
    **Requer autenticação**
    
    Retorna estatísticas detalhadas incluindo:
    - Total de candidaturas
    - Candidaturas analisadas vs pendentes
    - Scores médio, máximo e mínimo
    - Melhor candidato
    - Tendências de candidaturas
    """
    return await job_service.get_job_statistics(job_id)

@router.get("/{job_id}/trends")
async def get_applications_trends(
    job_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Número de dias para análise de tendências"),
    current_user: UserResponse = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Obter tendências de candidaturas
    
    **Requer autenticação**
    
    Retorna dados de candidaturas por dia para análise de tendências.
    Útil para gráficos e análises temporais.
    """
    trends = await job_service.get_applications_trends(job_id, days=days)
    
    return {
        "job_id": job_id,
        "period_days": days,
        "trends": trends,
        "total_applications_in_period": sum(trend.get("applications", 0) for trend in trends)
    }

@router.get("/{job_id}/similar", response_model=List[JobSummary])
async def get_similar_jobs(
    job_id: UUID,
    limit: int = Query(5, ge=1, le=20, description="Limite de vagas similares"),
    current_user: UserResponse = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Obter vagas similares
    
    **Requer autenticação**
    
    Retorna vagas similares à vaga especificada.
    Útil para recomendações e análises comparativas.
    """
    return await job_service.get_similar_jobs(job_id, limit=limit)

# =============================================
# VALIDATION ROUTES
# =============================================

@router.get("/{job_id}/exists")
async def check_job_exists(
    job_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Verificar se vaga existe
    
    **Requer autenticação**
    
    Retorna se a vaga existe sem retornar seus dados.
    """
    exists = await job_service.job_exists(job_id)
    is_active = await job_service.job_is_active(job_id) if exists else False
    
    return {
        "exists": exists,
        "is_active": is_active,
        "job_id": job_id
    }

@router.get("/validate/code/{code_vacancy_job}")
async def validate_job_code_availability(
    code_vacancy_job: str,
    exclude_job_id: Optional[UUID] = Query(None, description="ID da vaga a excluir da validação"),
    current_user: UserResponse = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Validar disponibilidade de código da vaga
    
    **Requer autenticação**
    
    Verifica se o código da vaga está disponível para uso.
    Útil para validação em tempo real durante criação/edição.
    """
    is_available = await job_service.validate_job_code_availability(code_vacancy_job, exclude_job_id)
    
    return {
        "code_vacancy_job": code_vacancy_job,
        "is_available": is_available,
        "message": "Código disponível" if is_available else "Código já está em uso"
    }

@router.get("/{job_id}/can-close")
async def check_can_close_job(
    job_id: UUID,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    job_service: JobService = Depends(get_job_service)
):
    """
    Verificar se vaga pode ser fechada
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Verifica se a vaga pode ser fechada e retorna os motivos caso não possa.
    """
    result = await job_service.can_close_job(job_id)
    
    return {
        "job_id": job_id,
        "can_close": result["can_close"],
        "reasons": result.get("reasons", []),
        "job_name": result.get("job_name"),
        "total_applications": result.get("total_applications", 0),
        "message": "Vaga pode ser fechada" if result["can_close"] else "Vaga não pode ser fechada"
    }

@router.get("/{job_id}/is-active")
async def check_job_is_active(
    job_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Verificar se vaga está ativa
    
    **Requer autenticação**
    
    Verifica se a vaga está ativa (não foi fechada).
    """
    is_active = await job_service.job_is_active(job_id)
    
    return {
        "job_id": job_id,
        "is_active": is_active,
        "message": "Vaga está ativa" if is_active else "Vaga está fechada ou não existe"
    }