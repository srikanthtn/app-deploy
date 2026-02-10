"""
Hygiene Analysis API Routes

WHY: API layer responsibilities:
1. Request validation (Pydantic)
2. Authentication/authorization
3. Correlation ID injection
4. Error translation to HTTP responses
5. NO business logic

This is the outermost layer - adapts HTTP to application layer.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from pydantic import BaseModel, Field

from ...application.use_cases.analyze_cleanliness import (
    AnalyzeCleanlinessUseCase,
    AnalyzeCleanlinessCommand
)
from ...domain.value_objects import CleanlinessStatus
from ..dependencies import get_analyze_use_case, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/hygiene", tags=["Hygiene Analysis"])


# === Request/Response DTOs ===

class AnalysisResponse(BaseModel):
    """
    API response for cleanliness analysis.
    
    WHY: Pydantic model for automatic JSON serialization and OpenAPI docs.
    This is the "view model" - what API consumers see.
    """
    audit_id: UUID
    dealer_id: str
    checkpoint_id: str
    status: CleanlinessStatus
    confidence: float
    reason: str
    negative_labels: list[dict]
    image_url: Optional[str] = None
    analyzed_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "audit_id": "123e4567-e89b-12d3-a456-426614174000",
                "dealer_id": "dealer-001",
                "checkpoint_id": "reception",
                "status": "CLEAN",
                "confidence": 94.5,
                "reason": "No cleanliness issues detected",
                "negative_labels": [],
                "analyzed_at": "2024-01-15T10:30:00Z"
            }
        }


class ManualOverrideRequest(BaseModel):
    """Request to override AI decision"""
    audit_id: UUID
    is_clean: bool
    reviewer_notes: str = Field(..., min_length=10)


# === Endpoints ===

@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze facility cleanliness",
    description="""
    Upload a facility image for automated cleanliness analysis.
    
    **Process:**
    1. Image uploaded to S3
    2. Amazon Rekognition analyzes image
    3. Business rules evaluate cleanliness
    4. Results stored for audit trail
    
    **Returns:**
    - CLEAN: Facility passes hygiene standards
    - NOT_CLEAN: Issues detected (see negative_labels for details)
    - REQUIRES_MANUAL_REVIEW: Low confidence, needs human review
    - INSUFFICIENT_DATA: Unable to analyze
    """
)
async def analyze_cleanliness(
    dealer_id: str = Form(..., description="Dealer identifier"),
    checkpoint_id: str = Form(..., description="Checkpoint/location identifier"),
    image: UploadFile = File(..., description="Facility image (JPEG/PNG, max 15MB)"),
    min_confidence: float = Form(70.0, ge=0.0, le=100.0),
    use_case: AnalyzeCleanlinessUseCase = Depends(get_analyze_use_case),
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze facility image for cleanliness.
    
    WHY: Form data (not JSON) because we're uploading a file.
    
    Security: Requires authentication (current_user dependency).
    WHY: Only authorized mobile app users can submit audits.
    """
    # Validation: Check file type
    logger.info(f"📸 Received image with content_type: {image.content_type}, filename: {image.filename}")
    if image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image format '{image.content_type}'. Must be JPEG or PNG."
        )
    
    # Validation: Check file size
    image_bytes = await image.read()
    size_mb = len(image_bytes) / (1024 * 1024)
    
    if size_mb > 15:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image too large ({size_mb:.1f}MB). Maximum 15MB."
        )
    
    logger.info(
        f"Received analysis request for dealer={dealer_id}, checkpoint={checkpoint_id}",
        extra={
            "dealer_id": dealer_id,
            "checkpoint_id": checkpoint_id,
            "uploader_id": current_user['user_id'],
            "file_size_mb": size_mb
        }
    )
    
    try:
        # Execute use case
        command = AnalyzeCleanlinessCommand(
            dealer_id=dealer_id,
            checkpoint_id=checkpoint_id,
            uploader_id=current_user['user_id'],
            image_bytes=image_bytes,
            content_type=image.content_type,
            min_confidence=min_confidence
        )
        
        audit_result = await use_case.execute(command)
        
        # Convert domain entity to API response
        return AnalysisResponse(
            audit_id=audit_result.audit_id,
            dealer_id=audit_result.image_metadata.dealer_id,
            checkpoint_id=audit_result.image_metadata.checkpoint_id,
            status=audit_result.status,
            confidence=audit_result.overall_confidence.value,
            reason=audit_result.reason,
            negative_labels=[
                {"name": label.name, "confidence": label.confidence.value}
                for label in audit_result.negative_labels
            ],
            analyzed_at=audit_result.analyzed_at.isoformat() + "Z"
        )
    
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        
        # WHY: Translate exceptions to appropriate HTTP errors
        # In production, use more granular error handling
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed. Please try again."
        )


@router.get(
    "/audits/{audit_id}",
    response_model=AnalysisResponse,
    summary="Get audit result by ID"
)
async def get_audit(
    audit_id: UUID,
    use_case: AnalyzeCleanlinessUseCase = Depends(get_analyze_use_case),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve audit result by ID.
    
    WHY: Idempotent GET - clients can poll for results.
    """
    # Implementation: Query repository
    # For now, returns 404
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Audit {audit_id} not found"
    )


@router.post(
    "/audits/{audit_id}/override",
    response_model=AnalysisResponse,
    summary="Apply manual override to audit",
    description="""
    Auditor can override AI decision.
    
    **Use cases:**
    - AI incorrectly flagged as NOT_CLEAN
    - AI missed obvious issues
    - Requires human judgment call
    
    **Audit trail:** Override is logged with reviewer ID and timestamp.
    """
)
async def override_audit(
    audit_id: UUID,
    request: ManualOverrideRequest,
    use_case: AnalyzeCleanlinessUseCase = Depends(get_analyze_use_case),
    current_user: dict = Depends(get_current_user)
):
    """
    Apply manual override to existing audit.
    
    WHY: Humans must be able to correct AI mistakes.
    Security: Only authorized reviewers can override.
    """
    # Implementation: Load audit, apply override, save
    # For now, returns 404
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Audit {audit_id} not found"
    )


@router.get(
    "/dealers/{dealer_id}/stats",
    summary="Get dealer cleanliness statistics",
    description="Aggregate statistics for dealer compliance reporting"
)
async def get_dealer_stats(
    dealer_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get cleanliness compliance stats for dealer.
    
    WHY: Dashboard/reporting requirement.
    Returns: Counts by status, compliance rate, trend.
    """
    # Implementation: Query repository for aggregates
    return {
        "dealer_id": dealer_id,
        "total_audits": 0,
        "clean": 0,
        "not_clean": 0,
        "requires_review": 0,
        "compliance_rate": 0.0
    }
