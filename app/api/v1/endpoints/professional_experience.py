# =============================================
# app/api/v1/endpoints/professional_experience.py
# =============================================
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.config.database import get_db
from app.services.professional_experience_service import ProfessionalExperienceService
from app.schemas.professional_experience import (
    ProfessionalExperienceCreate,
    ProfessionalExperienceUpdate,
    ProfessionalExperienceResponse,
    ProfessionalExperienceDetail,
    ProfessionalExperienceSummary,
    ProfessionalExperienceSearchFilters,
    ProfessionalExperienceStatistics,
    EmploymentTypeEnum
)

# =============================================
# ROUTER INSTANCE
# =============================================
router = APIRouter()

# =============================================
# DEPENDENCIES
# =============================================
async def get_experience_service(db: AsyncSession = Depends(get_db)) -> ProfessionalExperienceService:
    return ProfessionalExperienceService(db)

# =============================================
# BASIC CRUD ROUTES
# =============================================

@router.post("/", response_model=ProfessionalExperienceResponse, status_code=status.HTTP_201_CREATED)
async def create_professional_experience(
    experience_data: ProfessionalExperienceCreate,
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Criar nova experiência profissional
    
    - **job_title**: Cargo/Função
    - **company_name**: Nome da empresa
    - **employment_type**: Tipo de contratação (CLT, PJ, Estágio, etc.)
    - **location**: Localização do trabalho (opcional)
    - **start_date**: Data de início
    - **end_date**: Data de fim (null se atual)
    - **is_current**: Se é o trabalho atual
    - **user_id**: ID do usuário
    """
    return await experience_service.create_experience(experience_data)

@router.get("/", response_model=List[ProfessionalExperienceResponse])
async def get_professional_experiences(
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Listar experiências profissionais com paginação
    """
    return await experience_service.get_experiences(skip=skip, limit=limit)

@router.get("/{experience_id}", response_model=ProfessionalExperienceDetail)
async def get_professional_experience(
    experience_id: UUID,
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Obter experiência profissional por ID
    
    Retorna informações detalhadas da experiência incluindo duração calculada.
    """
    return await experience_service.get_experience(experience_id)

@router.put("/{experience_id}", response_model=ProfessionalExperienceDetail)
async def update_professional_experience(
    experience_id: UUID,
    experience_data: ProfessionalExperienceUpdate,
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Atualizar experiência profissional
    
    Permite atualização parcial dos dados da experiência.
    Apenas os campos fornecidos serão atualizados.
    """
    return await experience_service.update_experience(experience_id, experience_data)

@router.delete("/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_professional_experience(
    experience_id: UUID,
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Deletar experiência profissional (soft delete)
    
    Marca a experiência como deletada sem remover do banco de dados.
    """
    await experience_service.delete_experience(experience_id)

# =============================================
# USER SPECIFIC ROUTES
# =============================================

@router.get("/user/{user_id}", response_model=List[ProfessionalExperienceSummary])
async def get_user_professional_experiences(
    user_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Obter todas as experiências profissionais de um usuário
    
    Retorna lista resumida das experiências do usuário com paginação.
    Ordenado por data de início (mais recente primeiro).
    """
    return await experience_service.get_user_experiences(user_id, skip=skip, limit=limit)

@router.get("/user/{user_id}/current", response_model=Optional[ProfessionalExperienceDetail])
async def get_user_current_experience(
    user_id: UUID,
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Obter experiência profissional atual de um usuário
    
    Retorna a experiência marcada como atual (is_current=True).
    Retorna null se o usuário não possui experiência atual.
    """
    return await experience_service.get_user_current_experience(user_id)

@router.get("/user/{user_id}/timeline", response_model=List[dict])
async def get_user_experience_timeline(
    user_id: UUID,
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Obter linha do tempo de experiências profissionais do usuário
    
    Retorna a progressão na carreira do usuário ordenada cronologicamente
    com informações de duração e posicionamento.
    """
    return await experience_service.get_user_experience_timeline(user_id)

# =============================================
# SEARCH AND FILTERING ROUTES
# =============================================

@router.get("/search/", response_model=List[ProfessionalExperienceSummary])
async def search_professional_experiences(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[UUID] = Query(None, description="Filtrar por usuário"),
    job_title: Optional[str] = Query(None, description="Filtrar por cargo"),
    company_name: Optional[str] = Query(None, description="Filtrar por empresa"),
    employment_type: Optional[EmploymentTypeEnum] = Query(None, description="Filtrar por tipo de contratação"),
    location: Optional[str] = Query(None, description="Filtrar por localização"),
    is_current: Optional[bool] = Query(None, description="Filtrar trabalhos atuais"),
    min_duration_months: Optional[int] = Query(None, ge=0, description="Duração mínima em meses"),
    max_duration_months: Optional[int] = Query(None, ge=0, description="Duração máxima em meses"),
    start_date_after: Optional[date] = Query(None, description="Data de início posterior a"),
    start_date_before: Optional[date] = Query(None, description="Data de início anterior a"),
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Buscar experiências profissionais com filtros avançados
    
    Permite filtrar experiências por diversos critérios como cargo, empresa,
    tipo de contratação, localização, duração, período, etc.
    """
    filters = ProfessionalExperienceSearchFilters(
        user_id=user_id,
        job_title=job_title,
        company_name=company_name,
        employment_type=employment_type,
        location=location,
        is_current=is_current,
        min_duration_months=min_duration_months,
        max_duration_months=max_duration_months,
        start_date_after=start_date_after,
        start_date_before=start_date_before
    )
    
    return await experience_service.search_experiences(filters, skip=skip, limit=limit)

@router.get("/search/count", response_model=dict)
async def get_experiences_search_count(
    user_id: Optional[UUID] = Query(None),
    job_title: Optional[str] = Query(None),
    company_name: Optional[str] = Query(None),
    employment_type: Optional[EmploymentTypeEnum] = Query(None),
    is_current: Optional[bool] = Query(None),
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Contar experiências profissionais que atendem aos filtros
    
    Retorna o número total de experiências que correspondem aos critérios de busca.
    """
    filters = ProfessionalExperienceSearchFilters(
        user_id=user_id,
        job_title=job_title,
        company_name=company_name,
        employment_type=employment_type,
        is_current=is_current
    )
    
    count = await experience_service.get_experiences_count(filters)
    return {"total_count": count}

# =============================================
# STATISTICS AND ANALYTICS ROUTES
# =============================================

@router.get("/statistics/user/{user_id}", response_model=ProfessionalExperienceStatistics)
async def get_user_experience_statistics(
    user_id: UUID,
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Obter estatísticas de experiências profissionais de um usuário
    
    Retorna métricas completas sobre as experiências do usuário incluindo:
    - Total de experiências e posições atuais
    - Duração total e média das experiências
    - Empresas onde trabalhou
    - Cargos ocupados
    - Tipo de contratação mais comum
    - Progressão na carreira
    """
    return await experience_service.get_user_statistics(user_id)

@router.get("/analytics/user/{user_id}/total-years", response_model=dict)
async def get_user_total_experience_years(
    user_id: UUID,
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Calcular total de anos de experiência do usuário
    
    Retorna o total de anos de experiência profissional acumulada.
    """
    total_years = await experience_service.get_total_experience_years(user_id)
    return {"user_id": user_id, "total_experience_years": total_years}

@router.get("/analytics/user/{user_id}/seniority", response_model=dict)
async def get_user_seniority_level(
    user_id: UUID,
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Calcular nível de senioridade do usuário
    
    Baseado no total de anos de experiência, retorna o nível:
    - Júnior (< 1 ano)
    - Pleno (1-3 anos)
    - Sênior (3-7 anos)
    - Especialista (7+ anos)
    """
    seniority = await experience_service.calculate_seniority_level(user_id)
    return {"user_id": user_id, "seniority_level": seniority}

@router.get("/analytics/user/{user_id}/companies", response_model=dict)
async def get_user_companies_worked(
    user_id: UUID,
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Obter lista de empresas onde o usuário trabalhou
    
    Retorna lista única de todas as empresas das experiências do usuário.
    """
    companies = await experience_service.get_companies_worked(user_id)
    return {"user_id": user_id, "companies_worked": companies}

@router.get("/analytics/user/{user_id}/recommendations", response_model=dict)
async def get_user_job_recommendations(
    user_id: UUID,
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Obter recomendações de vagas baseadas na experiência
    
    Analisa o histórico profissional e sugere próximos passos na carreira.
    """
    recommendations = await experience_service.get_job_recommendations(user_id)
    return {"user_id": user_id, "job_recommendations": recommendations}

# =============================================
# VALIDATION HELPER ROUTES
# =============================================

@router.get("/{experience_id}/exists", response_model=dict)
async def check_experience_exists(
    experience_id: UUID,
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Verificar se experiência profissional existe
    
    Retorna se a experiência existe sem retornar seus dados.
    """
    exists = await experience_service.experience_exists(experience_id)
    return {"exists": exists, "experience_id": experience_id}

@router.get("/user/{user_id}/has-experiences", response_model=dict)
async def check_user_has_experiences(
    user_id: UUID,
    experience_service: ProfessionalExperienceService = Depends(get_experience_service)
):
    """
    Verificar se usuário possui experiências profissionais
    
    Retorna se o usuário tem pelo menos uma experiência cadastrada.
    """
    has_experiences = await experience_service.user_has_experiences(user_id)
    return {"has_experiences": has_experiences, "user_id": user_id}