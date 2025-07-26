# =============================================
# app/schemas/job.py
# =============================================
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import re

# =============================================
# BASE SCHEMA
# =============================================
class JobBase(BaseModel):
    job_name: str = Field(..., min_length=1, max_length=255, description="Nome da vaga")
    activities: Optional[str] = Field(None, description="Atividades da vaga")
    pre_requisites: Optional[str] = Field(None, description="Pré-requisitos obrigatórios")
    differentials: Optional[str] = Field(None, description="Diferenciais desejados")
    code_vacancy_job: str = Field(..., min_length=1, max_length=50, description="Código único da vaga")
    company_id: UUID = Field(..., description="ID da empresa")

    @validator('job_name')
    def validate_job_name(cls, v):
        """Validate job name"""
        if not v or not v.strip():
            raise ValueError("Nome da vaga é obrigatório")
        return v.strip()

    @validator('code_vacancy_job')
    def validate_code_vacancy_job(cls, v):
        """Validate job code format"""
        if not v or not v.strip():
            raise ValueError("Código da vaga é obrigatório")
        
        # Allow alphanumeric and some special characters
        if not re.match(r'^[A-Za-z0-9_-]+$', v.strip()):
            raise ValueError("Código da vaga deve conter apenas letras, números, _ ou -")
        
        return v.strip().upper()

# =============================================
# CREATE SCHEMA
# =============================================
class JobCreate(JobBase):
    """Schema para criação de vaga"""
    pass

# =============================================
# UPDATE SCHEMA
# =============================================
class JobUpdate(BaseModel):
    """Schema para atualização de vaga (campos opcionais)"""
    job_name: Optional[str] = Field(None, min_length=1, max_length=255)
    activities: Optional[str] = None
    pre_requisites: Optional[str] = None
    differentials: Optional[str] = None
    code_vacancy_job: Optional[str] = Field(None, min_length=1, max_length=50)

    @validator('job_name')
    def validate_job_name(cls, v):
        """Validate job name if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Nome da vaga não pode ser vazio")
        return v.strip() if v else v

    @validator('code_vacancy_job')
    def validate_code_vacancy_job(cls, v):
        """Validate job code format if provided"""
        if v is None:
            return v
            
        if not v.strip():
            raise ValueError("Código da vaga não pode ser vazio")
            
        if not re.match(r'^[A-Za-z0-9_-]+$', v.strip()):
            raise ValueError("Código da vaga deve conter apenas letras, números, _ ou -")
        
        return v.strip().upper()

# =============================================
# RESPONSE SCHEMA
# =============================================
class JobResponse(JobBase):
    """Schema para resposta da API"""
    model_config = ConfigDict(from_attributes=True)
    
    job_id: UUID
    created_date: datetime
    updated_date: Optional[datetime] = None
    deleted_date: Optional[datetime] = None

# =============================================
# DETAIL SCHEMA
# =============================================
class JobDetail(JobResponse):
    """Schema para resposta detalhada com relacionamentos"""
    create_user_id: Optional[UUID] = None
    
    # Company information
    company_name: Optional[str] = Field(None, description="Nome da empresa")
    company_area: Optional[str] = Field(None, description="Área de atividade da empresa")
    
    # Application statistics
    total_applications: Optional[int] = Field(None, description="Total de candidaturas")
    pending_applications: Optional[int] = Field(None, description="Candidaturas pendentes")
    analyzed_applications: Optional[int] = Field(None, description="Candidaturas analisadas")
    
    # Job status
    is_active: bool = Field(True, description="Se a vaga está ativa")
    
    @validator('is_active')
    def validate_is_active(cls, v, values):
        """Check if job is active based on deleted_date"""
        deleted_date = values.get('deleted_date')
        return deleted_date is None

# =============================================
# SUMMARY SCHEMA
# =============================================
class JobSummary(BaseModel):
    """Schema resumido para listagens"""
    model_config = ConfigDict(from_attributes=True)
    
    job_id: UUID
    job_name: str
    code_vacancy_job: str
    company_id: UUID
    company_name: Optional[str] = None
    created_date: datetime
    total_applications: Optional[int] = 0

# =============================================
# SEARCH FILTERS SCHEMA
# =============================================
class JobSearchFilters(BaseModel):
    """Schema para filtros de busca"""
    job_name: Optional[str] = Field(None, description="Filtrar por nome da vaga")
    company_id: Optional[UUID] = Field(None, description="Filtrar por empresa")
    company_name: Optional[str] = Field(None, description="Filtrar por nome da empresa")
    keywords: Optional[str] = Field(None, description="Palavras-chave em atividades, pré-requisitos ou diferenciais")
    code_vacancy_job: Optional[str] = Field(None, description="Filtrar por código da vaga")
    is_active: Optional[bool] = Field(True, description="Filtrar vagas ativas")
    created_after: Optional[datetime] = Field(None, description="Filtrar por data de criação")
    created_before: Optional[datetime] = Field(None, description="Filtrar por data de criação")
    has_applications: Optional[bool] = Field(None, description="Filtrar vagas com candidaturas")

# =============================================
# STATISTICS SCHEMA
# =============================================
class JobStatistics(BaseModel):
    """Schema para estatísticas da vaga"""
    model_config = ConfigDict(from_attributes=True)
    
    job_id: UUID
    total_applications: int = 0
    pending_analysis: int = 0
    analyzed_applications: int = 0
    avg_score: Optional[float] = None
    highest_score: Optional[float] = None
    lowest_score: Optional[float] = None
    top_candidate_id: Optional[UUID] = None
    applications_by_day: Optional[dict] = None  # For charts

# =============================================
# RANKING SCHEMA
# =============================================
class JobCandidateRanking(BaseModel):
    """Schema para ranking de candidatos da vaga"""
    model_config = ConfigDict(from_attributes=True)
    
    application_id: UUID
    user_id: UUID
    user_name: str
    user_email: str
    total_score: float
    academic_score: Optional[float] = None
    professional_experience_score: Optional[float] = None
    professional_courses_score: Optional[float] = None
    strong_points_score: Optional[float] = None
    weak_points_score: Optional[float] = None
    analysis_date: Optional[datetime] = None
    ranking_position: Optional[int] = None