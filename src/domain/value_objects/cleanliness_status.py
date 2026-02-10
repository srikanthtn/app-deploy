"""
Cleanliness Status Value Object

WHY: Represents the business decision about facility cleanliness.
This is a domain concept, NOT a technical enum from Rekognition.
"""
from enum import Enum
from typing import List, Optional


class CleanlinessStatus(str, Enum):
    """
    Business-level cleanliness determination.
    
    WHY: Using Enum ensures type safety and prevents invalid states.
    Inheriting from str makes it JSON serializable for FastAPI.
    """
    CLEAN = "CLEAN"
    NOT_CLEAN = "NOT_CLEAN"
    REQUIRES_MANUAL_REVIEW = "REQUIRES_MANUAL_REVIEW"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

    def is_compliant(self) -> bool:
        """WHY: Business rule - only CLEAN facilities pass audit"""
        return self == CleanlinessStatus.CLEAN

    def requires_human_intervention(self) -> bool:
        """WHY: These statuses need auditor review before final decision"""
        return self in {
            CleanlinessStatus.REQUIRES_MANUAL_REVIEW,
            CleanlinessStatus.INSUFFICIENT_DATA
        }

    @staticmethod
    def from_evaluation(
        negative_labels: List[str],
        confidence_below_threshold: bool,
        manual_override: Optional[bool] = None
    ) -> "CleanlinessStatus":
        """
        Factory method to determine status from evaluation criteria.
        
        WHY: Centralizes business logic for status determination.
        This is a domain rule that should NEVER live in a controller.
        
        Business Rules:
        1. Manual override always wins (for auditor corrections)
        2. Low confidence triggers manual review
        3. Presence of negative labels = NOT_CLEAN
        4. Otherwise = CLEAN
        """
        if manual_override is not None:
            return CleanlinessStatus.CLEAN if manual_override else CleanlinessStatus.NOT_CLEAN
        
        if confidence_below_threshold:
            return CleanlinessStatus.REQUIRES_MANUAL_REVIEW
        
        if negative_labels:
            return CleanlinessStatus.NOT_CLEAN
        
        return CleanlinessStatus.CLEAN
