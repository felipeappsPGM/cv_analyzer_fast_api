# =============================================
# app/schemas/professional_experience.py
# =============================================
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List
from datetime import date, datetime, timedelta
from uuid import UUID
from enum import Enum

# =============================================
# ENUMS
# =============================================
class EmploymentTypeEnum(str, Enum):
    CLT = "CLT"
    PJ = "PJ"
    ESTAGIO = "Estágio"
    FREELANCER = "Freelancer"
    AUTONOMO = "Autônomo"
    TERCEIRIZADO = "Terceirizado"
    COOPERADO = "Cooperado"
    TEMPORARIO = "Temporário"
    OUTRO = "Outro"

# =============================================
# BASE SCHEMA
# =============================================
class ProfessionalExperienceBase(BaseModel):
    job_title: str = Field(..., min_length=1, max_length=255, description="Cargo/Função")
    company_name: str = Field(..., min_length=1, max_length=255, description="Nome da empresa")
    employment_type: Optional[EmploymentTypeEnum] = Field(None, description="Tipo de contratação")
    location: Optional[str] = Field(None, max_length=255, description="Localização do trabalho")
    start_date: date = Field(..., description="Data de início")
    end_date: Optional[date] = Field(None, description="Data de fim (null se atual)")
    is_current: bool = Field(False, description="Se é o trabalho atual")
    user_id: UUID = Field(..., description="ID do usuário")

    @validator('job_title')
    def validate_job_title(cls, v):
        """Validate job title"""
        if not v or not v.strip():
            raise ValueError("Cargo/Função é obrigatório")
        return v.strip()

    @validator('company_name')
    def validate_company_name(cls, v):
        """Validate company name"""
        if not v or not v.strip():
            raise ValueError("Nome da empresa é obrigatório")
        return v.strip()

    @validator('end_date')
    def validate_dates(cls, v, values):
        """Validate date logic"""
        start_date = values.get('start_date')
        is_current = values.get('is_current', False)
        
        if is_current and v is not None:
            raise ValueError("Trabalho atual não deve ter data de fim")
        
        if not is_current and v is None:
            raise ValueError("Trabalho finalizado deve ter data de fim")
            
        if start_date and v and v <= start_date:
            raise ValueError("Data de fim deve ser posterior à data de início")
        
        if v and v > date.today():
            raise ValueError("Data de fim não pode ser futura")
            
        return v

    @validator('start_date')
    def validate_start_date(cls, v):
        """Validate start date"""
        if v > date.today():
            raise ValueError("Data de início não pode ser futura")
        
        # Check if date is reasonable (not too old)
        if v < date(1950, 1, 1):
            raise ValueError("Data de início muito antiga")
            
        return v

# =============================================
# CREATE SCHEMA
# =============================================
class ProfessionalExperienceCreate(ProfessionalExperienceBase):
    """Schema para criação de experiência profissional"""
    pass

# =============================================
# UPDATE SCHEMA
# =============================================
class ProfessionalExperienceUpdate(BaseModel):
    """Schema para atualização de experiência profissional (campos opcionais)"""
    job_title: Optional[str] = Field(None, min_length=1, max_length=255)
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    employment_type: Optional[EmploymentTypeEnum] = None
    location: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None

    @validator('job_title')
    def validate_job_title(cls, v):
        """Validate job title if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Cargo/Função não pode ser vazio")
        return v.strip() if v else v

    @validator('company_name')
    def validate_company_name(cls, v):
        """Validate company name if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Nome da empresa não pode ser vazio")
        return v.strip() if v else v

    @validator('end_date')
    def validate_dates(cls, v, values):
        """Validate date logic if provided"""
        start_date = values.get('start_date')
        is_current = values.get('is_current')
        
        if is_current and v is not None:
            raise ValueError("Trabalho atual não deve ter data de fim")
            
        if start_date and v and v <= start_date:
            raise ValueError("Data de fim deve ser posterior à data de início")
        
        if v and v > date.today():
            raise ValueError("Data de fim não pode ser futura")
            
        return v

# =============================================
# RESPONSE SCHEMA
# =============================================
class ProfessionalExperienceResponse(ProfessionalExperienceBase):
    """Schema para resposta da API"""
    model_config = ConfigDict(from_attributes=True)
    
    professional_experience_id: UUID
    created_date: datetime
    updated_date: Optional[datetime] = None
    deleted_date: Optional[datetime] = None

# =============================================
# DETAIL SCHEMA
# =============================================
class ProfessionalExperienceDetail(ProfessionalExperienceResponse):
    """Schema para resposta detalhada com relacionamentos"""
    create_user_id: Optional[UUID] = None
    
    # Calculated fields
    duration_months: Optional[int] = Field(None, description="Duração em meses")
    duration_years: Optional[float] = Field(None, description="Duração em anos")
    duration_formatted: Optional[str] = Field(None, description="Duração formatada")
    
    # User information
    user_name: Optional[str] = Field(None, description="Nome do usuário")

    @validator('duration_months', always=True)
    def calculate_duration_months(cls, v, values):
        """Calculate duration in months"""
        start_date = values.get('start_date')
        end_date = values.get('end_date')
        is_current = values.get('is_current', False)
        
        if not start_date:
            return None
            
        if is_current:
            end_date = date.today()
        elif not end_date:
            return None
            
        delta = end_date - start_date
        return int(delta.days / 30.44)  # Average days per month

    @validator('duration_years', always=True)
    def calculate_duration_years(cls, v, values):
        """Calculate duration in years"""
        duration_months = values.get('duration_months')
        if duration_months is None:
            return None
        return round(duration_months / 12, 1)

    @validator('duration_formatted', always=True)
    def format_duration(cls, v, values):
        """Format duration as human-readable string"""
        duration_months = values.get('duration_months')
        if duration_months is None:
            return None
            
        years = duration_months // 12
        months = duration_months % 12
        
        parts = []
        if years > 0:
            parts.append(f"{years} {'ano' if years == 1 else 'anos'}")
        if months > 0:
            parts.append(f"{months} {'mês' if months == 1 else 'meses'}")
            
        return " e ".join(parts) if parts else "Menos de 1 mês"

# =============================================
# SUMMARY SCHEMA
# =============================================
class ProfessionalExperienceSummary(BaseModel):
    """Schema resumido para listagens"""
    model_config = ConfigDict(from_attributes=True)
    
    professional_experience_id: UUID
    job_title: str
    company_name: str
    employment_type: Optional[EmploymentTypeEnum] = None
    start_date: date
    end_date: Optional[date] = None
    is_current: bool
    duration_formatted: Optional[str] = None

# =============================================
# SEARCH FILTERS SCHEMA
# =============================================
class ProfessionalExperienceSearchFilters(BaseModel):
    """Schema para filtros de busca"""
    user_id: Optional[UUID] = Field(None, description="Filtrar por usuário")
    job_title: Optional[str] = Field(None, description="Filtrar por cargo")
    company_name: Optional[str] = Field(None, description="Filtrar por empresa")
    employment_type: Optional[EmploymentTypeEnum] = Field(None, description="Filtrar por tipo de contratação")
    location: Optional[str] = Field(None, description="Filtrar por localização")
    is_current: Optional[bool] = Field(None, description="Filtrar trabalhos atuais")
    min_duration_months: Optional[int] = Field(None, ge=0, description="Duração mínima em meses")
    max_duration_months: Optional[int] = Field(None, ge=0, description="Duração máxima em meses")
    start_date_after: Optional[date] = Field(None, description="Data de início posterior a")
    start_date_before: Optional[date] = Field(None, description="Data de início anterior a")

# =============================================
# STATISTICS SCHEMA
# =============================================
class ProfessionalExperienceStatistics(BaseModel):
    """Schema para estatísticas de experiência profissional"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: UUID
    total_experiences: int = 0
    current_positions: int = 0
    total_duration_months: int = 0
    total_duration_years: float = 0.0
    avg_duration_months: Optional[float] = None
    most_common_employment_type: Optional[EmploymentTypeEnum] = None
    companies_worked: List[str] = Field(default_factory=list)
    job_titles_held: List[str] = Field(default_factory=list)
    career_progression: Optional[dict] = None  # For charts