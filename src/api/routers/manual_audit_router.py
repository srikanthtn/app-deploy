"""
Manual Audit API Router
========================
FastAPI endpoints for manual audit submission and retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from src.api.schemas.manual_audit_schemas import (
    ManualAuditCreate,
    ManualAuditResponse,
    ManualAuditListResponse,
    HealthCheckResponse
)
from src.infrastructure.database.manual_audit_db import get_db
from src.infrastructure.database.manual_audit_repository import ManualAuditRepository

# Create router
router = APIRouter(
    prefix="/api/v1",
    tags=["Manual Audit"]
)


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint

    Returns API status and timestamp
    """
    return {
        "status": "healthy",
        "message": "Manual Audit API is running",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post(
    "/manual-audit",
    response_model=ManualAuditResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Manual Audit",
    description="Submit a new manual audit from the Flutter mobile app"
)
async def create_manual_audit(
    audit: ManualAuditCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new manual audit

    **Request Body:**
    - All dealer, audit, location, and credential fields

    **Response:**
    - Created audit with assigned ID
    - HTTP 201 on success
    - HTTP 400 on validation error
    - HTTP 500 on database error
    """
    try:
        print(f"📥 Received manual audit submission from dealer: {audit.dealer_id}")

        # Create audit in database
        db_audit = ManualAuditRepository.create(db, audit)

        print(f"✅ Manual audit created successfully with ID: {db_audit.id}")

        # Return response
        return ManualAuditResponse(
            id=db_audit.id,
            dealer_id=db_audit.dealer_id,
            dealer_name=db_audit.dealer_name,
            dealer_details=db_audit.dealer_details,
            dealer_consolidated_summary=db_audit.dealer_consolidated_summary,
            date=db_audit.date.isoformat(),
            month=db_audit.month,
            time=db_audit.time.isoformat(),
            shift=db_audit.shift,
            compliance_status=db_audit.compliance_status,
            level_1=db_audit.level_1,
            sub_category=db_audit.sub_category,
            checkpoint=db_audit.checkpoint,
            photo_url=db_audit.photo_url,
            confidence_level=db_audit.confidence_level,
            feedback=db_audit.feedback,
            language=db_audit.language,
            country=db_audit.country,
            zone=db_audit.zone,
            email=db_audit.email,
            created_at=db_audit.created_at.isoformat(),
            updated_at=db_audit.updated_at.isoformat() if db_audit.updated_at else None,
        )

    except ValueError as e:
        print(f"❌ Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data format: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create manual audit: {str(e)}"
        )


@router.get(
    "/manual-audit/{audit_id}",
    response_model=ManualAuditResponse,
    summary="Get Manual Audit by ID",
    description="Retrieve a specific manual audit by its ID"
)
async def get_manual_audit(
    audit_id: int,
    db: Session = Depends(get_db)
):
    """
    Get manual audit by ID

    **Path Parameters:**
    - audit_id: Unique audit identifier

    **Response:**
    - Audit details if found
    - HTTP 404 if not found
    """
    audit = ManualAuditRepository.get_by_id(db, audit_id)

    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Manual audit with ID {audit_id} not found"
        )

    return ManualAuditResponse(
        id=audit.id,
        dealer_id=audit.dealer_id,
        dealer_name=audit.dealer_name,
        dealer_details=audit.dealer_details,
        dealer_consolidated_summary=audit.dealer_consolidated_summary,
        date=audit.date.isoformat(),
        month=audit.month,
        time=audit.time.isoformat(),
        shift=audit.shift,
        compliance_status=audit.compliance_status,
        level_1=audit.level_1,
        sub_category=audit.sub_category,
        checkpoint=audit.checkpoint,
        photo_url=audit.photo_url,
        confidence_level=audit.confidence_level,
        feedback=audit.feedback,
        language=audit.language,
        country=audit.country,
        zone=audit.zone,
        email=audit.email,
        created_at=audit.created_at.isoformat(),
        updated_at=audit.updated_at.isoformat() if audit.updated_at else None,
    )


@router.get(
    "/manual-audits",
    response_model=ManualAuditListResponse,
    summary="List All Manual Audits",
    description="Retrieve all manual audits with pagination"
)
async def list_manual_audits(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all manual audits

    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum records to return (default: 100, max: 1000)

    **Response:**
    - List of audits with total count
    """
    if limit > 1000:
        limit = 1000

    audits = ManualAuditRepository.get_all(db, skip=skip, limit=limit)
    total = ManualAuditRepository.count(db)

    audit_responses = [
        ManualAuditResponse(
            id=audit.id,
            dealer_id=audit.dealer_id,
            dealer_name=audit.dealer_name,
            dealer_details=audit.dealer_details,
            dealer_consolidated_summary=audit.dealer_consolidated_summary,
            date=audit.date.isoformat(),
            month=audit.month,
            time=audit.time.isoformat(),
            shift=audit.shift,
            compliance_status=audit.compliance_status,
            level_1=audit.level_1,
            sub_category=audit.sub_category,
            checkpoint=audit.checkpoint,
            photo_url=audit.photo_url,
            confidence_level=audit.confidence_level,
            feedback=audit.feedback,
            language=audit.language,
            country=audit.country,
            zone=audit.zone,
            email=audit.email,
            created_at=audit.created_at.isoformat(),
            updated_at=audit.updated_at.isoformat() if audit.updated_at else None,
        )
        for audit in audits
    ]

    return ManualAuditListResponse(
        total=total,
        audits=audit_responses
    )


@router.get(
    "/manual-audits/dealer/{dealer_id}",
    response_model=ManualAuditListResponse,
    summary="Get Audits by Dealer",
    description="Retrieve all manual audits for a specific dealer"
)
async def get_audits_by_dealer(
    dealer_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get manual audits by dealer ID

    **Path Parameters:**
    - dealer_id: Dealer identifier

    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum records to return (default: 100)

    **Response:**
    - List of audits for the dealer with total count
    """
    audits = ManualAuditRepository.get_by_dealer(db, dealer_id, skip=skip, limit=limit)
    total = len(audits)

    audit_responses = [
        ManualAuditResponse(
            id=audit.id,
            dealer_id=audit.dealer_id,
            dealer_name=audit.dealer_name,
            dealer_details=audit.dealer_details,
            dealer_consolidated_summary=audit.dealer_consolidated_summary,
            date=audit.date.isoformat(),
            month=audit.month,
            time=audit.time.isoformat(),
            shift=audit.shift,
            compliance_status=audit.compliance_status,
            level_1=audit.level_1,
            sub_category=audit.sub_category,
            checkpoint=audit.checkpoint,
            photo_url=audit.photo_url,
            confidence_level=audit.confidence_level,
            feedback=audit.feedback,
            language=audit.language,
            country=audit.country,
            zone=audit.zone,
            email=audit.email,
            created_at=audit.created_at.isoformat(),
            updated_at=audit.updated_at.isoformat() if audit.updated_at else None,
        )
        for audit in audits
    ]

    return ManualAuditListResponse(
        total=total,
        audits=audit_responses
    )

