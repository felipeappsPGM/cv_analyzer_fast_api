# =============================================
# app/database/models/company.py
# =============================================
from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import uuid

class Company(Base):
    __tablename__ = "companies"
    
    # Primary Key
    company_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # Basic Info
    company_name = Column(String(255), nullable=False, index=True)
    area_of_activity = Column(String(500), nullable=True)
    cnpj = Column(String(18), unique=True, nullable=False, index=True)
    
    # Foreign Keys
    address_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Audit Fields
    created_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_date = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_date = Column(DateTime(timezone=True), nullable=True)
    create_user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships (will be defined after all models are created)
    # users = relationship("User", back_populates="company", lazy="select")
    # jobs = relationship("Job", back_populates="company", lazy="select") 
    # address = relationship("Address", back_populates="companies", lazy="select")
    
    def __repr__(self):
        return f"<Company(company_id={self.company_id}, company_name='{self.company_name}', cnpj='{self.cnpj}')>"