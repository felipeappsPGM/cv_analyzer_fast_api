# =============================================
# app/schemas/company.py
# =============================================
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import re

# =============================================
# BASE SCHEMA
# =============================================
class CompanyBase(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255, description="Nome da empresa")
    area_of_activity: Optional[str] = Field(None, max_length=500, description="Área de atividade da empresa")
    cnpj: str = Field(..., min_length=14, max_length=18, description="CNPJ da empresa")
    address_id: Optional[UUID] = Field(None, description="ID do endereço")

    @validator('cnpj')
    def validate_cnpj(cls, v):
        """Validate CNPJ format"""
        if not v:
            raise ValueError("CNPJ é obrigatório")
        
        # Remove non-digit characters
        cnpj_digits = re.sub(r'\D', '', v)
        
        if len(cnpj_digits) != 14:
            raise ValueError("CNPJ deve conter 14 dígitos")
        
        # Basic CNPJ validation (simplified)
        if cnpj_digits == cnpj_digits[0] * 14:
            raise ValueError("CNPJ inválido")
            
        return cnpj_digits

    @validator('company_name')
    def validate_company_name(cls, v):
        """Validate company name"""
        if not v or not v.strip():
            raise ValueError("Nome da empresa é obrigatório")
        return v.strip()

# =============================================
# CREATE SCHEMA
# =============================================
class CompanyCreate(CompanyBase):
    """Schema para criação de empresa"""
    pass

# =============================================
# UPDATE SCHEMA
# =============================================
class CompanyUpdate(BaseModel):
    """Schema para atualização de empresa (campos opcionais)"""
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    area_of_activity: Optional[str] = Field(None, max_length=500)
    cnpj: Optional[str] = Field(None, min_length=14, max_length=18)
    address_id: Optional[UUID] = None

    @validator('cnpj')
    def validate_cnpj(cls, v):
        """Validate CNPJ format if provided"""
        if v is None:
            return v
            
        # Remove non-digit characters
        cnpj_digits = re.sub(r'\D', '', v)
        
        if len(cnpj_digits) != 14:
            raise ValueError("CNPJ deve conter 14 dígitos")
        
        return cnpj_digits

    @validator('company_name')
    def validate_company_name(cls, v):
        """Validate company name if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Nome da empresa não pode ser vazio")
        return v.strip() if v else v

# =============================================
# RESPONSE SCHEMA
# =============================================
class CompanyResponse(CompanyBase):
    """Schema para resposta da API (sem dados sensíveis)"""
    model_config = ConfigDict(from_attributes=True)
    
    company_id: UUID
    created_date: datetime
    updated_date: Optional[datetime] = None
    deleted_date: Optional[datetime] = None

# =============================================
# DETAIL SCHEMA
# =============================================
class CompanyDetail(CompanyResponse):
    """Schema para resposta detalhada com relacionamentos"""
    create_user_id: Optional[UUID] = None
    
    # Related data (will be populated by service layer)
    total_jobs: Optional[int] = Field(None, description="Total de vagas da empresa")
    active_jobs: Optional[int] = Field(None, description="Vagas ativas")
    total_users: Optional[int] = Field(None, description="Total de usuários vinculados")

# =============================================
# SUMMARY SCHEMA
# =============================================
class CompanySummary(BaseModel):
    """Schema resumido para listagens"""
    model_config = ConfigDict(from_attributes=True)
    
    company_id: UUID
    company_name: str
    area_of_activity: Optional[str] = None
    cnpj: str
    created_date: datetime

# =============================================
# SEARCH FILTERS SCHEMA
# =============================================
class CompanySearchFilters(BaseModel):
    """Schema para filtros de busca"""
    company_name: Optional[str] = Field(None, description="Filtrar por nome da empresa")
    area_of_activity: Optional[str] = Field(None, description="Filtrar por área de atividade")
    cnpj: Optional[str] = Field(None, description="Filtrar por CNPJ")
    has_active_jobs: Optional[bool] = Field(None, description="Filtrar empresas com vagas ativas")
    created_after: Optional[datetime] = Field(None, description="Filtrar por data de criação")
    created_before: Optional[datetime] = Field(None, description="Filtrar por data de criação")

# =============================================
# STATISTICS SCHEMA
# =============================================
class CompanyStatistics(BaseModel):
    """Schema para estatísticas da empresa"""
    model_config = ConfigDict(from_attributes=True)
    
    company_id: UUID
    total_jobs: int = 0
    active_jobs: int = 0
    closed_jobs: int = 0
    total_applications: int = 0
    total_users: int = 0
    avg_applications_per_job: float = 0.0
    most_applied_job: Optional[str] = None