# =============================================
# app/database/models/application_job.py
# =============================================
from sqlalchemy import Column, DateTime, text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import uuid

class ApplicationJob(Base):
    __tablename__ = "application_jobs"
    
    # Primary Key
    application_job_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # Foreign Keys
    professional_profile_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('professional_profiles.professional_profile_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    job_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('jobs.job_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Audit Fields
    created_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_date = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_date = Column(DateTime(timezone=True), nullable=True)
    create_user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'job_id', name='uq_user_job_application'),
    )
    
    # Relationships (will be defined after all models are created)
    # user = relationship("User", back_populates="applications", lazy="select")
    # job = relationship("Job", back_populates="applications", lazy="select")
    # professional_profile = relationship("ProfessionalProfile", back_populates="applications", lazy="select")
    # analysis = relationship("AnalyzeApplicationJob", back_populates="application", uselist=False, lazy="select")
    
    def __repr__(self):
        return f"<ApplicationJob(application_job_id={self.application_job_id}, user_id={self.user_id}, job_id={self.job_id})>"