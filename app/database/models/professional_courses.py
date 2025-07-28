# =============================================
# app/database/models/professional_courses.py
# =============================================
from sqlalchemy import Column, String, Date, DateTime, Integer, LargeBinary, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import uuid

class ProfessionalCourses(Base):
    __tablename__ = "professional_courses"
    
    # Primary Key
    professional_courses_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # Course Info
    course_name = Column(String(255), nullable=False)
    institution_name = Column(String(255), nullable=False, index=True)
    token_id = Column(String(255), nullable=True)  # ID do certificado/token
    duration_time_hours = Column(Integer, nullable=True)
    
    # Certification Media
    certification_media_pdf = Column(LargeBinary, nullable=True)
    certification_media_image = Column(LargeBinary, nullable=True)
    
    # Dates
    start_date = Column(Date, nullable=True)
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
    
    # =============================================
    # RELATIONSHIPS
    # =============================================
    
    # User relationship
    user = relationship("User", back_populates="professional_courses", lazy="select")
    
    def __repr__(self):
        return f"<ProfessionalCourses(professional_courses_id={self.professional_courses_id}, course='{self.course_name}', institution='{self.institution_name}')>"