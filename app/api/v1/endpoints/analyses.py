# =============================================
# app/api/v1/endpoints/analyses.py
# =============================================
from fastapi import APIRouter, Depends, status, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
from uuid import UUID
import io

from app.config.database import get_db
from app.services.analysis_service import AnalysisService
from app.schemas.analyze_application_job import (
    AnalyzeApplicationJobCreate,
    AnalyzeApplicationJobUpdate,
    AnalyzeApplicationJobResponse,
    AnalyzeApplicationJobDetail,
    AnalyzeApplicationJobSummary,
    AnalyzeApplicationJobSearchFilters,
    AnalysisRanking,
    BulkAnalysisRequest,
    BulkAnalysisResponse,
    AnalysisStatistics,
    ScoreCategoryEnum,
    AnalysisStatusEnum
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
async def get_analysis_service(db: AsyncSession = Depends(get_db)) -> AnalysisService:
    return AnalysisService(db)

def check_analysis_ownership_or_admin(current_user: UserResponse, analysis_user_id: UUID):
    """Helper to check if user owns analysis or is admin/recruiter"""
    if current_user.user_type in ["admin", "recruiter", "company_owner"]:
        return True
    return current_user.user_id == analysis_user_id

# =============================================
# ANALYSIS CRUD ROUTES
# =============================================

@router.post("/", response_model=AnalyzeApplicationJobResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    analysis_data: AnalyzeApplicationJobCreate,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Criar nova análise manualmente
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    **BR01-BR06**: Implementa sistema de pontuação ponderada:
    - Formação acadêmica: 30%
    - Experiência profissional: 35%
    - Cursos profissionais: 20%
    - Pontos fortes: +15%
    - Pontos fracos: -10%
    
    A pontuação total será calculada automaticamente se não fornecida.
    """
    return await analysis_service.create_analysis(analysis_data, create_user_id=current_user.user_id)

@router.get("/", response_model=List[AnalyzeApplicationJobResponse])
async def get_analyses(
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Listar todas as análises com paginação
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    - **skip**: Número de registros a pular (padrão: 0)
    - **limit**: Limite de registros retornados (padrão: 100, máximo: 1000)
    """
    return await analysis_service.get_analyses(skip=skip, limit=limit)

@router.get("/search", response_model=List[AnalyzeApplicationJobSummary])
async def search_analyses(
    user_id: Optional[UUID] = Query(None, description="Filtrar por usuário"),
    professional_profile_id: Optional[UUID] = Query(None, description="Filtrar por perfil profissional"),
    job_id: Optional[UUID] = Query(None, description="Filtrar por vaga"),
    company_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    score_category: Optional[ScoreCategoryEnum] = Query(None, description="Filtrar por categoria de pontuação"),
    min_total_score: Optional[float] = Query(None, ge=0, le=100, description="Pontuação mínima"),
    max_total_score: Optional[float] = Query(None, ge=0, le=100, description="Pontuação máxima"),
    min_academic_score: Optional[float] = Query(None, ge=0, le=100, description="Pontuação acadêmica mínima"),
    min_experience_score: Optional[float] = Query(None, ge=0, le=100, description="Pontuação experiência mínima"),
    has_opinion: Optional[bool] = Query(None, description="Filtrar por presença de opinião"),
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Buscar análises com filtros avançados
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Permite filtrar análises por diversos critérios incluindo categorias de score.
    """
    filters = AnalyzeApplicationJobSearchFilters(
        user_id=user_id,
        professional_profile_id=professional_profile_id,
        job_id=job_id,
        company_id=company_id,
        score_category=score_category,
        min_total_score=min_total_score,
        max_total_score=max_total_score,
        min_academic_score=min_academic_score,
        min_experience_score=min_experience_score,
        has_opinion=has_opinion
    )
    
    return await analysis_service.search_analyses(filters, skip=skip, limit=limit)

@router.get("/{analysis_id}", response_model=AnalyzeApplicationJobDetail)
async def get_analysis(
    analysis_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Obter análise por ID
    
    **Requer autenticação**
    
    Usuários podem ver apenas suas próprias análises, exceto admins/recruiters.
    Retorna análise detalhada com breakdown ponderado e insights.
    """
    analysis = await analysis_service.get_analysis(analysis_id)
    
    # Check ownership or admin privileges
    if not check_analysis_ownership_or_admin(current_user, analysis.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode acessar suas próprias análises"
        )
    
    return analysis

@router.put("/{analysis_id}", response_model=AnalyzeApplicationJobDetail)
async def update_analysis(
    analysis_id: UUID,
    analysis_data: AnalyzeApplicationJobUpdate,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Atualizar análise
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Permite atualização das pontuações individuais.
    A pontuação total será recalculada automaticamente baseada nas BR01-BR06.
    """
    return await analysis_service.update_analysis(analysis_id, analysis_data)

@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: UUID,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Deletar análise (soft delete)
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Marca a análise como deletada sem remover do banco de dados.
    """
    await analysis_service.delete_analysis(analysis_id)

# =============================================
# APPLICATION ANALYSIS ROUTES
# =============================================

@router.post("/analyze-application/{application_id}", response_model=AnalyzeApplicationJobResponse)
async def analyze_application(
    application_id: UUID,
    force_reanalysis: bool = Query(False, description="Forçar reanálise se já existe"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Analisar candidatura usando LLM
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Executa análise completa da candidatura usando modelos de linguagem.
    Aplica automaticamente as regras de pontuação BR01-BR06.
    """
    return await analysis_service.analyze_application(application_id, force_reanalysis=force_reanalysis)

@router.get("/can-analyze/{application_id}")
async def check_can_analyze_application(
    application_id: UUID,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Verificar se candidatura pode ser analisada
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Verifica se a candidatura está elegível para análise ou reanálise.
    """
    result = await analysis_service.can_analyze_application(application_id)
    
    return {
        "application_id": application_id,
        "can_analyze": result["can_analyze"],
        "reasons": result.get("reasons", []),
        "has_existing_analysis": result.get("has_existing_analysis", False),
        "message": "Pode analisar" if result["can_analyze"] else "Não pode analisar"
    }

@router.post("/bulk-analyze", response_model=BulkAnalysisResponse)
async def bulk_analyze_applications(
    request: BulkAnalysisRequest,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Analisar múltiplas candidaturas em lote
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    - **application_job_ids**: Lista de IDs das candidaturas (máximo 100)
    - **force_reanalysis**: Forçar reanálise de candidaturas já analisadas
    - **priority**: Prioridade da análise (1=alta, 10=baixa)
    
    Retorna informações sobre o job de análise em lote.
    """
    return await analysis_service.bulk_analyze_applications(request)

# =============================================
# JOB RANKING AND REPORTS ROUTES
# =============================================

@router.get("/job/{job_id}/ranking", response_model=List[AnalysisRanking])
async def get_job_ranking(
    job_id: UUID,
    limit: int = Query(50, ge=1, le=200, description="Limite de candidatos no ranking"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Obter ranking de candidatos para uma vaga
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Retorna candidatos ordenados por pontuação total com detalhes da análise.
    Baseado no sistema de pontuação ponderada BR01-BR06.
    """
    return await analysis_service.get_job_ranking(job_id, limit=limit)

@router.get("/job/{job_id}/statistics")
async def get_job_analysis_statistics(
    job_id: UUID,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Obter estatísticas de análises para uma vaga
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Retorna métricas estatísticas das análises da vaga.
    """
    stats = await analysis_service.get_job_analysis_stats(job_id)
    
    return {
        "job_id": job_id,
        **stats
    }

@router.get("/job/{job_id}/report")
async def generate_analysis_report(
    job_id: UUID,
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Gerar relatório PDF de análises da vaga
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Gera relatório em PDF com ranking, estatísticas e insights.
    """
    report_data = await analysis_service.generate_analysis_report(job_id)
    
    # Return PDF as streaming response
    pdf_stream = io.BytesIO(report_data)
    
    return StreamingResponse(
        io.BytesIO(report_data),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=analysis_report_job_{job_id}.pdf"
        }
    )

# =============================================
# USER ANALYSIS ROUTES
# =============================================

@router.get("/user/{user_id}", response_model=List[AnalyzeApplicationJobSummary])
async def get_user_analyses(
    user_id: UUID,
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Listar análises de um usuário específico
    
    **Requer autenticação**
    
    Usuários podem ver apenas suas próprias análises, exceto admins/recruiters.
    """
    if not check_analysis_ownership_or_admin(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode acessar suas próprias análises"
        )
    
    return await analysis_service.get_user_analyses(user_id, skip=skip, limit=limit)

@router.get("/user/{user_id}/best", response_model=AnalyzeApplicationJobDetail)
async def get_user_best_analysis(
    user_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Obter melhor análise do usuário
    
    **Requer autenticação**
    
    Retorna a análise com maior pontuação total do usuário.
    """
    if not check_analysis_ownership_or_admin(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode acessar suas próprias análises"
        )
    
    best_analysis = await analysis_service.get_user_best_analysis(user_id)
    if not best_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não possui análises"
        )
    
    return best_analysis

@router.get("/user/{user_id}/progress")
async def get_user_analysis_progress(
    user_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Obter progresso de análises do usuário
    
    **Requer autenticação**
    
    Retorna tendências de melhoria e estatísticas históricas.
    """
    if not check_analysis_ownership_or_admin(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode acessar suas próprias análises"
        )
    
    progress = await analysis_service.get_user_analysis_progress(user_id)
    
    return {
        "user_id": user_id,
        **progress
    }

# =============================================
# STATISTICS AND ANALYTICS ROUTES
# =============================================

@router.get("/analytics/statistics", response_model=AnalysisStatistics)
async def get_analysis_statistics(
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Obter estatísticas gerais de análises
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Retorna estatísticas abrangentes do sistema de análises incluindo:
    - Distribuição de pontuações por categoria
    - Histograma de scores
    - Top performers
    """
    return await analysis_service.get_analysis_statistics()

@router.get("/analytics/global-ranking")
async def get_global_ranking(
    limit: int = Query(100, ge=1, le=500, description="Limite de candidatos no ranking"),
    current_user: UserResponse = Depends(require_recruiter_or_admin),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Obter ranking global de todas as análises
    
    **Requer autenticação e permissão de recruiter, company_owner ou admin**
    
    Retorna os melhores candidatos do sistema ordenados por pontuação.
    """
    # This would call a method in the service that uses repository's get_global_ranking
    from app.repositories.analyze_application_job_repository import AnalyzeApplicationJobRepository
    
    analysis_repo = AnalyzeApplicationJobRepository(analysis_service.db)
    ranking = await analysis_repo.get_global_ranking(limit=limit)
    
    return {
        "global_ranking": ranking,
        "total_candidates": len(ranking),
        "limit_applied": limit
    }

# =============================================
# CONVENIENCE ROUTES
# =============================================

@router.get("/my-analyses", response_model=List[AnalyzeApplicationJobSummary])
async def get_my_analyses(
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros retornados"),
    current_user: UserResponse = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Listar minhas análises (endpoint de conveniência)
    
    **Requer autenticação**
    
    Retorna as análises do usuário atual.
    """
    return await analysis_service.get_user_analyses(current_user.user_id, skip=skip, limit=limit)

@router.get("/my-best", response_model=AnalyzeApplicationJobDetail)
async def get_my_best_analysis(
    current_user: UserResponse = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Obter minha melhor análise (endpoint de conveniência)
    
    **Requer autenticação**
    
    Retorna a análise com maior pontuação do usuário atual.
    """
    best_analysis = await analysis_service.get_user_best_analysis(current_user.user_id)
    if not best_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Você não possui análises"
        )
    
    return best_analysis

@router.get("/my-progress")
async def get_my_analysis_progress(
    current_user: UserResponse = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Obter meu progresso de análises (endpoint de conveniência)
    
    **Requer autenticação**
    
    Retorna tendências de melhoria e estatísticas do usuário atual.
    """
    progress = await analysis_service.get_user_analysis_progress(current_user.user_id)
    
    return {
        "user_id": current_user.user_id,
        **progress
    }

# =============================================
# VALIDATION ROUTES
# =============================================

@router.get("/{analysis_id}/exists")
async def check_analysis_exists(
    analysis_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Verificar se análise existe
    
    **Requer autenticação**
    
    Retorna se a análise existe sem retornar seus dados.
    """
    exists = await analysis_service.analysis_exists(analysis_id)
    
    return {
        "exists": exists,
        "analysis_id": analysis_id
    }

# =============================================
# SCORE CALCULATION ROUTES
# =============================================

@router.post("/calculate-score")
async def calculate_weighted_score(
    academic_score: float = Query(..., ge=0, le=100, description="Pontuação acadêmica"),
    experience_score: float = Query(..., ge=0, le=100, description="Pontuação experiência"),
    courses_score: float = Query(..., ge=0, le=100, description="Pontuação cursos"),
    strong_points_score: float = Query(..., ge=0, le=100, description="Pontuação pontos fortes"),
    weak_points_score: float = Query(..., ge=0, le=100, description="Pontuação pontos fracos"),
    current_user: UserResponse = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Calcular pontuação ponderada (BR01-BR06)
    
    **Requer autenticação**
    
    Calcula a pontuação final baseada nas regras de negócio:
    - Academic: 30%
    - Experience: 35% 
    - Courses: 20%
    - Strong Points: +15%
    - Weak Points: -10%
    
    Útil para preview antes de criar análise.
    """
    total_score = analysis_service._calculate_weighted_score(
        academic_score=academic_score,
        experience_score=experience_score,
        courses_score=courses_score,
        strong_points_score=strong_points_score,
        weak_points_score=weak_points_score
    )
    
    # Calculate breakdown
    breakdown = {
        "academic_weighted": round(academic_score * 0.30, 2),
        "experience_weighted": round(experience_score * 0.35, 2),
        "courses_weighted": round(courses_score * 0.20, 2),
        "strong_points_weighted": round(strong_points_score * 0.15, 2),
        "weak_points_penalty": round(weak_points_score * 0.10, 2)
    }
    
    # Determine category
    if total_score >= 90:
        category = ScoreCategoryEnum.EXCELLENT
    elif total_score >= 80:
        category = ScoreCategoryEnum.VERY_GOOD
    elif total_score >= 70:
        category = ScoreCategoryEnum.GOOD
    elif total_score >= 60:
        category = ScoreCategoryEnum.SATISFACTORY
    else:
        category = ScoreCategoryEnum.NEEDS_IMPROVEMENT
    
    return {
        "total_score": round(total_score, 2),
        "score_category": category,
        "weighted_breakdown": breakdown,
        "business_rules": {
            "BR01": "Formação acadêmica: 30%",
            "BR02": "Experiência profissional: 35%", 
            "BR03": "Cursos profissionais: 20%",
            "BR04": "Pontos fortes: +15%",
            "BR05": "Pontos fracos: -10%"
        }
    }