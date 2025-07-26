# =============================================
# app/database/models/address.py
# =============================================
from sqlalchemy import Column, String, DateTime, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import uuid

class Address(Base):
    __tablename__ = "addresses"
    
    # Primary Key
    address_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # Address Info
    street_type = Column(String(50), nullable=True)  # Rua, Avenida, etc.
    street_name = Column(String(255), nullable=False)
    number = Column(String(20), nullable=True)
    cep = Column(String(10), nullable=True, index=True)
    neighborhood = Column(String(100), nullable=True)
    cidade = Column(String(100), nullable=True)  # Keeping original field name from DER
    city = Column(String(100), nullable=True)  # Alternative city field
    state = Column(String(100), nullable=True, index=True)
    country = Column(String(100), nullable=False, default='Brasil')
    
    # Foreign Keys (Optional - address can belong to company or user)
    company_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('companies.company_id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    
    # Audit Fields
    created_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_date = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_date = Column(DateTime(timezone=True), nullable=True)
    create_user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships (will be defined after all models are created)
    # company = relationship("Company", back_populates="addresses", lazy="select")
    # user = relationship("User", back_populates="addresses", lazy="select")
    
    @property
    def full_address(self):
        """Return formatted full address"""
        parts = [
            f"{self.street_type} {self.street_name}" if self.street_type else self.street_name,
            self.number,
            self.neighborhood,
            self.cidade or self.city,
            self.state,
            self.country
        ]
        return ", ".join([part for part in parts if part])
    
    def __repr__(self):
        return f"<Address(address_id={self.address_id}, street='{self.street_name}', city='{self.cidade or self.city}')>"