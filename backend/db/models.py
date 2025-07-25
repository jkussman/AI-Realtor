"""
Database models for the AI Realtor application.
"""

from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float, Index, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Building(Base):
    """Model for residential apartment buildings."""
    
    __tablename__ = "buildings"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(String, unique=True, index=True, nullable=False)
    standardized_address = Column(String, unique=True, index=True, nullable=True)
    latitude = Column(String, nullable=True)
    longitude = Column(String, nullable=True)
    building_type = Column(String, nullable=False)
    bounding_box = Column(JSON, nullable=True)
    approved = Column(Boolean, default=False)
    contact_email = Column(String, nullable=True)
    contact_name = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    email_sent = Column(Boolean, default=False)
    reply_received = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Contact confidence scores
    contact_email_confidence = Column(Integer, default=0)
    contact_source = Column(String, nullable=True)
    contact_source_url = Column(String, nullable=True)
    contact_verified = Column(Boolean, default=False)
    contact_last_verified = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)
    verification_flags = Column(JSON, nullable=True)
    
    # Basic building info
    property_manager = Column(String, nullable=True)
    number_of_units = Column(Integer, nullable=True)
    year_built = Column(Integer, nullable=True)
    square_footage = Column(Integer, nullable=True)
    
    # Detailed rental information
    is_coop = Column(Boolean, default=False)
    is_mixed_use = Column(Boolean, default=False)
    total_apartments = Column(Integer, nullable=True)
    two_bedroom_apartments = Column(Integer, nullable=True)
    recent_2br_rent = Column(Integer, nullable=True)
    rent_range_2br = Column(String, nullable=True)
    has_laundry = Column(Boolean, default=False)
    laundry_type = Column(String, nullable=True)
    amenities = Column(JSON, nullable=True)
    pet_policy = Column(String, nullable=True)
    building_style = Column(String, nullable=True)
    management_company = Column(String, nullable=True)
    contact_info = Column(JSON, nullable=True)  # Changed from String to JSON
    recent_availability = Column(Boolean, default=False)
    rental_notes = Column(Text, nullable=True)
    neighborhood = Column(String, nullable=True)
    stories = Column(Integer, nullable=True)
    
    # Relationship to email logs
    email_logs = relationship("EmailLog", back_populates="building")
    
    __table_args__ = (
        # Create a unique index on name, but only if name is not null and not empty
        Index('ix_buildings_name_unique', 
              name, 
              unique=True, 
              postgresql_where=and_(name != None, name != "")),
    )


class EmailLog(Base):
    """Model for tracking email communications."""
    
    __tablename__ = "email_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="sent")  # sent, delivered, opened, replied, bounced
    opened = Column(Boolean, default=False)
    replied = Column(Boolean, default=False)
    reply_content = Column(Text, nullable=True)
    reply_received_at = Column(DateTime, nullable=True)
    
    # Gmail specific fields
    gmail_message_id = Column(String, nullable=True)
    gmail_thread_id = Column(String, nullable=True)
    
    # Relationship to building
    building = relationship("Building", back_populates="email_logs")


class ContactSource(Base):
    """Model for tracking where contact information was found."""
    
    __tablename__ = "contact_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False)
    source_type = Column(String, nullable=False)  # web_search, api, manual
    source_url = Column(String, nullable=True)
    confidence_score = Column(Integer, default=0)  # 0-100
    extracted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to building
    building = relationship("Building") 