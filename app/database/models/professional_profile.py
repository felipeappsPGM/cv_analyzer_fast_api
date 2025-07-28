# =============================================
# app/database/models/professional_profile.py
# =============================================
from sqlalchemy import Column, String, Text, DateTime, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import uuid

class ProfessionalProfile(Base):
    __tablename__ = "professional_profiles"
    
    # Primary Key
    professional_profile_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # Basic Info
    professional_profile_name = Column(String(255), nullable=False)
    professional_profile_description = Column(Text, nullable=True)
    
    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    academic_background_id = Column(UUID(as_uuid=True), nullable=True)
    professional_experience_id = Column(UUID(as_uuid=True), nullable=True)
    professional_courses_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Audit Fields
    created_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_date = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_date = Column(DateTime(timezone=True), nullable=True)
    create_user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # =============================================
    # RELATIONSHIPS
    # =============================================
    
    # User relationship
    user = relationship("User", back_populates="professional_profiles", lazy="select")
    
    # Application relationship
    applications = relationship("ApplicationJob", back_populates="professional_profile", lazy="select", cascade="all, delete-orphan")
    
    # Analysis relationship
    analyses = relationship("AnalyzeApplicationJob", back_populates="professional_profile", lazy="select", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ProfessionalProfile(professional_profile_id={self.professional_profile_id}, name='{self.professional_profile_name}')>"