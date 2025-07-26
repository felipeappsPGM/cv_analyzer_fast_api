# =============================================
# app/schemas/academic_background.py
# =============================================
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from enum import Enum

# =============================================
# ENUMS
# =============================================
class DegreeTypeEnum(str, Enum):
    ENSINO_MEDIO = "Ensino Médio"
    TECNICO = "Técnico"
    TECNOLOGIA = "Tecnólogo"
    GRADUACAO = "Graduação"
    POS_GRADUACAO = "Pós-graduação"
    ESPECIALIZACAO = "Especialização"
    MBA = "MBA"
    MESTRADO = "Mestrado"
    DOUTORADO = "Doutorado"
    POS_DOUTORADO = "Pós-doutorado"

class AcademicStatusEnum(str, Enum):
    CONCLUIDO = "Concluído"
    EM_ANDAMENTO = "Em Andamento"
    TRANCADO = "Trancado"
    INCOMPLETO = "Incompleto"

# =============================================
# BASE SCHEMA
# =============================================
class AcademicBackgroundBase(BaseModel):
    degree_name: str = Field(..., min_length=1, max_length=255, description="Nome do curso/diploma")
    degree_type: DegreeTypeEnum = Field(..., description="Tipo de formação")
    field_of_study: str = Field(..., min_length=1, max_length=255, description="Área de estudo")
    institution_name: str = Field(..., min_length=1, max_length=255, description="Nome da instituição")
    start_date: date = Field(..., description="Data de início")
    end_date: Optional[date] = Field(None, description="Data de conclusão")
    user_id: UUID = Field(..., description="ID do usuário")

    @validator('degree_name')
    def validate_degree_name(cls, v):
        """Validate degree name"""
        if not v or not v.strip():
            raise ValueError("Nome do curso/diploma é obrigatório")
        return v.strip()

    @validator('field_of_study')
    def validate_field_of_study(cls, v):
        """Validate field of study"""
        if not v or not v.strip():
            raise ValueError("Área de estudo é obrigatória")
        return v.strip()

    @validator('institution_name')
    def validate_institution_name(cls, v):
        """Validate institution name"""
        if not v or not v.strip():
            raise ValueError("Nome da instituição é obrigatório")
        return v.strip()

    @validator('end_date')
    def validate_dates(cls, v, values):
        """Validate date logic"""
        start_date = values.get('start_date')
        
        if start_date and v and v <= start_date:
            raise ValueError("Data de conclusão deve ser posterior à data de início")
        
        if v and v > date.today():
            raise ValueError("Data de conclusão não pode ser futura")
            
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
class AcademicBackgroundCreate(AcademicBackgroundBase):
    """Schema para criação de formação acadêmica"""
    pass

# =============================================
# UPDATE SCHEMA
# =============================================
class AcademicBackgroundUpdate(BaseModel):
    """Schema para atualização de formação acadêmica (campos opcionais)"""
    degree_name: Optional[str] = Field(None, min_length=1, max_length=255)
    degree_type: Optional[DegreeTypeEnum] = None
    field_of_study: Optional[str] = Field(None, min_length=1, max_length=255)
    institution_name: Optional[str] = Field(None, min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @validator('degree_name', 'field_of_study', 'institution_name')
    def validate_text_fields(cls, v):
        """Validate text fields if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Campo não pode ser vazio")
        return v.strip() if v else v

    @validator('end_date')
    def validate_dates(cls, v, values):
        """Validate date logic if provided"""
        start_date = values.get('start_date')
        
        if start_date and v and v <= start_date:
            raise ValueError("Data de conclusão deve ser posterior à data de início")
        
        if v and v > date.today():
            raise ValueError("Data de conclusão não pode ser futura")
            
        return v

# =============================================
# RESPONSE SCHEMA
# =============================================
class AcademicBackgroundResponse(AcademicBackgroundBase):
    """Schema para resposta da API"""
    model_config = ConfigDict(from_attributes=True)
    
    academic_background_id: UUID
    created_date: datetime
    updated_date: Optional[datetime] = None
    deleted_date: Optional[datetime] = None

# =============================================
# DETAIL SCHEMA
# =============================================
class AcademicBackgroundDetail(AcademicBackgroundResponse):
    """Schema para resposta detalhada com relacionamentos"""
    create_user_id: Optional[UUID] = None
    
    # Calculated fields
    duration_months: Optional[int] = Field(None, description="Duração em meses")
    duration_years: Optional[float] = Field(None, description="Duração em anos")
    duration_formatted: Optional[str] = Field(None, description="Duração formatada")
    status: AcademicStatusEnum = Field(..., description="Status da formação")
    is_completed: bool = Field(..., description="Se a formação foi concluída")
    
    # User information
    user_name: Optional[str] = Field(None, description="Nome do usuário")

    @validator('duration_months', always=True)
    def calculate_duration_months(cls, v, values):
        """Calculate duration in months"""
        start_date = values.get('start_date')
        end_date = values.get('end_date')
        
        if not start_date:
            return None
            
        if not end_date:
            # If no end date, calculate until today (ongoing)
            end_date = date.today()
            
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

    @validator('is_completed', always=True)
    def calculate_is_completed(cls, v, values):
        """Check if the academic background is completed"""
        end_date = values.get('end_date')
        return end_date is not None and end_date <= date.today()

    @validator('status', always=True)
    def calculate_status(cls, v, values):
        """Calculate status based on dates"""
        start_date = values.get('start_date')
        end_date = values.get('end_date')
        
        if not start_date:
            return AcademicStatusEnum.INCOMPLETO
            
        if end_date:
            if end_date <= date.today():
                return AcademicStatusEnum.CONCLUIDO
            else:
                return AcademicStatusEnum.EM_ANDAMENTO
        else:
            # No end date means ongoing
            return AcademicStatusEnum.EM_ANDAMENTO

# =============================================
# SUMMARY SCHEMA
# =============================================
class AcademicBackgroundSummary(BaseModel):
    """Schema resumido para listagens"""
    model_config = ConfigDict(from_attributes=True)
    
    academic_background_id: UUID
    degree_name: str
    degree_type: DegreeTypeEnum
    field_of_study: str
    institution_name: str
    start_date: date
    end_date: Optional[date] = None
    status: AcademicStatusEnum
    duration_formatted: Optional[str] = None

# =============================================
# SEARCH FILTERS SCHEMA
# =============================================
class AcademicBackgroundSearchFilters(BaseModel):
    """Schema para filtros de busca"""
    user_id: Optional[UUID] = Field(None, description="Filtrar por usuário")
    degree_name: Optional[str] = Field(None, description="Filtrar por nome do curso")
    degree_type: Optional[DegreeTypeEnum] = Field(None, description="Filtrar por tipo de formação")
    field_of_study: Optional[str] = Field(None, description="Filtrar por área de estudo")
    institution_name: Optional[str] = Field(None, description="Filtrar por instituição")
    status: Optional[AcademicStatusEnum] = Field(None, description="Filtrar por status")
    is_completed: Optional[bool] = Field(None, description="Filtrar formações concluídas")
    min_duration_months: Optional[int] = Field(None, ge=0, description="Duração mínima em meses")
    max_duration_months: Optional[int] = Field(None, ge=0, description="Duração máxima em meses")
    start_date_after: Optional[date] = Field(None, description="Data de início posterior a")
    start_date_before: Optional[date] = Field(None, description="Data de início anterior a")
    graduation_year: Optional[int] = Field(None, ge=1950, le=2030, description="Ano de formatura")

# =============================================
# STATISTICS SCHEMA
# =============================================
class AcademicBackgroundStatistics(BaseModel):
    """Schema para estatísticas de formação acadêmica"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: UUID
    total_academic_backgrounds: int = 0
    completed_degrees: int = 0
    ongoing_degrees: int = 0
    highest_degree_type: Optional[DegreeTypeEnum] = None
    total_study_duration_months: int = 0
    total_study_duration_years: float = 0.0
    institutions_attended: List[str] = Field(default_factory=list)
    fields_of_study: List[str] = Field(default_factory=list)
    degree_types_completed: List[DegreeTypeEnum] = Field(default_factory=list)
    academic_progression: Optional[dict] = None  # For charts

# =============================================
# VALIDATION HELPERS SCHEMA
# =============================================
class InstitutionSuggestion(BaseModel):
    """Schema para sugestões de instituições"""
    institution_name: str
    confidence_score: float = Field(..., ge=0, le=1)
    alternative_names: List[str] = Field(default_factory=list)

class FieldOfStudySuggestion(BaseModel):
    """Schema para sugestões de área de estudo"""
    field_name: str
    category: str
    related_fields: List[str] = Field(default_factory=list)