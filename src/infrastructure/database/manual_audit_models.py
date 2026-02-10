"""
Manual Audit Database Models
=============================
SQLAlchemy models for manual audit data storage in PostgreSQL
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ManualAudit(Base):
    """
    Manual Audit database model

    Stores comprehensive audit data submitted from Flutter mobile app
    """
    __tablename__ = 'manual_audits'

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Dealer Information
    dealer_id = Column(String(100), nullable=False, index=True)
    dealer_name = Column(String(255), nullable=False)
    dealer_details = Column(Text, nullable=True)
    dealer_consolidated_summary = Column(Text, nullable=True)

    # Date & Time
    date = Column(DateTime, nullable=False, index=True)
    month = Column(String(50), nullable=False)
    time = Column(DateTime, nullable=False)
    shift = Column(String(50), nullable=False)

    # Audit Details
    compliance_status = Column(String(50), nullable=False)
    level_1 = Column(String(100), nullable=False)
    sub_category = Column(String(100), nullable=False)
    checkpoint = Column(String(255), nullable=False)

    # Media & Confidence
    photo_url = Column(String(500), nullable=True)
    confidence_level = Column(Float, nullable=False)

    # Feedback
    feedback = Column(Text, nullable=False)

    # Location
    language = Column(String(50), nullable=False)
    country = Column(String(100), nullable=False)
    zone = Column(String(100), nullable=False)

    # Credentials (stored for audit trail only - NOT for authentication)
    email = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)  # Note: In production, hash this!

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ManualAudit(id={self.id}, dealer_id='{self.dealer_id}', date='{self.date}')>"

    def to_dict(self):
        """Convert model to dictionary for JSON response"""
        return {
            'id': self.id,
            'dealer_id': self.dealer_id,
            'dealer_name': self.dealer_name,
            'dealer_details': self.dealer_details,
            'dealer_consolidated_summary': self.dealer_consolidated_summary,
            'date': self.date.isoformat() if self.date else None,
            'month': self.month,
            'time': self.time.isoformat() if self.time else None,
            'shift': self.shift,
            'compliance_status': self.compliance_status,
            'level_1': self.level_1,
            'sub_category': self.sub_category,
            'checkpoint': self.checkpoint,
            'photo_url': self.photo_url,
            'confidence_level': self.confidence_level,
            'feedback': self.feedback,
            'language': self.language,
            'country': self.country,
            'zone': self.zone,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

