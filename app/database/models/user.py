# =============================================
# app/database/models/user.py
# =============================================
from sqlalchemy import Column, String, Boolean, Date, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.config.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    # Primary Key
    user_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    
    # Basic Info
    user_name = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    user_email = Column(String(255), unique=True, nullable=False)
    is_work = Column(Boolean, default=False)
    user_type = Column(String(255), nullable=False)
    
    # Foreign Keys (UUIDs para outras tabelas)
    professional_profile_id = Column(UUID(as_uuid=True), nullable=True)
    professional_experience_id = Column(UUID(as_uuid=True), nullable=True)
    professional_courses_id = Column(UUID(as_uuid=True), nullable=True)
    academic_background_id = Column(UUID(as_uuid=True), nullable=True)
    analyze_application_job_id = Column(UUID(as_uuid=True), nullable=True)
    curriculum_id = Column(UUID(as_uuid=True), nullable=True)
    address_id = Column(UUID(as_uuid=True), nullable=True)
    company_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Dates
    birth_day = Column(Date, nullable=True)
    created_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    update_date = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_date = Column(DateTime(timezone=True), nullable=True)
    
    # Audit
    create_user_id = Column(UUID(as_uuid=True), nullable=True)