# =============================================
# app/schemas/professional_courses.py
# =============================================
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from enum import Enum

# =============================================
# ENUMS
# =============================================
class CourseStatusEnum(str, Enum):
    CONCLUIDO = "Concluído"
    EM_ANDAMENTO = "Em Andamento"
    TRANCADO = "Trancado"
    CANCELADO = "Cancelado"

class CourseCategoryEnum(str, Enum):
    TECNOLOGIA = "Tecnologia"
    NEGOCIOS = "Negócios"
    IDIOMAS = "Idiomas"
    DESIGN = "Design"
    MARKETING = "Marketing"
    GESTAO = "Gestão"
    FINANCAS = "Finanças"
    VENDAS = "Vendas"
    RH = "Recursos Humanos"
    JURIDICO = "Jurídico"
    SAUDE = "Saúde"
    EDUCACAO = "Educação"
    ENGENHARIA = "Engenharia"
    CERTIFICACAO = "Certificação"
    OUTROS = "Outros"

# =============================================
# BASE SCHEMA
# =============================================
class ProfessionalCoursesBase(BaseModel):
    course_name: str = Field(..., min_length=1, max_length=255, description="Nome do curso")
    institution_name: str = Field(..., min_length=1, max_length=255, description="Nome da instituição")
    token_id: Optional[str] = Field(None, max_length=255, description="ID do certificado/token")
    duration_time_hours: Optional[int] = Field(None, ge=1, le=10000, description="Duração em horas")
    start_date: Optional[date] = Field(None, description="Data de início")
    end_date: Optional[date] = Field(None, description="Data de conclusão")
    user_id: UUID = Field(..., description="ID do usuário")

    @validator('course_name')
    def validate_course_name(cls, v):
        """Validate course name"""
        if not v or not v.strip():
            raise ValueError("Nome do curso é obrigatório")
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
        if v and v > date.today():
            raise ValueError("Data de início não pode ser futura")
        
        # Check if date is reasonable (not too old)
        if v and v < date(1990, 1, 1):
            raise ValueError("Data de início muito antiga")
            
        return v

    @validator('duration_time_hours')
    def validate_duration(cls, v):
        """Validate duration hours"""
        if v is not None and v <= 0:
            raise ValueError("Duração deve ser maior que zero")
        return v

# =============================================
# CREATE SCHEMA
# =============================================
class ProfessionalCoursesCreate(ProfessionalCoursesBase):
    """Schema para criação de curso profissional"""
    # Optional files for certification media
    certification_media_pdf: Optional[bytes] = Field(None, description="PDF do certificado")
    certification_media_image: Optional[bytes] = Field(None, description="Imagem do certificado")

# =============================================
# UPDATE SCHEMA
# =============================================
class ProfessionalCoursesUpdate(BaseModel):
    """Schema para atualização de curso profissional (campos opcionais)"""
    course_name: Optional[str] = Field(None, min_length=1, max_length=255)
    institution_name: Optional[str] = Field(None, min_length=1, max_length=255)
    token_id: Optional[str] = Field(None, max_length=255)
    duration_time_hours: Optional[int] = Field(None, ge=1, le=10000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    certification_media_pdf: Optional[bytes] = None
    certification_media_image: Optional[bytes] = None

    @validator('course_name', 'institution_name')
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
class ProfessionalCoursesResponse(ProfessionalCoursesBase):
    """Schema para resposta da API (sem arquivos binários)"""
    model_config = ConfigDict(from_attributes=True)
    
    professional_courses_id: UUID
    created_date: datetime
    updated_date: Optional[datetime] = None
    deleted_date: Optional[datetime] = None
    
    # Indicate presence of certification media without including the data
    has_pdf_certificate: bool = Field(False, description="Se possui certificado PDF")
    has_image_certificate: bool = Field(False, description="Se possui certificado em imagem")

# =============================================
# DETAIL SCHEMA
# =============================================
class ProfessionalCoursesDetail(ProfessionalCoursesResponse):
    """Schema para resposta detalhada com relacionamentos"""
    create_user_id: Optional[UUID] = None
    
    # Calculated fields
    duration_months: Optional[int] = Field(None, description="Duração em meses")
    duration_formatted: Optional[str] = Field(None, description="Duração formatada")
    status: CourseStatusEnum = Field(..., description="Status do curso")
    is_completed: bool = Field(..., description="Se o curso foi concluído")
    category: Optional[CourseCategoryEnum] = Field(None, description="Categoria do curso")
    
    # User information
    user_name: Optional[str] = Field(None, description="Nome do usuário")
    
    # Certification info
    certificate_download_url: Optional[str] = Field(None, description="URL para download do certificado")

    @validator('duration_months', always=True)
    def calculate_duration_months(cls, v, values):
        """Calculate duration in months based on dates or hours"""
        start_date = values.get('start_date')
        end_date = values.get('end_date')
        duration_hours = values.get('duration_time_hours')
        
        # Try to calculate from dates first
        if start_date and end_date:
            delta = end_date - start_date
            return int(delta.days / 30.44)  # Average days per month
        
        # Fallback to hours estimation (assuming 20 hours per month for part-time study)
        if duration_hours:
            return max(1, int(duration_hours / 20))
            
        return None

    @validator('duration_formatted', always=True)
    def format_duration(cls, v, values):
        """Format duration as human-readable string"""
        duration_hours = values.get('duration_time_hours')
        start_date = values.get('start_date')
        end_date = values.get('end_date')
        
        # If we have duration in hours, use that
        if duration_hours:
            if duration_hours < 24:
                return f"{duration_hours} horas"
            else:
                days = duration_hours // 8  # Assuming 8 hours per day
                return f"{days} dias ({duration_hours}h)"
        
        # Otherwise use date calculation
        duration_months = values.get('duration_months')
        if duration_months is None:
            return None
            
        if duration_months < 1:
            return "Menos de 1 mês"
        elif duration_months < 12:
            return f"{duration_months} {'mês' if duration_months == 1 else 'meses'}"
        else:
            years = duration_months // 12
            months = duration_months % 12
            parts = []
            if years > 0:
                parts.append(f"{years} {'ano' if years == 1 else 'anos'}")
            if months > 0:
                parts.append(f"{months} {'mês' if months == 1 else 'meses'}")
            return " e ".join(parts)

    @validator('is_completed', always=True)
    def calculate_is_completed(cls, v, values):
        """Check if the course is completed"""
        end_date = values.get('end_date')
        return end_date is not None and end_date <= date.today()

    @validator('status', always=True)
    def calculate_status(cls, v, values):
        """Calculate status based on dates"""
        start_date = values.get('start_date')
        end_date = values.get('end_date')
        
        if end_date:
            if end_date <= date.today():
                return CourseStatusEnum.CONCLUIDO
            else:
                return CourseStatusEnum.EM_ANDAMENTO
        elif start_date:
            return CourseStatusEnum.EM_ANDAMENTO
        else:
            return CourseStatusEnum.EM_ANDAMENTO

# =============================================
# SUMMARY SCHEMA
# =============================================
class ProfessionalCoursesSummary(BaseModel):
    """Schema resumido para listagens"""
    model_config = ConfigDict(from_attributes=True)
    
    professional_courses_id: UUID
    course_name: str
    institution_name: str
    duration_time_hours: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: CourseStatusEnum
    category: Optional[CourseCategoryEnum] = None
    has_certificate: bool = Field(False, description="Se possui certificado")

# =============================================
# SEARCH FILTERS SCHEMA
# =============================================
class ProfessionalCoursesSearchFilters(BaseModel):
    """Schema para filtros de busca"""
    user_id: Optional[UUID] = Field(None, description="Filtrar por usuário")
    course_name: Optional[str] = Field(None, description="Filtrar por nome do curso")
    institution_name: Optional[str] = Field(None, description="Filtrar por instituição")
    category: Optional[CourseCategoryEnum] = Field(None, description="Filtrar por categoria")
    status: Optional[CourseStatusEnum] = Field(None, description="Filtrar por status")
    is_completed: Optional[bool] = Field(None, description="Filtrar cursos concluídos")
    has_certificate: Optional[bool] = Field(None, description="Filtrar com certificado")
    min_duration_hours: Optional[int] = Field(None, ge=0, description="Duração mínima em horas")
    max_duration_hours: Optional[int] = Field(None, ge=0, description="Duração máxima em horas")
    start_date_after: Optional[date] = Field(None, description="Data de início posterior a")
    start_date_before: Optional[date] = Field(None, description="Data de início anterior a")
    completion_year: Optional[int] = Field(None, ge=1990, le=2030, description="Ano de conclusão")

# =============================================
# STATISTICS SCHEMA
# =============================================
class ProfessionalCoursesStatistics(BaseModel):
    """Schema para estatísticas de cursos profissionais"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: UUID
    total_courses: int = 0
    completed_courses: int = 0
    ongoing_courses: int = 0
    total_study_hours: int = 0
    avg_course_duration_hours: Optional[float] = None
    institutions_attended: List[str] = Field(default_factory=list)
    course_categories: List[CourseCategoryEnum] = Field(default_factory=list)
    certificates_earned: int = 0
    most_studied_category: Optional[CourseCategoryEnum] = None
    courses_by_year: Optional[dict] = None  # For charts
    skill_development_trend: Optional[dict] = None

# =============================================
# CERTIFICATE SCHEMAS
# =============================================
class CertificateUpload(BaseModel):
    """Schema para upload de certificado"""
    file_type: str = Field(..., pattern="^(pdf|image)$", description="Tipo do arquivo")
    file_data: bytes = Field(..., description="Dados do arquivo")
    file_name: str = Field(..., max_length=255, description="Nome do arquivo")

class CertificateInfo(BaseModel):
    """Schema para informações do certificado"""
    professional_courses_id: UUID
    has_pdf: bool
    has_image: bool
    upload_date: datetime
    file_size_bytes: Optional[int] = None
    download_urls: dict = Field(default_factory=dict)

# =============================================
# BULK OPERATIONS SCHEMA
# =============================================
class BulkCoursesCreate(BaseModel):
    """Schema para criação em lote de cursos"""
    user_id: UUID
    courses: List[ProfessionalCoursesCreate] = Field(..., min_items=1, max_items=50)

class BulkCoursesResponse(BaseModel):
    """Schema para resposta de criação em lote"""
    created_courses: List[ProfessionalCoursesResponse]
    failed_courses: List[dict] = Field(default_factory=list)
    total_created: int
    total_failed: int

# =============================================
# SKILL EXTRACTION SCHEMA
# =============================================
class ExtractedSkills(BaseModel):
    """Schema para skills extraídas dos cursos"""
    professional_courses_id: UUID
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    tools_and_technologies: List[str] = Field(default_factory=list)
    confidence_scores: dict = Field(default_factory=dict)