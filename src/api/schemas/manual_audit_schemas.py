"""
Manual Audit API Schemas
=========================
Pydantic models for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class ManualAuditCreate(BaseModel):
    """Schema for creating a new manual audit"""

    # Dealer Information
    dealer_id: str = Field(..., min_length=1, max_length=100, description="Unique dealer identifier")
    dealer_name: str = Field(..., min_length=1, max_length=255, description="Dealer name")
    dealer_details: Optional[str] = Field(None, description="Additional dealer information")
    dealer_consolidated_summary: Optional[str] = Field(None, description="Overall audit summary")

    # Date & Time
    date: str = Field(..., description="Audit date (YYYY-MM-DD format)")
    month: str = Field(..., max_length=50, description="Month name")
    time: str = Field(..., description="Audit time (ISO 8601 format)")
    shift: str = Field(..., max_length=50, description="Shift (Morning/Evening/Night)")

    # Audit Details
    compliance_status: str = Field(..., max_length=50, description="Compliance status")
    level_1: str = Field(..., max_length=100, description="Level 1 category", alias="level_1")
    sub_category: str = Field(..., max_length=100, description="Sub-category")
    checkpoint: str = Field(..., max_length=255, description="Checkpoint name")

    # Media & Confidence
    photo_url: Optional[str] = Field(None, max_length=500, description="Photo URL if available")
    confidence_level: float = Field(..., ge=0, le=100, description="Confidence level (0-100)")

    # Feedback
    feedback: str = Field(..., min_length=1, description="Audit feedback/notes")

    # Location
    language: str = Field(..., max_length=50, description="Language")
    country: str = Field(..., max_length=100, description="Country")
    zone: str = Field(..., max_length=100, description="Zone/Region")

    # Credentials (for audit trail only)
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=1, description="Password (stored for audit trail)")

    class Config:
        json_schema_extra = {
            "example": {
                "dealer_id": "DEALER001",
                "dealer_name": "Downtown Stellantis Showroom",
                "dealer_details": "Premium dealership location",
                "dealer_consolidated_summary": "All checkpoints passed with excellent hygiene standards",
                "date": "2026-02-10",
                "month": "February",
                "time": "2026-02-10T14:30:00",
                "shift": "Morning Shift",
                "compliance_status": "Compliant",
                "level_1": "Level 1 - Critical",
                "sub_category": "Cleanliness",
                "checkpoint": "Surface Sanitation",
                "photo_url": "https://example.com/photo.jpg",
                "confidence_level": 95.5,
                "feedback": "Excellent hygiene maintained across all checkpoints",
                "language": "English",
                "country": "India",
                "zone": "North Zone",
                "email": "dealer@stellantis.com",
                "password": "secure123"
            }
        }


class ManualAuditResponse(BaseModel):
    """Schema for manual audit response"""

    id: int
    dealer_id: str
    dealer_name: str
    dealer_details: Optional[str]
    dealer_consolidated_summary: Optional[str]
    date: str
    month: str
    time: str
    shift: str
    compliance_status: str
    level_1: str
    sub_category: str
    checkpoint: str
    photo_url: Optional[str]
    confidence_level: float
    feedback: str
    language: str
    country: str
    zone: str
    email: str
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class ManualAuditListResponse(BaseModel):
    """Schema for listing manual audits"""
    total: int
    audits: list[ManualAuditResponse]


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    timestamp: str

