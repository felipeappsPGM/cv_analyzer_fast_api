# =============================================
# app/schemas/address.py
# =============================================
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum
import re

# =============================================
# ENUMS
# =============================================
class StreetTypeEnum(str, Enum):
    RUA = "Rua"
    AVENIDA = "Avenida"
    ALAMEDA = "Alameda"
    TRAVESSA = "Travessa"
    PRACA = "Praça"
    ESTRADA = "Estrada"
    RODOVIA = "Rodovia"
    LARGO = "Largo"
    VIELA = "Viela"
    OUTRO = "Outro"

class StateEnum(str, Enum):
    AC = "Acre"
    AL = "Alagoas"
    AP = "Amapá"
    AM = "Amazonas"
    BA = "Bahia"
    CE = "Ceará"
    DF = "Distrito Federal"
    ES = "Espírito Santo"
    GO = "Goiás"
    MA = "Maranhão"
    MT = "Mato Grosso"
    MS = "Mato Grosso do Sul"
    MG = "Minas Gerais"
    PA = "Pará"
    PB = "Paraíba"
    PR = "Paraná"
    PE = "Pernambuco"
    PI = "Piauí"
    RJ = "Rio de Janeiro"
    RN = "Rio Grande do Norte"
    RS = "Rio Grande do Sul"
    RO = "Rondônia"
    RR = "Roraima"
    SC = "Santa Catarina"
    SP = "São Paulo"
    SE = "Sergipe"
    TO = "Tocantins"

# =============================================
# BASE SCHEMA
# =============================================
class AddressBase(BaseModel):
    street_type: Optional[StreetTypeEnum] = Field(None, description="Tipo do logradouro")
    street_name: str = Field(..., min_length=1, max_length=255, description="Nome da rua/logradouro")
    number: Optional[str] = Field(None, max_length=20, description="Número")
    cep: Optional[str] = Field(None, max_length=10, description="CEP")
    neighborhood: Optional[str] = Field(None, max_length=100, description="Bairro")
    cidade: Optional[str] = Field(None, max_length=100, description="Cidade (campo original)")
    city: Optional[str] = Field(None, max_length=100, description="Cidade (campo alternativo)")
    state: Optional[str] = Field(None, max_length=100, description="Estado")
    country: str = Field("Brasil", max_length=100, description="País")
    
    # Optional foreign keys
    company_id: Optional[UUID] = Field(None, description="ID da empresa (se endereço da empresa)")
    user_id: Optional[UUID] = Field(None, description="ID do usuário (se endereço pessoal)")

    @validator('street_name')
    def validate_street_name(cls, v):
        """Validate street name"""
        if not v or not v.strip():
            raise ValueError("Nome da rua é obrigatório")
        return v.strip()

    @validator('cep')
    def validate_cep(cls, v):
        """Validate CEP format"""
        if v is None:
            return v
        
        # Remove non-digit characters
        cep_digits = re.sub(r'\D', '', v)
        
        if len(cep_digits) != 8:
            raise ValueError("CEP deve conter 8 dígitos")
        
        # Format as XXXXX-XXX
        return f"{cep_digits[:5]}-{cep_digits[5:]}"

    @validator('number')
    def validate_number(cls, v):
        """Validate address number"""
        if v is not None:
            v = v.strip()
            if v.lower() in ['s/n', 'sn', 'sem numero', 'sem número']:
                return 'S/N'
        return v

    @validator('cidade', 'city', 'neighborhood')
    def validate_text_fields(cls, v):
        """Validate text fields"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    @validator('country')
    def validate_country(cls, v):
        """Validate and set default country"""
        if not v or not v.strip():
            return "Brasil"
        return v.strip()

# =============================================
# CREATE SCHEMA
# =============================================
class AddressCreate(AddressBase):
    """Schema para criação de endereço"""
    
    @validator('user_id', 'company_id')
    def validate_owner(cls, v, values, field):
        """Validate that address belongs to either user or company, not both"""
        user_id = values.get('user_id')
        company_id = values.get('company_id')
        
        if user_id and company_id:
            raise ValueError("Endereço deve pertencer a usuário OU empresa, não ambos")
        
        if not user_id and not company_id:
            raise ValueError("Endereço deve pertencer a um usuário ou empresa")
            
        return v

# =============================================
# UPDATE SCHEMA
# =============================================
class AddressUpdate(BaseModel):
    """Schema para atualização de endereço (campos opcionais)"""
    street_type: Optional[StreetTypeEnum] = None
    street_name: Optional[str] = Field(None, min_length=1, max_length=255)
    number: Optional[str] = Field(None, max_length=20)
    cep: Optional[str] = Field(None, max_length=10)
    neighborhood: Optional[str] = Field(None, max_length=100)
    cidade: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)

    @validator('street_name')
    def validate_street_name(cls, v):
        """Validate street name if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Nome da rua não pode ser vazio")
        return v.strip() if v else v

    @validator('cep')
    def validate_cep(cls, v):
        """Validate CEP format if provided"""
        if v is None:
            return v
        
        # Remove non-digit characters
        cep_digits = re.sub(r'\D', '', v)
        
        if len(cep_digits) != 8:
            raise ValueError("CEP deve conter 8 dígitos")
        
        # Format as XXXXX-XXX
        return f"{cep_digits[:5]}-{cep_digits[5:]}"

# =============================================
# RESPONSE SCHEMA
# =============================================
class AddressResponse(AddressBase):
    """Schema para resposta da API"""
    model_config = ConfigDict(from_attributes=True)
    
    address_id: UUID
    created_date: datetime
    updated_date: Optional[datetime] = None
    deleted_date: Optional[datetime] = None

# =============================================
# DETAIL SCHEMA
# =============================================
class AddressDetail(AddressResponse):
    """Schema para resposta detalhada com relacionamentos"""
    create_user_id: Optional[UUID] = None
    
    # Calculated fields
    full_address: Optional[str] = Field(None, description="Endereço completo formatado")
    coordinates: Optional[dict] = Field(None, description="Coordenadas geográficas (lat, lng)")
    
    # Related entity information
    owner_name: Optional[str] = Field(None, description="Nome do proprietário (usuário ou empresa)")
    owner_type: Optional[str] = Field(None, description="Tipo do proprietário (user|company)")
    
    # Address validation
    is_validated: bool = Field(False, description="Se o endereço foi validado")
    validation_source: Optional[str] = Field(None, description="Fonte da validação")
    validation_date: Optional[datetime] = Field(None, description="Data da validação")

    @validator('full_address', always=True)
    def calculate_full_address(cls, v, values):
        """Calculate full formatted address"""
        parts = []
        
        # Street type + name
        street_type = values.get('street_type')
        street_name = values.get('street_name')
        if street_type and street_name:
            parts.append(f"{street_type} {street_name}")
        elif street_name:
            parts.append(street_name)
        
        # Number
        number = values.get('number')
        if number:
            parts.append(number)
        
        # Neighborhood
        neighborhood = values.get('neighborhood')
        if neighborhood:
            parts.append(neighborhood)
        
        # City (prefer 'cidade' over 'city')
        cidade = values.get('cidade') or values.get('city')
        if cidade:
            parts.append(cidade)
        
        # State
        state = values.get('state')
        if state:
            parts.append(state)
        
        # Country
        country = values.get('country')
        if country and country != "Brasil":
            parts.append(country)
        
        # CEP
        cep = values.get('cep')
        if cep:
            parts.append(f"CEP: {cep}")
        
        return ", ".join(parts) if parts else None

    @validator('owner_type', always=True)
    def determine_owner_type(cls, v, values):
        """Determine owner type based on foreign keys"""
        if values.get('user_id'):
            return "user"
        elif values.get('company_id'):
            return "company"
        return None

# =============================================
# SUMMARY SCHEMA
# =============================================
class AddressSummary(BaseModel):
    """Schema resumido para listagens"""
    model_config = ConfigDict(from_attributes=True)
    
    address_id: UUID
    street_name: str
    number: Optional[str] = None
    neighborhood: Optional[str] = None
    cidade: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    cep: Optional[str] = None
    full_address: Optional[str] = None
    owner_type: Optional[str] = None

# =============================================
# SEARCH FILTERS SCHEMA
# =============================================
class AddressSearchFilters(BaseModel):
    """Schema para filtros de busca"""
    user_id: Optional[UUID] = Field(None, description="Filtrar por usuário")
    company_id: Optional[UUID] = Field(None, description="Filtrar por empresa")
    street_name: Optional[str] = Field(None, description="Filtrar por nome da rua")
    neighborhood: Optional[str] = Field(None, description="Filtrar por bairro")
    city: Optional[str] = Field(None, description="Filtrar por cidade")
    state: Optional[str] = Field(None, description="Filtrar por estado")
    cep: Optional[str] = Field(None, description="Filtrar por CEP")
    country: Optional[str] = Field(None, description="Filtrar por país")
    street_type: Optional[StreetTypeEnum] = Field(None, description="Filtrar por tipo de logradouro")
    is_validated: Optional[bool] = Field(None, description="Filtrar endereços validados")
    owner_type: Optional[str] = Field(None, regex="^(user|company)$", description="Filtrar por tipo de proprietário")

# =============================================
# VALIDATION SCHEMAS
# =============================================
class AddressValidationRequest(BaseModel):
    """Schema para solicitação de validação de endereço"""
    address_id: UUID
    force_revalidation: bool = Field(False, description="Forçar revalidação")

class AddressValidationResponse(BaseModel):
    """Schema para resposta de validação"""
    address_id: UUID
    is_valid: bool
    validation_source: str
    validation_date: datetime
    suggested_corrections: Optional[dict] = None
    coordinates: Optional[dict] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)

class BulkAddressValidation(BaseModel):
    """Schema para validação em lote"""
    address_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    force_revalidation: bool = Field(False)

# =============================================
# CEP LOOKUP SCHEMAS
# =============================================
class CepLookupRequest(BaseModel):
    """Schema para consulta de CEP"""
    cep: str = Field(..., regex=r'^\d{5}-?\d{3}$', description="CEP no formato XXXXX-XXX ou XXXXXXXX")

class CepLookupResponse(BaseModel):
    """Schema para resposta de consulta de CEP"""
    cep: str
    street_name: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = None
    ddd: Optional[str] = None
    provider: str
    found: bool

# =============================================
# STATISTICS SCHEMA
# =============================================
class AddressStatistics(BaseModel):
    """Schema para estatísticas de endereços"""
    model_config = ConfigDict(from_attributes=True)
    
    total_addresses: int = 0
    user_addresses: int = 0
    company_addresses: int = 0
    validated_addresses: int = 0
    by_state: dict = Field(default_factory=dict)
    by_city: dict = Field(default_factory=dict)
    most_common_neighborhoods: List[dict] = Field(default_factory=list)
    validation_rate: float = 0.0
    top_states: List[dict] = Field(default_factory=list)
    top_cities: List[dict] = Field(default_factory=list)

# =============================================
# GEOLOCATION SCHEMAS
# =============================================
class Coordinates(BaseModel):
    """Schema para coordenadas geográficas"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy_meters: Optional[float] = None
    source: Optional[str] = None

class NearbyAddressesRequest(BaseModel):
    """Schema para busca de endereços próximos"""
    coordinates: Coordinates
    radius_km: float = Field(10, ge=0.1, le=100, description="Raio de busca em km")
    limit: int = Field(50, ge=1, le=1000, description="Limite de resultados")

class AddressWithDistance(AddressSummary):
    """Schema para endereço com distância"""
    distance_km: Optional[float] = None
    coordinates: Optional[Coordinates] = None