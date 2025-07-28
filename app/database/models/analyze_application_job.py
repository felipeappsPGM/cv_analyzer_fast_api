# =============================================
# app/database/models/analyze_application_job.py
# =============================================
from sqlalchemy import Column, Float, Text, DateTime, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import uuid

class AnalyzeApplicationJob(Base):
    __tablename__ = "analyze_application_jobs"
    
    # Primary Key
    analyze_application_job_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # Analysis Scores (based on business rules BR01-BR06)
    academic_score = Column(Float, nullable=True, default=0.0)  # 30% weight
    professional_experience_score = Column(Float, nullable=True, default=0.0)  # 35% weight
    professional_courses_score = Column(Float, nullable=True, default=0.0)  # 20% weight
    weak_points_score = Column(Float, nullable=True, default=0.0)  # -10% weight
    strong_points_score = Column(Float, nullable=True, default=0.0)  # 15% weight
    total_score = Column(Float, nullable=False, default=0.0, index=True)  # Final weighted score
    
    # LLM Generated Opinion
    opinion_application_job = Column(Text, nullable=True)
    
    # Foreign Keys
    professional_profile_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('professional_profiles.professional_profile_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Application job relationship (optional)
    application_job_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('application_jobs.application_job_id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    
    # Audit Fields
    created_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_date = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_date = Column(DateTime(timezone=True), nullable=True)
    create_user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # =============================================
    # RELATIONSHIPS
    # =============================================
    
    # User relationship
    user = relationship("User", back_populates="analyses", lazy="select")
    
    # Professional Profile relationship
    professional_profile = relationship("ProfessionalProfile", back_populates="analyses", lazy="select")
    
    # Application relationship (optional)
    application = relationship("ApplicationJob", back_populates="analysis", lazy="select")
    
    def calculate_total_score(self):
        """
        Calculate total score based on business rules BR01-BR06:
        - Academic: 30%
        - Professional Experience: 35%
        - Professional Courses: 20%
        - Strong Points: +15%
        - Weak Points: -10%
        """
        academic = (self.academic_score or 0) * 0.30
        experience = (self.professional_experience_score or 0) * 0.35
        courses = (self.professional_courses_score or 0) * 0.20
        strong = (self.strong_points_score or 0) * 0.15
        weak = (self.weak_points_score or 0) * 0.10
        
        self.total_score = academic + experience + courses + strong - weak
        return self.total_score
    
    def __repr__(self):
        return f"<AnalyzeApplicationJob(analyze_application_job_id={self.analyze_application_job_id}, total_score={self.total_score})>"