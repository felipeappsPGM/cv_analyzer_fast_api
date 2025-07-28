# =============================================
# app/api/v1/endpoints/academic_background.py
# =============================================
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.config.database import get_db
from app.services.academic_background_service import AcademicBackgroundService
from app.schemas.academic_background import (
    AcademicBackgroundCreate,
    AcademicBackgroundUpdate,
    AcademicBackgroundResponse,
    AcademicBackgroundDetail,
    AcademicBackgroundSummary,
    AcademicBackgroundSearchFilters,
    AcademicBackgroundStatistics,
    DegreeTypeEnum,
    AcademicStatusEnum
)

# =============================================
# ROUTER INSTANCE
# =============================================
router = APIRouter()

# =============================================
# DEPENDENCIES
# =============================================
async def get_academic_service(db: AsyncSession = Depends(get_db)) -> AcademicBackgroundService:
    return AcademicBackgroundService(db)

# =============================================
# BASIC CRUD ROUTES
# =============================================

@router.post("/", response_model=AcademicBackgroundResponse, status_code=status.HTTP_201_CREATED)
async def create_academic_background(
    academic_data: AcademicBackgroundCreate,
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Criar nova formação acadêmica
    
    - **degree_name**: Nome do curso/diploma
    - **degree_type**: Tipo de formação (Graduação, Mestrado, Doutorado, etc.)
    - **field_of_study**: Área de estudo
    - **institution_name**: Nome da instituição
    - **start_date**: Data de início
    - **end_date**: Data de conclusão (opcional se em andamento)
    - **user_id**: ID do usuário
    """
    return await academic_service.create_academic_background(academic_data)

@router.get("/", response_model=List[AcademicBackgroundResponse])
async def get_academic_backgrounds(
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Listar formações acadêmicas com paginação
    """
    return await academic_service.get_academic_backgrounds(skip=skip, limit=limit)

@router.get("/{academic_id}", response_model=AcademicBackgroundDetail)
async def get_academic_background(
    academic_id: UUID,
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Obter formação acadêmica por ID
    
    Retorna informações detalhadas da formação incluindo duração calculada e status.
    """
    return await academic_service.get_academic_background(academic_id)

@router.put("/{academic_id}", response_model=AcademicBackgroundDetail)
async def update_academic_background(
    academic_id: UUID,
    academic_data: AcademicBackgroundUpdate,
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Atualizar formação acadêmica
    
    Permite atualização parcial dos dados da formação.
    Apenas os campos fornecidos serão atualizados.
    """
    return await academic_service.update_academic_background(academic_id, academic_data)

@router.delete("/{academic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_academic_background(
    academic_id: UUID,
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Deletar formação acadêmica (soft delete)
    
    Marca a formação como deletada sem remover do banco de dados.
    """
    await academic_service.delete_academic_background(academic_id)

# =============================================
# USER SPECIFIC ROUTES
# =============================================

@router.get("/user/{user_id}", response_model=List[AcademicBackgroundSummary])
async def get_user_academic_backgrounds(
    user_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Obter todas as formações acadêmicas de um usuário
    
    Retorna lista resumida das formações do usuário com paginação.
    Ordenado por data de início (mais recente primeiro).
    """
    return await academic_service.get_user_academic_backgrounds(user_id, skip=skip, limit=limit)

@router.get("/user/{user_id}/highest-degree", response_model=Optional[AcademicBackgroundDetail])
async def get_user_highest_degree(
    user_id: UUID,
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Obter a maior formação acadêmica de um usuário
    
    Retorna a formação de mais alto nível do usuário baseado na hierarquia:
    Pós-doutorado > Doutorado > Mestrado > MBA > Especialização > 
    Pós-graduação > Graduação > Tecnólogo > Técnico > Ensino Médio
    """
    return await academic_service.get_user_highest_degree(user_id)

@router.get("/user/{user_id}/progression", response_model=List[dict])
async def get_user_degree_progression(
    user_id: UUID,
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Obter progressão acadêmica do usuário
    
    Retorna a evolução educacional do usuário ordenada cronologicamente
    com informações de duração e status de conclusão.
    """
    return await academic_service.get_user_degree_progression(user_id)

# =============================================
# SEARCH AND FILTERING ROUTES
# =============================================

@router.get("/search/", response_model=List[AcademicBackgroundSummary])
async def search_academic_backgrounds(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[UUID] = Query(None, description="Filtrar por usuário"),
    degree_name: Optional[str] = Query(None, description="Filtrar por nome do curso"),
    degree_type: Optional[DegreeTypeEnum] = Query(None, description="Filtrar por tipo de formação"),
    field_of_study: Optional[str] = Query(None, description="Filtrar por área de estudo"),
    institution_name: Optional[str] = Query(None, description="Filtrar por instituição"),
    status: Optional[AcademicStatusEnum] = Query(None, description="Filtrar por status"),
    is_completed: Optional[bool] = Query(None, description="Filtrar formações concluídas"),
    min_duration_months: Optional[int] = Query(None, ge=0, description="Duração mínima em meses"),
    max_duration_months: Optional[int] = Query(None, ge=0, description="Duração máxima em meses"),
    start_date_after: Optional[date] = Query(None, description="Data de início posterior a"),
    start_date_before: Optional[date] = Query(None, description="Data de início anterior a"),
    graduation_year: Optional[int] = Query(None, ge=1950, le=2030, description="Ano de formatura"),
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Buscar formações acadêmicas com filtros avançados
    
    Permite filtrar formações por diversos critérios como nome do curso, tipo,
    área de estudo, instituição, status, duração, período, ano de formatura, etc.
    """
    filters = AcademicBackgroundSearchFilters(
        user_id=user_id,
        degree_name=degree_name,
        degree_type=degree_type,
        field_of_study=field_of_study,
        institution_name=institution_name,
        status=status,
        is_completed=is_completed,
        min_duration_months=min_duration_months,
        max_duration_months=max_duration_months,
        start_date_after=start_date_after,
        start_date_before=start_date_before,
        graduation_year=graduation_year
    )
    
    return await academic_service.search_academic_backgrounds(filters, skip=skip, limit=limit)

@router.get("/search/count", response_model=dict)
async def get_academic_backgrounds_search_count(
    user_id: Optional[UUID] = Query(None),
    degree_name: Optional[str] = Query(None),
    degree_type: Optional[DegreeTypeEnum] = Query(None),
    field_of_study: Optional[str] = Query(None),
    institution_name: Optional[str] = Query(None),
    status: Optional[AcademicStatusEnum] = Query(None),
    is_completed: Optional[bool] = Query(None),
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Contar formações acadêmicas que atendem aos filtros
    
    Retorna o número total de formações que correspondem aos critérios de busca.
    """
    filters = AcademicBackgroundSearchFilters(
        user_id=user_id,
        degree_name=degree_name,
        degree_type=degree_type,
        field_of_study=field_of_study,
        institution_name=institution_name,
        status=status,
        is_completed=is_completed
    )
    
    count = await academic_service.get_academic_backgrounds_count(filters)
    return {"total_count": count}

# =============================================
# STATISTICS AND ANALYTICS ROUTES
# =============================================

@router.get("/statistics/user/{user_id}", response_model=AcademicBackgroundStatistics)
async def get_user_academic_statistics(
    user_id: UUID,
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Obter estatísticas de formações acadêmicas de um usuário
    
    Retorna métricas completas sobre as formações do usuário incluindo:
    - Total de formações, concluídas, em andamento
    - Maior nível de formação
    - Duração total e anos de estudo
    - Instituições frequentadas
    - Áreas de estudo
    - Tipos de formação concluídas
    - Progressão acadêmica
    """
    return await academic_service.get_user_statistics(user_id)

@router.get("/analytics/user/{user_id}/education-score", response_model=dict)
async def get_user_education_score(
    user_id: UUID,
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Calcular score de educação do usuário (0-100)
    
    Baseado nos tipos de formação e quantidade de diplomas,
    calcula um score educacional ponderado.
    """
    score = await academic_service.calculate_education_score(user_id)
    return {"user_id": user_id, "education_score": score}

@router.get("/analytics/user/{user_id}/recommendations", response_model=dict)
async def get_user_degree_recommendations(
    user_id: UUID,
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Obter recomendações de próximas formações
    
    Analisa a formação atual e sugere próximos passos educacionais.
    """
    recommendations = await academic_service.get_degree_recommendations(user_id)
    return {"user_id": user_id, "degree_recommendations": recommendations}

@router.get("/analytics/institutions-ranking", response_model=List[dict])
async def get_institutions_ranking(
    limit: int = Query(10, ge=1, le=50, description="Limite de instituições retornadas"),
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Obter ranking das principais instituições
    
    Retorna as instituições mais populares baseado no número de estudantes.
    """
    return await academic_service.get_institutions_ranking(limit)

@router.get("/analytics/fields-distribution", response_model=List[dict])
async def get_fields_of_study_distribution(
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Obter distribuição de áreas de estudo
    
    Retorna estatísticas sobre as áreas de estudo mais populares.
    """
    return await academic_service.get_fields_of_study_distribution()

# =============================================
# VALIDATION AND HELPER ROUTES
# =============================================

@router.get("/{academic_id}/exists", response_model=dict)
async def check_academic_background_exists(
    academic_id: UUID,
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Verificar se formação acadêmica existe
    
    Retorna se a formação existe sem retornar seus dados.
    """
    exists = await academic_service.academic_background_exists(academic_id)
    return {"exists": exists, "academic_id": academic_id}

@router.get("/user/{user_id}/has-academics", response_model=dict)
async def check_user_has_academic_backgrounds(
    user_id: UUID,
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Verificar se usuário possui formações acadêmicas
    
    Retorna se o usuário tem pelo menos uma formação cadastrada.
    """
    has_academics = await academic_service.user_has_academic_backgrounds(user_id)
    return {"has_academic_backgrounds": has_academics, "user_id": user_id}

@router.get("/user/{user_id}/has-degree-type/{degree_type}", response_model=dict)
async def check_user_has_degree_type(
    user_id: UUID,
    degree_type: DegreeTypeEnum,
    academic_service: AcademicBackgroundService = Depends(get_academic_service)
):
    """
    Verificar se usuário possui um tipo específico de formação
    
    Retorna se o usuário tem o tipo de formação especificado.
    """
    has_degree = await academic_service.user_has_degree_type(user_id, degree_type)
    return {
        "user_id": user_id,
        "degree_type": degree_type.value,
        "has_degree_type": has_degree
    }