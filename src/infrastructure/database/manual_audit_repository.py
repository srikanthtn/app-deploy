"""
Manual Audit Repository
========================
Data access layer for manual audit operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.infrastructure.database.manual_audit_models import ManualAudit
from src.api.schemas.manual_audit_schemas import ManualAuditCreate


class ManualAuditRepository:
    """Repository for manual audit database operations"""

    @staticmethod
    def create(db: Session, audit_data: ManualAuditCreate) -> ManualAudit:
        """
        Create a new manual audit record

        Args:
            db: Database session
            audit_data: Manual audit data from request

        Returns:
            Created ManualAudit instance
        """
        # Parse date and time strings to datetime
        audit_date = datetime.fromisoformat(audit_data.date.replace('Z', '+00:00'))
        audit_time = datetime.fromisoformat(audit_data.time.replace('Z', '+00:00'))

        # Create database model instance
        db_audit = ManualAudit(
            dealer_id=audit_data.dealer_id,
            dealer_name=audit_data.dealer_name,
            dealer_details=audit_data.dealer_details,
            dealer_consolidated_summary=audit_data.dealer_consolidated_summary,
            date=audit_date,
            month=audit_data.month,
            time=audit_time,
            shift=audit_data.shift,
            compliance_status=audit_data.compliance_status,
            level_1=audit_data.level_1,
            sub_category=audit_data.sub_category,
            checkpoint=audit_data.checkpoint,
            photo_url=audit_data.photo_url,
            confidence_level=audit_data.confidence_level,
            feedback=audit_data.feedback,
            language=audit_data.language,
            country=audit_data.country,
            zone=audit_data.zone,
            email=audit_data.email,
            password=audit_data.password,  # NOTE: Hash this in production!
        )

        # Add to database
        db.add(db_audit)
        db.commit()
        db.refresh(db_audit)

        return db_audit

    @staticmethod
    def get_by_id(db: Session, audit_id: int) -> Optional[ManualAudit]:
        """
        Get manual audit by ID

        Args:
            db: Database session
            audit_id: Audit ID

        Returns:
            ManualAudit instance or None
        """
        return db.query(ManualAudit).filter(ManualAudit.id == audit_id).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[ManualAudit]:
        """
        Get all manual audits with pagination

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of ManualAudit instances
        """
        return db.query(ManualAudit).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_dealer(db: Session, dealer_id: str, skip: int = 0, limit: int = 100) -> List[ManualAudit]:
        """
        Get manual audits by dealer ID

        Args:
            db: Database session
            dealer_id: Dealer ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of ManualAudit instances
        """
        return (
            db.query(ManualAudit)
            .filter(ManualAudit.dealer_id == dealer_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_date_range(
        db: Session,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[ManualAudit]:
        """
        Get manual audits within date range

        Args:
            db: Database session
            start_date: Start date
            end_date: End date
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of ManualAudit instances
        """
        return (
            db.query(ManualAudit)
            .filter(ManualAudit.date >= start_date, ManualAudit.date <= end_date)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def count(db: Session) -> int:
        """
        Count total manual audits

        Args:
            db: Database session

        Returns:
            Total count of manual audits
        """
        return db.query(ManualAudit).count()

    @staticmethod
    def delete(db: Session, audit_id: int) -> bool:
        """
        Delete manual audit by ID

        Args:
            db: Database session
            audit_id: Audit ID

        Returns:
            True if deleted, False if not found
        """
        audit = db.query(ManualAudit).filter(ManualAudit.id == audit_id).first()
        if audit:
            db.delete(audit)
            db.commit()
            return True
        return False

    # ==========================================================================
    # MANAGER PORTAL AGGREGATION METHODS
    # ==========================================================================

    @staticmethod
    def get_manager_dashboard_data(db: Session) -> Dict[str, Any]:
        """
        Get aggregated compliance data for Manager Portal dashboard

        Aggregates manual_audits data into hierarchical structure:
        Country → Zone → Facility with calculated compliance percentages

        Args:
            db: Database session

        Returns:
            Dict containing countries list with nested zones and facilities
        """
        # Get all audits
        all_audits = db.query(ManualAudit).all()

        if not all_audits:
            return {
                "countries": [],
                "total_audits": 0,
                "last_updated": datetime.utcnow().isoformat()
            }

        # Group audits by country → zone → facility
        country_data = {}

        for audit in all_audits:
            country = audit.country
            zone = audit.zone
            facility_id = audit.dealer_id
            facility_name = audit.dealer_name

            # Initialize country if not exists
            if country not in country_data:
                country_data[country] = {
                    "zones": {}
                }

            # Initialize zone if not exists
            if zone not in country_data[country]["zones"]:
                country_data[country]["zones"][zone] = {
                    "facilities": {}
                }

            # Initialize facility if not exists
            if facility_id not in country_data[country]["zones"][zone]["facilities"]:
                country_data[country]["zones"][zone]["facilities"][facility_id] = {
                    "facility_name": facility_name,
                    "audits": [],
                    "zone": zone
                }

            # Add audit to facility
            country_data[country]["zones"][zone]["facilities"][facility_id]["audits"].append({
                "compliance_status": audit.compliance_status,
                "confidence_level": audit.confidence_level,
                "date": audit.date,
                "created_at": audit.created_at
            })

        # Calculate compliance percentages and structure response
        countries_list = []

        for country_name, country_info in country_data.items():
            zones_list = []
            country_total_compliant = 0
            country_total_audits = 0

            for zone_name, zone_info in country_info["zones"].items():
                facilities_list = []
                zone_total_compliant = 0
                zone_total_audits = 0

                for facility_id, facility_info in zone_info["facilities"].items():
                    audits = facility_info["audits"]
                    total_audits = len(audits)

                    # Calculate compliance: Compliant status OR confidence >= 80
                    compliant_audits = sum(
                        1 for a in audits
                        if a["compliance_status"].lower() == "compliant"
                        or a["confidence_level"] >= 80
                    )

                    compliance_percentage = (compliant_audits / total_audits * 100) if total_audits > 0 else 0

                    # Get last audit date
                    last_audit = max(audits, key=lambda a: a["created_at"])

                    # Count completed vs pending (for demonstration, all are completed)
                    completed_audits = total_audits
                    pending_audits = 0

                    facilities_list.append({
                        "facility_id": facility_id,
                        "facility_name": facility_info["facility_name"],
                        "compliance_percentage": round(compliance_percentage, 1),
                        "total_audits": total_audits,
                        "completed_audits": completed_audits,
                        "pending_audits": pending_audits,
                        "last_audit_date": last_audit["created_at"].isoformat(),
                        "zone": facility_info["zone"]
                    })

                    zone_total_compliant += compliant_audits
                    zone_total_audits += total_audits

                # Calculate zone compliance
                zone_compliance = (zone_total_compliant / zone_total_audits * 100) if zone_total_audits > 0 else 0

                zones_list.append({
                    "zone_name": zone_name,
                    "compliance_percentage": round(zone_compliance, 1),
                    "total_facilities": len(facilities_list),
                    "facilities": facilities_list
                })

                country_total_compliant += zone_total_compliant
                country_total_audits += zone_total_audits

            # Calculate country compliance
            country_compliance = (country_total_compliant / country_total_audits * 100) if country_total_audits > 0 else 0

            countries_list.append({
                "country_name": country_name,
                "compliance_percentage": round(country_compliance, 1),
                "total_zones": len(zones_list),
                "total_facilities": sum(z["total_facilities"] for z in zones_list),
                "zones": zones_list
            })

        return {
            "countries": countries_list,
            "total_audits": len(all_audits),
            "last_updated": datetime.utcnow().isoformat()
        }

    @staticmethod
    def get_facility_audits(db: Session, facility_id: str) -> List[ManualAudit]:
        """
        Get all audits for a specific facility (dealer)

        Args:
            db: Database session
            facility_id: Facility/Dealer ID

        Returns:
            List of ManualAudit instances for the facility
        """
        return (
            db.query(ManualAudit)
            .filter(ManualAudit.dealer_id == facility_id)
            .order_by(desc(ManualAudit.created_at))
            .all()
        )

    @staticmethod
    def get_zone_summary(db: Session, country: str, zone: str) -> Dict[str, Any]:
        """
        Get summary statistics for a specific zone

        Args:
            db: Database session
            country: Country name
            zone: Zone name

        Returns:
            Dict with zone statistics
        """
        audits = (
            db.query(ManualAudit)
            .filter(ManualAudit.country == country, ManualAudit.zone == zone)
            .all()
        )

        if not audits:
            return {
                "zone": zone,
                "country": country,
                "total_audits": 0,
                "compliance_percentage": 0,
                "facilities_count": 0
            }

        total_audits = len(audits)
        compliant_audits = sum(
            1 for a in audits
            if a.compliance_status.lower() == "compliant" or a.confidence_level >= 80
        )

        facilities = set(a.dealer_id for a in audits)

        return {
            "zone": zone,
            "country": country,
            "total_audits": total_audits,
            "compliance_percentage": round((compliant_audits / total_audits * 100), 1),
            "facilities_count": len(facilities)
        }


