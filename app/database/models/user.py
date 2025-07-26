# =============================================
# app/database/models/user.py (UPDATED WITH RELATIONSHIPS)
# =============================================
from sqlalchemy import Column, String, Boolean, Date, DateTime, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    # Primary Key
    user_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # Basic Info
    user_name = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    user_email = Column(String(255), unique=True, nullable=False, index=True)
    is_work = Column(Boolean, default=False)
    user_type = Column(String(255), nullable=False, index=True)
    
    # Foreign Keys (UUIDs para outras tabelas)
    professional_profile_id = Column(UUID(as_uuid=True), nullable=True)
    professional_experience_id = Column(UUID(as_uuid=True), nullable=True)
    professional_courses_id = Column(UUID(as_uuid=True), nullable=True)
    academic_background_id = Column(UUID(as_uuid=True), nullable=True)
    analyze_application_job_id = Column(UUID(as_uuid=True), nullable=True)
    curriculum_id = Column(UUID(as_uuid=True), nullable=True)
    address_id = Column(UUID(as_uuid=True), nullable=True)
    company_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('companies.company_id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Dates
    birth_day = Column(Date, nullable=True)
    created_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_date = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_date = Column(DateTime(timezone=True), nullable=True)
    
    # Audit
    create_user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # =============================================
    # RELATIONSHIPS
    # =============================================
    
    # Company relationship
    company = relationship("Company", back_populates="users", lazy="select")
    
    # Professional data relationships (one-to-many)
    professional_profiles = relationship(
        "ProfessionalProfile", 
        back_populates="user", 
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    professional_experiences = relationship(
        "ProfessionalExperience", 
        back_populates="user", 
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    academic_backgrounds = relationship(
        "AcademicBackground", 
        back_populates="user", 
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    professional_courses = relationship(
        "ProfessionalCourses", 
        back_populates="user", 
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    curricula = relationship(
        "Curriculum", 
        back_populates="user", 
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    # Application and analysis relationships
    applications = relationship(
        "ApplicationJob", 
        back_populates="user", 
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    analyses = relationship(
        "AnalyzeApplicationJob", 
        back_populates="user", 
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    # Address relationship
    addresses = relationship(
        "Address", 
        back_populates="user", 
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, user_name='{self.user_name}', user_email='{self.user_email}')>"