# =============================================
# app/schemas/curriculum.py
# =============================================
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID
from enum import Enum
import re

# =============================================
# ENUMS
# =============================================
class FileTypeEnum(str, Enum):
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    TXT = "txt"

class CurriculumStatusEnum(str, Enum):
    PENDING = "Pendente"
    PROCESSING = "Processando"
    PROCESSED = "Processado"
    FAILED = "Falha no Processamento"
    ACTIVE = "Ativo"
    ARCHIVED = "Arquivado"

# =============================================
# BASE SCHEMA
# =============================================
class CurriculumBase(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=255, description="Nome do arquivo")
    is_work: bool = Field(True, description="Se é currículo profissional")
    user_id: UUID = Field(..., description="ID do usuário")

    @validator('file_name')
    def validate_file_name(cls, v):
        """Validate file name and extension"""
        if not v or not v.strip():
            raise ValueError("Nome do arquivo é obrigatório")
        
        # Check for valid file extensions
        valid_extensions = ['.pdf', '.doc', '.docx', '.txt']
        file_lower = v.lower()
        if not any(file_lower.endswith(ext) for ext in valid_extensions):
            raise ValueError(f"Tipo de arquivo não suportado. Extensões válidas: {', '.join(valid_extensions)}")
        
        # Remove potentially dangerous characters
        clean_name = re.sub(r'[<>:"/\\|?*]', '', v.strip())
        return clean_name

# =============================================
# CREATE SCHEMA
# =============================================
class CurriculumCreate(CurriculumBase):
    """Schema para criação de currículo"""
    file_base64: Optional[str] = Field(None, description="Arquivo em base64")
    file_path: Optional[str] = Field(None, description="Caminho do arquivo no storage")
    
    @validator('file_base64')
    def validate_file_base64(cls, v):
        """Validate base64 content"""
        if v and len(v) > 50_000_000:  # ~50MB limit
            raise ValueError("Arquivo muito grande (máximo 50MB)")
        return v

# =============================================
# UPDATE SCHEMA
# =============================================
class CurriculumUpdate(BaseModel):
    """Schema para atualização de currículo (campos opcionais)"""
    file_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_work: Optional[bool] = None
    file_base64: Optional[str] = None
    file_path: Optional[str] = None

    @validator('file_name')
    def validate_file_name(cls, v):
        """Validate file name if provided"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Nome do arquivo não pode ser vazio")
            
            # Check for valid file extensions
            valid_extensions = ['.pdf', '.doc', '.docx', '.txt']
            file_lower = v.lower()
            if not any(file_lower.endswith(ext) for ext in valid_extensions):
                raise ValueError(f"Tipo de arquivo não suportado. Extensões válidas: {', '.join(valid_extensions)}")
            
            return re.sub(r'[<>:"/\\|?*]', '', v.strip())
        return v

# =============================================
# RESPONSE SCHEMA
# =============================================
class CurriculumResponse(CurriculumBase):
    """Schema para resposta da API (sem dados do arquivo)"""
    model_config = ConfigDict(from_attributes=True)
    
    curriculum_id: UUID
    created_date: datetime
    updated_date: Optional[datetime] = None
    deleted_date: Optional[datetime] = None
    
    # File info without actual content
    file_size_bytes: Optional[int] = Field(None, description="Tamanho do arquivo em bytes")
    file_type: Optional[FileTypeEnum] = Field(None, description="Tipo do arquivo")
    download_url: Optional[str] = Field(None, description="URL para download")

# =============================================
# DETAIL SCHEMA
# =============================================
class CurriculumDetail(CurriculumResponse):
    """Schema para resposta detalhada com relacionamentos"""
    create_user_id: Optional[UUID] = None
    
    # User information
    user_name: Optional[str] = Field(None, description="Nome do usuário")
    user_email: Optional[str] = Field(None, description="Email do usuário")
    
    # Processing information
    status: CurriculumStatusEnum = Field(CurriculumStatusEnum.PENDING, description="Status do processamento")
    processing_attempts: int = Field(0, description="Tentativas de processamento")
    last_processed_date: Optional[datetime] = Field(None, description="Data do último processamento")
    processing_error: Optional[str] = Field(None, description="Erro no processamento")
    
    # Extracted data summary
    has_extracted_data: bool = Field(False, description="Se possui dados extraídos")
    extraction_confidence: Optional[float] = Field(None, ge=0, le=1, description="Confiança da extração")
    
    # Usage statistics
    download_count: int = Field(0, description="Número de downloads")
    applications_count: int = Field(0, description="Número de candidaturas usando este currículo")
    last_used_date: Optional[datetime] = Field(None, description="Data do último uso")

    @validator('file_type', always=True)
    def extract_file_type(cls, v, values):
        """Extract file type from file name"""
        file_name = values.get('file_name', '')
        if file_name:
            file_lower = file_name.lower()
            if file_lower.endswith('.pdf'):
                return FileTypeEnum.PDF
            elif file_lower.endswith('.doc'):
                return FileTypeEnum.DOC
            elif file_lower.endswith('.docx'):
                return FileTypeEnum.DOCX
            elif file_lower.endswith('.txt'):
                return FileTypeEnum.TXT
        return v

# =============================================
# SUMMARY SCHEMA
# =============================================
class CurriculumSummary(BaseModel):
    """Schema resumido para listagens"""
    model_config = ConfigDict(from_attributes=True)
    
    curriculum_id: UUID
    file_name: str
    file_type: Optional[FileTypeEnum] = None
    file_size_bytes: Optional[int] = None
    is_work: bool
    status: CurriculumStatusEnum
    created_date: datetime
    has_extracted_data: bool = False
    applications_count: int = 0

# =============================================
# SEARCH FILTERS SCHEMA
# =============================================
class CurriculumSearchFilters(BaseModel):
    """Schema para filtros de busca"""
    user_id: Optional[UUID] = Field(None, description="Filtrar por usuário")
    file_name: Optional[str] = Field(None, description="Filtrar por nome do arquivo")
    file_type: Optional[FileTypeEnum] = Field(None, description="Filtrar por tipo de arquivo")
    is_work: Optional[bool] = Field(None, description="Filtrar currículos profissionais")
    status: Optional[CurriculumStatusEnum] = Field(None, description="Filtrar por status")
    has_extracted_data: Optional[bool] = Field(None, description="Filtrar com dados extraídos")
    min_file_size: Optional[int] = Field(None, ge=0, description="Tamanho mínimo do arquivo")
    max_file_size: Optional[int] = Field(None, ge=0, description="Tamanho máximo do arquivo")
    uploaded_after: Optional[datetime] = Field(None, description="Enviados após data")
    uploaded_before: Optional[datetime] = Field(None, description="Enviados antes da data")
    min_applications: Optional[int] = Field(None, ge=0, description="Mínimo de candidaturas")

# =============================================
# FILE UPLOAD SCHEMA
# =============================================
class CurriculumUpload(BaseModel):
    """Schema para upload de currículo"""
    file_data: bytes = Field(..., description="Dados do arquivo")
    file_name: str = Field(..., min_length=1, max_length=255)
    is_work: bool = Field(True, description="Se é currículo profissional")
    
    @validator('file_data')
    def validate_file_size(cls, v):
        """Validate file size"""
        if len(v) > 50_000_000:  # 50MB limit
            raise ValueError("Arquivo muito grande (máximo 50MB)")
        if len(v) < 100:  # Minimum file size
            raise ValueError("Arquivo muito pequeno")
        return v

class CurriculumUploadResponse(BaseModel):
    """Schema para resposta de upload"""
    curriculum_id: UUID
    file_name: str
    file_size_bytes: int
    upload_status: str
    processing_started: bool
    estimated_processing_time_minutes: Optional[int] = None

# =============================================
# EXTRACTION SCHEMAS
# =============================================
class ExtractedPersonalInfo(BaseModel):
    """Schema para informações pessoais extraídas"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    birth_date: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None

class ExtractedExperience(BaseModel):
    """Schema para experiência extraída"""
    job_title: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)

class ExtractedEducation(BaseModel):
    """Schema para educação extraída"""
    degree: Optional[str] = None
    institution: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class CurriculumExtractedData(BaseModel):
    """Schema para todos os dados extraídos do currículo"""
    curriculum_id: UUID
    extraction_date: datetime
    confidence_score: float = Field(..., ge=0, le=1)
    
    personal_info: ExtractedPersonalInfo
    experiences: List[ExtractedExperience] = Field(default_factory=list)
    education: List[ExtractedEducation] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    
    # Raw extracted text
    raw_text: Optional[str] = Field(None, description="Texto bruto extraído")
    
    # Processing metadata
    processing_time_seconds: Optional[float] = None
    llm_model_used: Optional[str] = None
    extraction_errors: List[str] = Field(default_factory=list)

# =============================================
# PROCESSING SCHEMAS
# =============================================
class ProcessingJob(BaseModel):
    """Schema para job de processamento"""
    curriculum_id: UUID
    job_id: UUID
    status: str
    started_at: datetime
    estimated_completion: Optional[datetime] = None
    progress_percentage: int = Field(0, ge=0, le=100)

class BulkProcessingRequest(BaseModel):
    """Schema para processamento em lote"""
    curriculum_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    force_reprocess: bool = Field(False, description="Forçar reprocessamento")
    priority: int = Field(5, ge=1, le=10, description="Prioridade (1=alta)")

class BulkProcessingResponse(BaseModel):
    """Schema para resposta de processamento em lote"""
    total_requested: int
    started_processing: int
    already_processed: int
    failed_to_start: int
    batch_job_id: UUID
    estimated_completion_minutes: Optional[int] = None

# =============================================
# STATISTICS SCHEMA
# =============================================
class CurriculumStatistics(BaseModel):
    """Schema para estatísticas de currículos"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: Optional[UUID] = None
    total_curricula: int = 0
    by_file_type: Dict[FileTypeEnum, int] = Field(default_factory=dict)
    by_status: Dict[CurriculumStatusEnum, int] = Field(default_factory=dict)
    total_file_size_mb: float = 0.0
    avg_file_size_mb: float = 0.0
    total_downloads: int = 0
    total_applications: int = 0
    processing_success_rate: float = 0.0
    avg_processing_time_seconds: Optional[float] = None
    most_recent_upload: Optional[datetime] = None
    upload_trends: Optional[dict] = None  # For charts