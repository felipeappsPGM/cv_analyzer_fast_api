# =============================================
# app/schemas/analyze_application_job.py
# =============================================
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID
from enum import Enum

# =============================================
# ENUMS
# =============================================
class AnalysisStatusEnum(str, Enum):
    PENDING = "Pendente"
    IN_PROGRESS = "Em Progresso"
    COMPLETED = "Concluída"
    FAILED = "Falhou"
    REQUIRES_REVIEW = "Requer Revisão"

class ScoreCategoryEnum(str, Enum):
    EXCELLENT = "Excelente"  # 90-100
    VERY_GOOD = "Muito Bom"  # 80-89
    GOOD = "Bom"  # 70-79
    SATISFACTORY = "Satisfatório"  # 60-69
    NEEDS_IMPROVEMENT = "Precisa Melhorar"  # 0-59

# =============================================
# BASE SCHEMA
# =============================================
class AnalyzeApplicationJobBase(BaseModel):
    professional_profile_id: UUID = Field(..., description="ID do perfil profissional")
    user_id: UUID = Field(..., description="ID do usuário")
    
    # Analysis Scores (based on business rules BR01-BR06)
    academic_score: Optional[float] = Field(None, ge=0, le=100, description="Pontuação acadêmica (30%)")
    professional_experience_score: Optional[float] = Field(None, ge=0, le=100, description="Pontuação experiência (35%)")
    professional_courses_score: Optional[float] = Field(None, ge=0, le=100, description="Pontuação cursos (20%)")
    weak_points_score: Optional[float] = Field(None, ge=0, le=100, description="Pontuação pontos fracos (-10%)")
    strong_points_score: Optional[float] = Field(None, ge=0, le=100, description="Pontuação pontos fortes (15%)")
    total_score: float = Field(0.0, ge=0, le=100, description="Pontuação final ponderada")
    
    # LLM Generated Opinion
    opinion_application_job: Optional[str] = Field(None, description="Opinião gerada pelo LLM")

    @validator('total_score')
    def validate_total_score(cls, v):
        """Validate total score range"""
        if v < 0 or v > 100:
            raise ValueError("Pontuação total deve estar entre 0 e 100")
        return round(v, 2)

# =============================================
# CREATE SCHEMA
# =============================================
class AnalyzeApplicationJobCreate(AnalyzeApplicationJobBase):
    """Schema para criação de análise"""
    
    @validator('academic_score', 'professional_experience_score', 'professional_courses_score', 
              'weak_points_score', 'strong_points_score')
    def validate_individual_scores(cls, v):
        """Validate individual score ranges"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Pontuações individuais devem estar entre 0 e 100")
        return round(v, 2) if v is not None else v

# =============================================
# UPDATE SCHEMA
# =============================================
class AnalyzeApplicationJobUpdate(BaseModel):
    """Schema para atualização de análise (campos opcionais)"""
    academic_score: Optional[float] = Field(None, ge=0, le=100)
    professional_experience_score: Optional[float] = Field(None, ge=0, le=100)
    professional_courses_score: Optional[float] = Field(None, ge=0, le=100)
    weak_points_score: Optional[float] = Field(None, ge=0, le=100)
    strong_points_score: Optional[float] = Field(None, ge=0, le=100)
    total_score: Optional[float] = Field(None, ge=0, le=100)
    opinion_application_job: Optional[str] = None

# =============================================
# RESPONSE SCHEMA
# =============================================
class AnalyzeApplicationJobResponse(AnalyzeApplicationJobBase):
    """Schema para resposta da API"""
    model_config = ConfigDict(from_attributes=True)
    
    analyze_application_job_id: UUID
    created_date: datetime
    updated_date: Optional[datetime] = None
    deleted_date: Optional[datetime] = None

# =============================================
# DETAIL SCHEMA
# =============================================
class AnalyzeApplicationJobDetail(AnalyzeApplicationJobResponse):
    """Schema para resposta detalhada com relacionamentos"""
    create_user_id: Optional[UUID] = None
    
    # User information
    user_name: Optional[str] = Field(None, description="Nome do usuário")
    user_email: Optional[str] = Field(None, description="Email do usuário")
    
    # Professional profile information
    profile_name: Optional[str] = Field(None, description="Nome do perfil profissional")
    
    # Calculated fields
    score_category: ScoreCategoryEnum = Field(..., description="Categoria da pontuação")
    weighted_breakdown: Dict[str, float] = Field(default_factory=dict, description="Breakdown ponderado dos scores")
    analysis_status: AnalysisStatusEnum = Field(AnalysisStatusEnum.COMPLETED, description="Status da análise")
    
    # Analysis insights
    strengths: List[str] = Field(default_factory=list, description="Pontos fortes identificados")
    weaknesses: List[str] = Field(default_factory=list, description="Pontos fracos identificados")
    recommendations: List[str] = Field(default_factory=list, description="Recomendações")
    
    # Comparison data
    percentile_rank: Optional[float] = Field(None, description="Posição percentil comparado a outros candidatos")
    ranking_position: Optional[int] = Field(None, description="Posição no ranking")
    total_candidates: Optional[int] = Field(None, description="Total de candidatos analisados")

    @validator('score_category', always=True)
    def calculate_score_category(cls, v, values):
        """Calculate score category based on total score"""
        total_score = values.get('total_score', 0)
        
        if total_score >= 90:
            return ScoreCategoryEnum.EXCELLENT
        elif total_score >= 80:
            return ScoreCategoryEnum.VERY_GOOD
        elif total_score >= 70:
            return ScoreCategoryEnum.GOOD
        elif total_score >= 60:
            return ScoreCategoryEnum.SATISFACTORY
        else:
            return ScoreCategoryEnum.NEEDS_IMPROVEMENT

    @validator('weighted_breakdown', always=True)
    def calculate_weighted_breakdown(cls, v, values):
        """Calculate weighted score breakdown"""
        academic = values.get('academic_score', 0) or 0
        experience = values.get('professional_experience_score', 0) or 0
        courses = values.get('professional_courses_score', 0) or 0
        strong = values.get('strong_points_score', 0) or 0
        weak = values.get('weak_points_score', 0) or 0
        
        return {
            "academic_weighted": round(academic * 0.30, 2),
            "experience_weighted": round(experience * 0.35, 2),
            "courses_weighted": round(courses * 0.20, 2),
            "strong_points_weighted": round(strong * 0.15, 2),
            "weak_points_penalty": round(weak * 0.10, 2)
        }

# =============================================
# SUMMARY SCHEMA
# =============================================
class AnalyzeApplicationJobSummary(BaseModel):
    """Schema resumido para listagens"""
    model_config = ConfigDict(from_attributes=True)
    
    analyze_application_job_id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    professional_profile_id: UUID
    total_score: float
    score_category: ScoreCategoryEnum
    created_date: datetime
    ranking_position: Optional[int] = None

# =============================================
# RANKING SCHEMA
# =============================================
class AnalysisRanking(BaseModel):
    """Schema para ranking de análises"""
    model_config = ConfigDict(from_attributes=True)
    
    analyze_application_job_id: UUID
    application_job_id: UUID
    user_id: UUID
    user_name: str
    user_email: str
    total_score: float
    score_category: ScoreCategoryEnum
    ranking_position: int
    percentile_rank: float
    
    # Score breakdown
    academic_score: Optional[float] = None
    professional_experience_score: Optional[float] = None
    professional_courses_score: Optional[float] = None
    strong_points_score: Optional[float] = None
    weak_points_score: Optional[float] = None
    
    # Summary insights
    top_strength: Optional[str] = None
    main_weakness: Optional[str] = None
    created_date: datetime

# =============================================
# SEARCH FILTERS SCHEMA
# =============================================
class AnalyzeApplicationJobSearchFilters(BaseModel):
    """Schema para filtros de busca"""
    user_id: Optional[UUID] = Field(None, description="Filtrar por usuário")
    professional_profile_id: Optional[UUID] = Field(None, description="Filtrar por perfil profissional")
    job_id: Optional[UUID] = Field(None, description="Filtrar por vaga")
    company_id: Optional[UUID] = Field(None, description="Filtrar por empresa")
    score_category: Optional[ScoreCategoryEnum] = Field(None, description="Filtrar por categoria de pontuação")
    min_total_score: Optional[float] = Field(None, ge=0, le=100, description="Pontuação mínima")
    max_total_score: Optional[float] = Field(None, ge=0, le=100, description="Pontuação máxima")
    min_academic_score: Optional[float] = Field(None, ge=0, le=100, description="Pontuação acadêmica mínima")
    min_experience_score: Optional[float] = Field(None, ge=0, le=100, description="Pontuação experiência mínima")
    analyzed_after: Optional[datetime] = Field(None, description="Analisadas após data")
    analyzed_before: Optional[datetime] = Field(None, description="Analisadas antes da data")
    has_opinion: Optional[bool] = Field(None, description="Filtrar por presença de opinião")

# =============================================
# BULK ANALYSIS SCHEMA
# =============================================
class BulkAnalysisRequest(BaseModel):
    """Schema para solicitação de análise em lote"""
    application_job_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    force_reanalysis: bool = Field(False, description="Forçar reanálise de candidaturas já analisadas")
    priority: int = Field(5, ge=1, le=10, description="Prioridade da análise (1=alta, 10=baixa)")

class BulkAnalysisResponse(BaseModel):
    """Schema para resposta de análise em lote"""
    total_requested: int
    started_analyses: int
    already_analyzed: int
    failed_to_start: int
    analysis_job_id: UUID = Field(..., description="ID do job de análise em lote")
    estimated_completion_minutes: Optional[int] = None

# =============================================
# STATISTICS SCHEMA
# =============================================
class AnalysisStatistics(BaseModel):
    """Schema para estatísticas de análises"""
    model_config = ConfigDict(from_attributes=True)
    
    # General statistics
    total_analyses: int = 0
    avg_total_score: Optional[float] = None
    median_total_score: Optional[float] = None
    std_dev_total_score: Optional[float] = None
    
    # Score distribution
    score_distribution: Dict[ScoreCategoryEnum, int] = Field(default_factory=dict)
    score_histogram: List[Dict[str, float]] = Field(default_factory=list)  # For charts
    
    # Category averages
    avg_academic_score: Optional[float] = None
    avg_experience_score: Optional[float] = None
    avg_courses_score: Optional[float] = None
    avg_strong_points_score: Optional[float] = None
    avg_weak_points_score: Optional[float] = None
    
    # Trends
    monthly_trends: Dict[str, float] = Field(default_factory=dict)
    top_performing_profiles: List[Dict] = Field(default_factory=list)
    improvement_opportunities: List[str] = Field(default_factory=list)

# =============================================
# COMPARISON SCHEMA
# =============================================
class AnalysisComparison(BaseModel):
    """Schema para comparação entre análises"""
    model_config = ConfigDict(from_attributes=True)
    
    analysis_a: AnalyzeApplicationJobSummary
    analysis_b: AnalyzeApplicationJobSummary
    
    score_differences: Dict[str, float] = Field(default_factory=dict)
    better_performing_analysis: UUID
    key_differentiators: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)