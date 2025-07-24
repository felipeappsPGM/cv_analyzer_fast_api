# =============================================
# app/schemas/user.py
# =============================================
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import date, datetime
from uuid import UUID

# Base Schema
class UserBase(BaseModel):
    user_name: str = Field(..., min_length=1, max_length=255)
    user_email: EmailStr
    is_work: bool = False
    user_type: str = Field(..., min_length=1, max_length=255)
    birth_day: Optional[date] = None

# Schema para criação
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=255)
    
# Schema para atualização
class UserUpdate(BaseModel):
    user_name: Optional[str] = Field(None, min_length=1, max_length=255)
    user_email: Optional[EmailStr] = None
    is_work: Optional[bool] = None
    user_type: Optional[str] = Field(None, min_length=1, max_length=255)
    birth_day: Optional[date] = None

# Schema para resposta (sem senha)
class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: UUID
    created_date: datetime
    update_date: Optional[datetime] = None
    deleted_date: Optional[datetime] = None

# Schema para resposta com relacionamentos
class UserDetail(UserResponse):
    professional_profile_id: Optional[UUID] = None
    professional_experience_id: Optional[UUID] = None
    professional_courses_id: Optional[UUID] = None
    academic_background_id: Optional[UUID] = None
    analyze_application_job_id: Optional[UUID] = None
    curriculum_id: Optional[UUID] = None
    address_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    create_user_id: Optional[UUID] = None