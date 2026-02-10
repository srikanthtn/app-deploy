"""
Manager Portal API Schemas
===========================
Pydantic models for Manager Portal aggregated data responses
"""

from pydantic import BaseModel
from typing import List
from datetime import datetime


class FacilityComplianceData(BaseModel):
    """Facility-level compliance data for Manager Portal"""
    facility_id: str
    facility_name: str
    compliance_percentage: float
    total_audits: int
    completed_audits: int
    pending_audits: int
    last_audit_date: str
    zone: str

    class Config:
        json_schema_extra = {
            "example": {
                "facility_id": "DEALER001",
                "facility_name": "Downtown Stellantis Showroom",
                "compliance_percentage": 92.5,
                "total_audits": 20,
                "completed_audits": 18,
                "pending_audits": 2,
                "last_audit_date": "2026-02-10T14:30:00",
                "zone": "North Zone"
            }
        }


class ZoneComplianceData(BaseModel):
    """Zone-level compliance data for Manager Portal"""
    zone_name: str
    compliance_percentage: float
    total_facilities: int
    facilities: List[FacilityComplianceData]

    class Config:
        json_schema_extra = {
            "example": {
                "zone_name": "North Zone",
                "compliance_percentage": 85.3,
                "total_facilities": 5,
                "facilities": []
            }
        }


class CountryComplianceData(BaseModel):
    """Country-level compliance data for Manager Portal"""
    country_name: str
    compliance_percentage: float
    total_zones: int
    total_facilities: int
    zones: List[ZoneComplianceData]

    class Config:
        json_schema_extra = {
            "example": {
                "country_name": "India",
                "compliance_percentage": 82.5,
                "total_zones": 3,
                "total_facilities": 15,
                "zones": []
            }
        }


class ManagerDashboardResponse(BaseModel):
    """Complete Manager Portal dashboard data"""
    countries: List[CountryComplianceData]
    total_audits: int
    last_updated: str

    class Config:
        json_schema_extra = {
            "example": {
                "countries": [],
                "total_audits": 150,
                "last_updated": "2026-02-10T15:00:00"
            }
        }

