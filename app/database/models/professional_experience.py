# =============================================
# app/database/models/professional_experience.py
# =============================================
from sqlalchemy import Column, String, Date, DateTime, Boolean, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import uuid

class ProfessionalExperience(Base):
    __tablename__ = "professional_experiences"
    
    # Primary Key
    professional_experience_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # Professional Experience Info
    job_title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False, index=True)
    employment_type = Column(String(100), nullable=True)  # CLT, PJ, Estágio, etc.
    location = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)
    
    # Foreign Keys
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
    
    # Relationships (will be defined after all models are created)
    # user = relationship("User", back_populates="professional_experiences", lazy="select")
    
    def __repr__(self):
        return f"<ProfessionalExperience(professional_experience_id={self.professional_experience_id}, job_title='{self.job_title}', company='{self.company_name}')>"