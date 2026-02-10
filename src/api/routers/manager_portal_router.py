"""
Manager Portal API Router
==========================
FastAPI endpoints for Manager Portal dashboard data retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from src.api.schemas.manager_portal_schemas import (
    ManagerDashboardResponse,
    CountryComplianceData,
    ZoneComplianceData,
    FacilityComplianceData
)
from src.infrastructure.database.manual_audit_db import get_db
from src.infrastructure.database.manual_audit_repository import ManualAuditRepository

# Create router
router = APIRouter(
    prefix="/api/v1/manager",
    tags=["Manager Portal"]
)


@router.get(
    "/dashboard",
    response_model=ManagerDashboardResponse,
    summary="Get Manager Dashboard Data",
    description="Retrieve aggregated compliance data for Manager Portal dashboard view"
)
async def get_manager_dashboard(db: Session = Depends(get_db)):
    """
    Get complete Manager Portal dashboard data

    Returns hierarchical compliance data aggregated from manual_audits table:
    - Country-level compliance metrics
    - Zone-level performance within each country
    - Facility-level details within each zone

    **Compliance Calculation:**
    - Audit is considered "compliant" if:
      - compliance_status = "Compliant" OR
      - confidence_level >= 80%
    - Compliance % = (compliant_audits / total_audits) * 100

    **Response Structure:**
    ```json
    {
      "countries": [
        {
          "country_name": "India",
          "compliance_percentage": 85.3,
          "total_zones": 3,
          "total_facilities": 12,
          "zones": [
            {
              "zone_name": "North Zone",
              "compliance_percentage": 87.5,
              "total_facilities": 5,
              "facilities": [
                {
                  "facility_id": "DEALER001",
                  "facility_name": "Downtown Stellantis",
                  "compliance_percentage": 92.0,
                  "total_audits": 25,
                  "completed_audits": 25,
                  "pending_audits": 0,
                  "last_audit_date": "2026-02-10T14:30:00",
                  "zone": "North Zone"
                }
              ]
            }
          ]
        }
      ],
      "total_audits": 150,
      "last_updated": "2026-02-10T15:00:00"
    }
    ```

    **Use Case:**
    - Manager Portal homepage displays country cards
    - Tapping a country shows zones
    - Tapping a zone shows facilities
    - Data refreshes on page reload

    **HTTP Responses:**
    - 200: Success with dashboard data
    - 500: Database error
    """
    try:
        print("📊 Manager Portal: Fetching dashboard data...")

        # Get aggregated data from repository
        dashboard_data = ManualAuditRepository.get_manager_dashboard_data(db)

        # Convert to Pydantic models for validation
        countries = []
        for country_dict in dashboard_data["countries"]:
            zones = []
            for zone_dict in country_dict["zones"]:
                facilities = [
                    FacilityComplianceData(**facility_dict)
                    for facility_dict in zone_dict["facilities"]
                ]
                zones.append(
                    ZoneComplianceData(
                        zone_name=zone_dict["zone_name"],
                        compliance_percentage=zone_dict["compliance_percentage"],
                        total_facilities=zone_dict["total_facilities"],
                        facilities=facilities
                    )
                )
            countries.append(
                CountryComplianceData(
                    country_name=country_dict["country_name"],
                    compliance_percentage=country_dict["compliance_percentage"],
                    total_zones=country_dict["total_zones"],
                    total_facilities=country_dict["total_facilities"],
                    zones=zones
                )
            )

        response = ManagerDashboardResponse(
            countries=countries,
            total_audits=dashboard_data["total_audits"],
            last_updated=dashboard_data["last_updated"]
        )

        print(f"✅ Manager Portal: Returned data for {len(countries)} countries, {dashboard_data['total_audits']} total audits")

        return response

    except Exception as e:
        print(f"❌ Manager Portal error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch manager dashboard data: {str(e)}"
        )


@router.get(
    "/zone/{country}/{zone_name}",
    summary="Get Zone Summary",
    description="Retrieve summary statistics for a specific zone"
)
async def get_zone_summary(
    country: str,
    zone_name: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get summary for a specific zone

    **Path Parameters:**
    - country: Country name (e.g., "India")
    - zone_name: Zone name (e.g., "North Zone")

    **Response:**
    ```json
    {
      "zone": "North Zone",
      "country": "India",
      "total_audits": 45,
      "compliance_percentage": 87.5,
      "facilities_count": 5
    }
    ```

    **Use Case:**
    - Quick zone statistics without full facility details
    - Can be used for charts/graphs

    **HTTP Responses:**
    - 200: Success with zone summary
    - 500: Database error
    """
    try:
        print(f"📊 Manager Portal: Fetching zone summary for {zone_name}, {country}...")

        summary = ManualAuditRepository.get_zone_summary(db, country, zone_name)

        print(f"✅ Manager Portal: Zone summary returned")

        return summary

    except Exception as e:
        print(f"❌ Manager Portal error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch zone summary: {str(e)}"
        )


@router.get(
    "/facility/{facility_id}/audits",
    summary="Get Facility Audits",
    description="Retrieve all audits for a specific facility"
)
async def get_facility_audits(
    facility_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all audits for a specific facility

    **Path Parameters:**
    - facility_id: Facility/Dealer ID (e.g., "DEALER001")

    **Response:**
    ```json
    {
      "facility_id": "DEALER001",
      "total_audits": 25,
      "audits": [
        {
          "id": 1,
          "date": "2026-02-10",
          "compliance_status": "Compliant",
          "confidence_level": 95.5,
          "checkpoint": "Surface Sanitation",
          "feedback": "Excellent hygiene"
        }
      ]
    }
    ```

    **Use Case:**
    - Facility detail page showing audit history
    - Audit trend analysis

    **HTTP Responses:**
    - 200: Success with facility audits
    - 404: Facility not found
    - 500: Database error
    """
    try:
        print(f"📊 Manager Portal: Fetching audits for facility {facility_id}...")

        audits = ManualAuditRepository.get_facility_audits(db, facility_id)

        if not audits:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No audits found for facility {facility_id}"
            )

        audit_list = [
            {
                "id": audit.id,
                "date": audit.date.isoformat(),
                "compliance_status": audit.compliance_status,
                "confidence_level": audit.confidence_level,
                "checkpoint": audit.checkpoint,
                "feedback": audit.feedback,
                "shift": audit.shift,
                "created_at": audit.created_at.isoformat()
            }
            for audit in audits
        ]

        print(f"✅ Manager Portal: Returned {len(audit_list)} audits for facility {facility_id}")

        return {
            "facility_id": facility_id,
            "total_audits": len(audit_list),
            "audits": audit_list
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Manager Portal error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch facility audits: {str(e)}"
        )

