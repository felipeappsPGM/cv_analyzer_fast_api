# =============================================
# app/database/models/curriculum.py
# =============================================
from sqlalchemy import Column, String, Text, Boolean, DateTime, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import uuid

class Curriculum(Base):
    __tablename__ = "curricula"
    
    # Primary Key
    curriculum_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # File Info
    file_base64 = Column(Text, nullable=True)  # Base64 encoded file
    file_path = Column(String(500), nullable=True)  # Path to file storage
    file_name = Column(String(255), unique=True, nullable=False, index=True)
    is_work = Column(Boolean, default=True, nullable=False)
    
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
    # user = relationship("User", back_populates="curricula", lazy="select")
    
    def __repr__(self):
        return f"<Curriculum(curriculum_id={self.curriculum_id}, file_name='{self.file_name}', user_id={self.user_id})>"