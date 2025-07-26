# =============================================
# app/schemas/professional_profile.py
# =============================================
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# =============================================
# BASE SCHEMA
# =============================================
class ProfessionalProfileBase(BaseModel):
    professional_profile_name: str = Field(..., min_length=1, max_length=255, description="Nome do perfil profissional")
    professional_profile_description: Optional[str] = Field(None, description="Descrição do perfil profissional")
    user_id: UUID = Field(..., description="ID do usuário")
    
    # Optional related IDs
    academic_background_id: Optional[UUID] = Field(None, description="ID da formação acadêmica principal")
    professional_experience_id: Optional[UUID] = Field(None, description="ID da experiência profissional principal")
    professional_courses_id: Optional[UUID] = Field(None, description="ID do curso profissional principal")

    @validator('professional_profile_name')
    def validate_profile_name(cls, v):
        """Validate profile name"""
        if not v or not v.strip():
            raise ValueError("Nome do perfil profissional é obrigatório")
        return v.strip()

# =============================================
# CREATE SCHEMA
# =============================================
class ProfessionalProfileCreate(ProfessionalProfileBase):
    """Schema para criação de perfil profissional"""
    pass

# =============================================
# UPDATE SCHEMA
# =============================================
class ProfessionalProfileUpdate(BaseModel):
    """Schema para atualização de perfil profissional (campos opcionais)"""
    professional_profile_name: Optional[str] = Field(None, min_length=1, max_length=255)
    professional_profile_description: Optional[str] = None
    academic_background_id: Optional[UUID] = None
    professional_experience_id: Optional[UUID] = None
    professional_courses_id: Optional[UUID] = None

    @validator('professional_profile_name')
    def validate_profile_name(cls, v):
        """Validate profile name if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Nome do perfil profissional não pode ser vazio")
        return v.strip() if v else v

# =============================================
# RESPONSE SCHEMA
# =============================================
class ProfessionalProfileResponse(ProfessionalProfileBase):
    """Schema para resposta da API"""
    model_config = ConfigDict(from_attributes=True)
    
    professional_profile_id: UUID
    created_date: datetime
    updated_date: Optional[datetime] = None
    deleted_date: Optional[datetime] = None

# =============================================
# DETAIL SCHEMA
# =============================================
class ProfessionalProfileDetail(ProfessionalProfileResponse):
    """Schema para resposta detalhada com relacionamentos"""
    create_user_id: Optional[UUID] = None
    
    # User information
    user_name: Optional[str] = Field(None, description="Nome do usuário")
    user_email: Optional[str] = Field(None, description="Email do usuário")
    
    # Profile statistics
    total_applications: Optional[int] = Field(None, description="Total de candidaturas")
    total_analyses: Optional[int] = Field(None, description="Total de análises realizadas")
    avg_score: Optional[float] = Field(None, description="Pontuação média nas análises")
    
    # Profile completeness
    has_academic_background: bool = Field(False, description="Possui formação acadêmica")
    has_professional_experience: bool = Field(False, description="Possui experiência profissional")
    has_professional_courses: bool = Field(False, description="Possui cursos profissionais")
    completeness_percentage: Optional[float] = Field(None, description="Percentual de completude do perfil")

# =============================================
# SUMMARY SCHEMA
# =============================================
class ProfessionalProfileSummary(BaseModel):
    """Schema resumido para listagens"""
    model_config = ConfigDict(from_attributes=True)
    
    professional_profile_id: UUID
    professional_profile_name: str
    user_id: UUID
    user_name: Optional[str] = None
    created_date: datetime
    completeness_percentage: Optional[float] = None

# =============================================
# SEARCH FILTERS SCHEMA
# =============================================
class ProfessionalProfileSearchFilters(BaseModel):
    """Schema para filtros de busca"""
    professional_profile_name: Optional[str] = Field(None, description="Filtrar por nome do perfil")
    user_id: Optional[UUID] = Field(None, description="Filtrar por usuário")
    user_name: Optional[str] = Field(None, description="Filtrar por nome do usuário")
    user_email: Optional[str] = Field(None, description="Filtrar por email do usuário")
    has_academic_background: Optional[bool] = Field(None, description="Filtrar por formação acadêmica")
    has_professional_experience: Optional[bool] = Field(None, description="Filtrar por experiência profissional")
    has_professional_courses: Optional[bool] = Field(None, description="Filtrar por cursos profissionais")
    min_completeness: Optional[float] = Field(None, ge=0, le=100, description="Completude mínima do perfil")
    created_after: Optional[datetime] = Field(None, description="Filtrar por data de criação")
    created_before: Optional[datetime] = Field(None, description="Filtrar por data de criação")

# =============================================
# COMPLETENESS SCHEMA
# =============================================
class ProfileCompletenessInfo(BaseModel):
    """Schema para informações de completude do perfil"""
    model_config = ConfigDict(from_attributes=True)
    
    professional_profile_id: UUID
    completeness_percentage: float = Field(..., ge=0, le=100)
    missing_items: List[str] = Field(default_factory=list, description="Itens faltando no perfil")
    completed_items: List[str] = Field(default_factory=list, description="Itens completados no perfil")
    suggestions: List[str] = Field(default_factory=list, description="Sugestões para melhorar o perfil")
    
    # Detailed completeness
    basic_info_complete: bool = Field(False, description="Informações básicas completas")
    academic_complete: bool = Field(False, description="Formação acadêmica completa")
    experience_complete: bool = Field(False, description="Experiência profissional completa")
    courses_complete: bool = Field(False, description="Cursos profissionais completos")

# =============================================
# STATISTICS SCHEMA
# =============================================
class ProfessionalProfileStatistics(BaseModel):
    """Schema para estatísticas do perfil profissional"""
    model_config = ConfigDict(from_attributes=True)
    
    professional_profile_id: UUID
    total_applications: int = 0
    successful_applications: int = 0
    pending_applications: int = 0
    avg_score: Optional[float] = None
    highest_score: Optional[float] = None
    lowest_score: Optional[float] = None
    best_performing_skills: List[str] = Field(default_factory=list)
    improvement_areas: List[str] = Field(default_factory=list)
    application_trend: Optional[dict] = None  # For charts