# =============================================
# app/database/models/job.py
# =============================================
from sqlalchemy import Column, String, Text, DateTime, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import uuid

class Job(Base):
    __tablename__ = "jobs"
    
    # Primary Key
    job_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # Basic Info
    job_name = Column(String(255), nullable=False, index=True)
    activities = Column(Text, nullable=True)
    pre_requisites = Column(Text, nullable=True)
    differentials = Column(Text, nullable=True)
    code_vacancy_job = Column(String(50), unique=True, nullable=False, index=True)
    
    # Foreign Keys
    company_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('companies.company_id', ondelete='CASCADE'),
        nullable=False,
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
    
    # Company relationship
    company = relationship("Company", back_populates="jobs", lazy="select")
    
    # Applications relationship
    applications = relationship("ApplicationJob", back_populates="job", lazy="select", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Job(job_id={self.job_id}, job_name='{self.job_name}', code_vacancy_job='{self.code_vacancy_job}')>"