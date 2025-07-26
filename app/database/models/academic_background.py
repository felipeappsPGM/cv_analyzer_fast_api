# =============================================
# app/database/models/academic_background.py
# =============================================
from sqlalchemy import Column, String, Date, DateTime, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import uuid

class AcademicBackground(Base):
    __tablename__ = "academic_backgrounds"
    
    # Primary Key
    academic_background_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # Academic Info
    degree_name = Column(String(255), nullable=False)
    degree_type = Column(String(100), nullable=False)  # Graduação, Pós, Mestrado, Doutorado, etc.
    field_of_study = Column(String(255), nullable=False)
    institution_name = Column(String(255), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    
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
    # user = relationship("User", back_populates="academic_backgrounds", lazy="select")
    
    def __repr__(self):
        return f"<AcademicBackground(academic_background_id={self.academic_background_id}, degree='{self.degree_name}', institution='{self.institution_name}')>"