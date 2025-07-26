# =============================================
# app/schemas/application_job.py
# =============================================
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum

# =============================================
# ENUMS
# =============================================
class ApplicationStatusEnum(str, Enum):
    PENDING = "Pendente"
    ANALYZING = "Analisando"
    ANALYZED = "Analisada"
    APPROVED = "Aprovada"
    REJECTED = "Rejeitada"
    WITHDRAWN = "Retirada"

# =============================================
# BASE SCHEMA
# =============================================
class ApplicationJobBase(BaseModel):
    professional_profile_id: UUID = Field(..., description="ID do perfil profissional")
    job_id: UUID = Field(..., description="ID da vaga")
    user_id: UUID = Field(..., description="ID do usuário")

    @validator('professional_profile_id', 'job_id', 'user_id')
    def validate_uuids(cls, v):
        """Validate that UUIDs are not None"""
        if v is None:
            raise ValueError("ID não pode ser nulo")
        return v

# =============================================
# CREATE SCHEMA
# =============================================
class ApplicationJobCreate(ApplicationJobBase):
    """Schema para criação de candidatura"""
    pass

# =============================================
# UPDATE SCHEMA
# =============================================
class ApplicationJobUpdate(BaseModel):
    """Schema para atualização de candidatura (campos opcionais)"""
    professional_profile_id: Optional[UUID] = None
    
    # Note: job_id and user_id typically shouldn't be changed after creation

# =============================================
# RESPONSE SCHEMA
# =============================================
class ApplicationJobResponse(ApplicationJobBase):
    """Schema para resposta da API"""
    model_config = ConfigDict(from_attributes=True)
    
    application_job_id: UUID
    created_date: datetime
    updated_date: Optional[datetime] = None
    deleted_date: Optional[datetime] = None

# =============================================
# DETAIL SCHEMA
# =============================================
class ApplicationJobDetail(ApplicationJobResponse):
    """Schema para resposta detalhada com relacionamentos"""
    create_user_id: Optional[UUID] = None
    
    # User information
    user_name: Optional[str] = Field(None, description="Nome do usuário")
    user_email: Optional[str] = Field(None, description="Email do usuário")
    
    # Job information
    job_name: Optional[str] = Field(None, description="Nome da vaga")
    job_code: Optional[str] = Field(None, description="Código da vaga")
    company_name: Optional[str] = Field(None, description="Nome da empresa")
    
    # Professional profile information
    profile_name: Optional[str] = Field(None, description="Nome do perfil profissional")
    
    # Application status and analysis
    status: ApplicationStatusEnum = Field(ApplicationStatusEnum.PENDING, description="Status da candidatura")
    has_analysis: bool = Field(False, description="Se possui análise")
    analysis_id: Optional[UUID] = Field(None, description="ID da análise")
    total_score: Optional[float] = Field(None, description="Pontuação total da análise")
    analysis_date: Optional[datetime] = Field(None, description="Data da análise")
    
    # Calculated fields
    is_active: bool = Field(True, description="Se a candidatura está ativa")
    days_since_application: Optional[int] = Field(None, description="Dias desde a candidatura")

    @validator('is_active', always=True)
    def calculate_is_active(cls, v, values):
        """Check if application is active"""
        deleted_date = values.get('deleted_date')
        return deleted_date is None

    @validator('days_since_application', always=True)
    def calculate_days_since_application(cls, v, values):
        """Calculate days since application"""
        created_date = values.get('created_date')
        if not created_date:
            return None
        return (datetime.utcnow() - created_date).days

# =============================================
# SUMMARY SCHEMA
# =============================================
class ApplicationJobSummary(BaseModel):
    """Schema resumido para listagens"""
    model_config = ConfigDict(from_attributes=True)
    
    application_job_id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    job_id: UUID
    job_name: Optional[str] = None
    company_name: Optional[str] = None
    created_date: datetime
    status: ApplicationStatusEnum = ApplicationStatusEnum.PENDING
    total_score: Optional[float] = None

# =============================================
# SEARCH FILTERS SCHEMA
# =============================================
class ApplicationJobSearchFilters(BaseModel):
    """Schema para filtros de busca"""
    user_id: Optional[UUID] = Field(None, description="Filtrar por usuário")
    job_id: Optional[UUID] = Field(None, description="Filtrar por vaga")
    company_id: Optional[UUID] = Field(None, description="Filtrar por empresa")
    professional_profile_id: Optional[UUID] = Field(None, description="Filtrar por perfil profissional")
    status: Optional[ApplicationStatusEnum] = Field(None, description="Filtrar por status")
    has_analysis: Optional[bool] = Field(None, description="Filtrar por análise")
    min_score: Optional[float] = Field(None, ge=0, le=100, description="Pontuação mínima")
    max_score: Optional[float] = Field(None, ge=0, le=100, description="Pontuação máxima")
    applied_after: Optional[datetime] = Field(None, description="Candidaturas após data")
    applied_before: Optional[datetime] = Field(None, description="Candidaturas antes da data")
    analyzed_after: Optional[datetime] = Field(None, description="Analisadas após data")
    analyzed_before: Optional[datetime] = Field(None, description="Analisadas antes da data")

# =============================================
# RANKING SCHEMA
# =============================================
class ApplicationJobRanking(BaseModel):
    """Schema para ranking de candidaturas"""
    model_config = ConfigDict(from_attributes=True)
    
    application_job_id: UUID
    user_id: UUID
    user_name: str
    user_email: str
    job_id: UUID
    total_score: float
    ranking_position: int
    
    # Detailed scores
    academic_score: Optional[float] = None
    professional_experience_score: Optional[float] = None
    professional_courses_score: Optional[float] = None
    strong_points_score: Optional[float] = None
    weak_points_score: Optional[float] = None
    
    # Analysis info
    analysis_date: Optional[datetime] = None
    opinion_summary: Optional[str] = Field(None, max_length=500, description="Resumo da opinião")

# =============================================
# BULK OPERATIONS SCHEMA
# =============================================
class ApplicationJobBulkCreate(BaseModel):
    """Schema para criação em lote de candidaturas"""
    user_id: UUID
    job_ids: List[UUID] = Field(..., min_items=1, max_items=50)
    professional_profile_id: UUID

    @validator('job_ids')
    def validate_job_ids(cls, v):
        """Validate job IDs list"""
        if len(set(v)) != len(v):
            raise ValueError("IDs de vagas duplicados não são permitidos")
        return v

class ApplicationJobBulkResponse(BaseModel):
    """Schema para resposta de criação em lote"""
    created_applications: List[ApplicationJobResponse]
    failed_applications: List[dict] = Field(default_factory=list)
    total_created: int
    total_failed: int

# =============================================
# STATISTICS SCHEMA
# =============================================
class ApplicationJobStatistics(BaseModel):
    """Schema para estatísticas de candidaturas"""
    model_config = ConfigDict(from_attributes=True)
    
    # General stats
    total_applications: int = 0
    pending_applications: int = 0
    analyzed_applications: int = 0
    approved_applications: int = 0
    rejected_applications: int = 0
    
    # Score statistics
    avg_score: Optional[float] = None
    median_score: Optional[float] = None
    highest_score: Optional[float] = None
    lowest_score: Optional[float] = None
    
    # Time statistics
    avg_days_to_analysis: Optional[float] = None
    applications_by_month: Optional[dict] = None
    
    # By job/company
    top_jobs_by_applications: List[dict] = Field(default_factory=list)
    top_companies_by_applications: List[dict] = Field(default_factory=list)