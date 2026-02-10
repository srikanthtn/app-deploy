"""
Audit Result Entity

WHY: This is the core domain entity representing a hygiene audit outcome.
It's NOT a database model - it's a business concept with identity and lifecycle.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from ..value_objects import CleanlinessStatus, ConfidenceScore, ImageMetadata


@dataclass
class DetectedLabel:
    """
    Individual label from vision analysis.
    
    WHY: Separated from AuditResult to support explainability.
    Auditors need to see WHICH labels caused NOT_CLEAN verdict.
    """
    name: str
    confidence: ConfidenceScore
    is_negative: bool  # Indicates unclean condition

    def __str__(self) -> str:
        flag = "❌" if self.is_negative else "✓"
        return f"{flag} {self.name} ({self.confidence.as_percentage()})"


@dataclass(kw_only=True)
class AuditResult:
    """
    Core domain entity: Result of a hygiene audit analysis.
    
    WHY: Entity (not value object) because:
    1. It has identity (audit_id)
    2. It has lifecycle (created, reviewed, archived)
    3. It's mutable (can be manually overridden)
    
    Lifecycle:
    CREATED → ANALYZED → (optionally) MANUALLY_REVIEWED → FINALIZED
    """
    # Identity
    audit_id: UUID = field(default_factory=uuid4)
    
    # Relationships
    image_metadata: ImageMetadata
    
    # Analysis Results
    detected_labels: List[DetectedLabel]
    overall_confidence: ConfidenceScore
    status: CleanlinessStatus
    
    # Explainability
    negative_labels: List[DetectedLabel] = field(default_factory=list)
    reason: Optional[str] = None
    
    # Audit Trail
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    manual_override: Optional[bool] = None
    
    # Technical Metadata
    vision_provider: str = "rekognition"  # Supports future: "tflite", "custom"
    model_version: Optional[str] = None

    def __post_init__(self):
        """
        WHY: Separate negative labels for explainability.
        Business requirement: Show users WHY something is not clean.
        """
        self.negative_labels = [
            label for label in self.detected_labels if label.is_negative
        ]
        
        if not self.reason:
            self.reason = self._generate_reason()

    def _generate_reason(self) -> str:
        """
        Generate human-readable explanation.
        
        WHY: Explainability is critical for:
        1. Dealer dispute resolution
        2. Auditor training
        3. Regulatory compliance
        """
        if self.status == CleanlinessStatus.CLEAN:
            return "No cleanliness issues detected"
        
        if self.status == CleanlinessStatus.INSUFFICIENT_DATA:
            return f"Confidence too low ({self.overall_confidence.as_percentage()})"
        
        if self.status == CleanlinessStatus.REQUIRES_MANUAL_REVIEW:
            return "Unclear results - manual review required"
        
        if self.negative_labels:
            label_names = [label.name for label in self.negative_labels[:3]]
            return f"Issues detected: {', '.join(label_names)}"
        
        return "Status determination unclear"

    def apply_manual_override(self, reviewer_id: str, is_clean: bool, notes: str) -> None:
        """
        Apply manual auditor override.
        
        WHY: Humans must be able to correct AI mistakes.
        This is a domain operation with business rules.
        
        Business Rules:
        1. Override always takes precedence
        2. Must record WHO made the decision (accountability)
        3. Must record WHEN (audit trail)
        """
        self.manual_override = is_clean
        self.status = CleanlinessStatus.CLEAN if is_clean else CleanlinessStatus.NOT_CLEAN
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow()
        self.reason = f"Manual override: {notes}"

    def is_finalized(self) -> bool:
        """WHY: Prevent re-analysis of already-reviewed audits"""
        return self.reviewed_by is not None

    def passes_compliance(self) -> bool:
        """
        Domain method: Does this audit represent a passing grade?
        
        WHY: Business rule centralized in domain, not scattered across services.
        """
        return self.status.is_compliant()

    def requires_review(self) -> bool:
        """WHY: Workflow routing decision based on domain state"""
        return self.status.requires_human_intervention()
