# =============================================
# app/api/v1/endpoints/professional_courses.py
# =============================================
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.config.database import get_db
from app.services.professional_courses_service import ProfessionalCoursesService
from app.schemas.professional_courses import (
    ProfessionalCoursesCreate,
    ProfessionalCoursesUpdate,
    ProfessionalCoursesResponse,
    ProfessionalCoursesDetail,
    ProfessionalCoursesSummary,
    ProfessionalCoursesSearchFilters,
    ProfessionalCoursesStatistics,
    BulkCoursesCreate,
    BulkCoursesResponse,
    CertificateInfo,
    CourseStatusEnum,
    CourseCategoryEnum
)

# =============================================
# ROUTER INSTANCE
# =============================================
router = APIRouter()

# =============================================
# DEPENDENCIES
# =============================================
async def get_courses_service(db: AsyncSession = Depends(get_db)) -> ProfessionalCoursesService:
    return ProfessionalCoursesService(db)

# =============================================
# BASIC CRUD ROUTES
# =============================================

@router.post("/", response_model=ProfessionalCoursesResponse, status_code=status.HTTP_201_CREATED)
async def create_professional_course(
    course_data: ProfessionalCoursesCreate,
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Criar novo curso profissional
    
    - **course_name**: Nome do curso
    - **institution_name**: Nome da instituição
    - **token_id**: ID do certificado/token (opcional)
    - **duration_time_hours**: Duração em horas (opcional)
    - **start_date**: Data de início (opcional)
    - **end_date**: Data de conclusão (opcional)
    - **user_id**: ID do usuário
    """
    return await courses_service.create_course(course_data)

@router.get("/", response_model=List[ProfessionalCoursesResponse])
async def get_professional_courses(
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Listar cursos profissionais com paginação
    """
    return await courses_service.get_courses(skip=skip, limit=limit)

@router.get("/{course_id}", response_model=ProfessionalCoursesDetail)
async def get_professional_course(
    course_id: UUID,
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Obter curso profissional por ID
    
    Retorna informações detalhadas do curso incluindo dados calculados.
    """
    return await courses_service.get_course(course_id)

@router.put("/{course_id}", response_model=ProfessionalCoursesDetail)
async def update_professional_course(
    course_id: UUID,
    course_data: ProfessionalCoursesUpdate,
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Atualizar curso profissional
    
    Permite atualização parcial dos dados do curso.
    Apenas os campos fornecidos serão atualizados.
    """
    return await courses_service.update_course(course_id, course_data)

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_professional_course(
    course_id: UUID,
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Deletar curso profissional (soft delete)
    
    Marca o curso como deletado sem remover do banco de dados.
    """
    await courses_service.delete_course(course_id)

# =============================================
# USER SPECIFIC ROUTES
# =============================================

@router.get("/user/{user_id}", response_model=List[ProfessionalCoursesSummary])
async def get_user_professional_courses(
    user_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Obter todos os cursos profissionais de um usuário
    
    Retorna lista resumida dos cursos do usuário com paginação.
    """
    return await courses_service.get_user_courses(user_id, skip=skip, limit=limit)

@router.get("/user/{user_id}/completed", response_model=List[ProfessionalCoursesResponse])
async def get_user_completed_courses(
    user_id: UUID,
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Obter cursos concluídos de um usuário
    
    Retorna apenas os cursos que já foram finalizados.
    """
    return await courses_service.get_user_completed_courses(user_id)

@router.get("/user/{user_id}/ongoing", response_model=List[ProfessionalCoursesResponse])
async def get_user_ongoing_courses(
    user_id: UUID,
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Obter cursos em andamento de um usuário
    
    Retorna apenas os cursos que ainda estão sendo realizados.
    """
    return await courses_service.get_user_ongoing_courses(user_id)

@router.get("/user/{user_id}/with-certificates", response_model=List[ProfessionalCoursesResponse])
async def get_user_courses_with_certificates(
    user_id: UUID,
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Obter cursos com certificados de um usuário
    
    Retorna apenas os cursos que possuem certificados anexados.
    """
    return await courses_service.get_user_courses_with_certificates(user_id)

# =============================================
# SEARCH AND FILTERING ROUTES
# =============================================

@router.get("/search/", response_model=List[ProfessionalCoursesSummary])
async def search_professional_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[UUID] = Query(None, description="Filtrar por usuário"),
    course_name: Optional[str] = Query(None, description="Filtrar por nome do curso"),
    institution_name: Optional[str] = Query(None, description="Filtrar por instituição"),
    category: Optional[CourseCategoryEnum] = Query(None, description="Filtrar por categoria"),
    status: Optional[CourseStatusEnum] = Query(None, description="Filtrar por status"),
    is_completed: Optional[bool] = Query(None, description="Filtrar cursos concluídos"),
    has_certificate: Optional[bool] = Query(None, description="Filtrar com certificado"),
    min_duration_hours: Optional[int] = Query(None, ge=0, description="Duração mínima em horas"),
    max_duration_hours: Optional[int] = Query(None, ge=0, description="Duração máxima em horas"),
    completion_year: Optional[int] = Query(None, ge=1990, le=2030, description="Ano de conclusão"),
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Buscar cursos profissionais com filtros avançados
    
    Permite filtrar cursos por diversos critérios como nome, instituição,
    categoria, status, presença de certificado, duração, etc.
    """
    filters = ProfessionalCoursesSearchFilters(
        user_id=user_id,
        course_name=course_name,
        institution_name=institution_name,
        category=category,
        status=status,
        is_completed=is_completed,
        has_certificate=has_certificate,
        min_duration_hours=min_duration_hours,
        max_duration_hours=max_duration_hours,
        completion_year=completion_year
    )
    
    return await courses_service.search_courses(filters, skip=skip, limit=limit)

@router.get("/search/count", response_model=dict)
async def get_courses_search_count(
    user_id: Optional[UUID] = Query(None),
    course_name: Optional[str] = Query(None),
    institution_name: Optional[str] = Query(None),
    category: Optional[CourseCategoryEnum] = Query(None),
    status: Optional[CourseStatusEnum] = Query(None),
    is_completed: Optional[bool] = Query(None),
    has_certificate: Optional[bool] = Query(None),
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Contar cursos profissionais que atendem aos filtros
    
    Retorna o número total de cursos que correspondem aos critérios de busca.
    """
    filters = ProfessionalCoursesSearchFilters(
        user_id=user_id,
        course_name=course_name,
        institution_name=institution_name,
        category=category,
        status=status,
        is_completed=is_completed,
        has_certificate=has_certificate
    )
    
    count = await courses_service.get_courses_count(filters)
    return {"total_count": count}

# =============================================
# STATISTICS AND ANALYTICS ROUTES
# =============================================

@router.get("/statistics/user/{user_id}", response_model=ProfessionalCoursesStatistics)
async def get_user_courses_statistics(
    user_id: UUID,
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Obter estatísticas de cursos profissionais de um usuário
    
    Retorna métricas completas sobre os cursos do usuário incluindo:
    - Total de cursos, concluídos, em andamento
    - Horas de estudo totais e média
    - Instituições frequentadas
    - Certificados obtidos
    - Distribuição por ano
    """
    return await courses_service.get_user_statistics(user_id)

@router.get("/analytics/top-institutions", response_model=List[dict])
async def get_top_institutions(
    limit: int = Query(10, ge=1, le=50, description="Limite de instituições retornadas"),
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Obter ranking das principais instituições
    
    Retorna as instituições mais populares baseado no número de cursos.
    """
    return await courses_service.get_top_institutions(limit)

# =============================================
# BULK OPERATIONS ROUTES
# =============================================

@router.post("/bulk/", response_model=BulkCoursesResponse, status_code=status.HTTP_201_CREATED)
async def bulk_create_professional_courses(
    bulk_data: BulkCoursesCreate,
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Criar múltiplos cursos profissionais em lote
    
    Permite criar vários cursos de uma vez para um usuário.
    Máximo de 50 cursos por requisição.
    """
    return await courses_service.bulk_create_courses(bulk_data)

# =============================================
# CERTIFICATE MANAGEMENT ROUTES
# =============================================

@router.get("/{course_id}/certificate", response_model=CertificateInfo)
async def get_course_certificate_info(
    course_id: UUID,
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Obter informações do certificado de um curso
    
    Retorna metadados sobre os certificados anexados ao curso
    sem retornar os dados binários.
    """
    return await courses_service.get_certificate_info(course_id)

# =============================================
# VALIDATION HELPER ROUTES
# =============================================

@router.get("/{course_id}/exists", response_model=dict)
async def check_course_exists(
    course_id: UUID,
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Verificar se curso profissional existe
    
    Retorna se o curso existe sem retornar seus dados.
    """
    exists = await courses_service.course_exists(course_id)
    return {"exists": exists, "course_id": course_id}

@router.get("/user/{user_id}/has-courses", response_model=dict)
async def check_user_has_courses(
    user_id: UUID,
    courses_service: ProfessionalCoursesService = Depends(get_courses_service)
):
    """
    Verificar se usuário possui cursos profissionais
    
    Retorna se o usuário tem pelo menos um curso cadastrado.
    """
    has_courses = await courses_service.user_has_courses(user_id)
    return {"has_courses": has_courses, "user_id": user_id}