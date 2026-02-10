"""
Confidence Score Value Object

WHY: Encapsulates validation and business rules around confidence scores.
Prevents invalid scores from entering the domain.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ConfidenceScore:
    """
    Immutable confidence score value object.
    
    WHY frozen=True: Value objects should be immutable to prevent
    accidental state mutations that violate business invariants.
    """
    value: float

    def __post_init__(self):
        """
        WHY: Fail-fast validation at domain boundaries.
        Invalid data should never enter the domain model.
        """
        if not 0.0 <= self.value <= 100.0:
            raise ValueError(f"Confidence score must be between 0 and 100, got {self.value}")

    def is_above_threshold(self, threshold: float) -> bool:
        """
        WHY: Domain method encapsulates comparison logic.
        Prevents scattered threshold checks across codebase.
        """
        return self.value >= threshold

    def as_percentage(self) -> str:
        """WHY: Presentation concern, but useful for logging/debugging"""
        return f"{self.value:.2f}%"

    @classmethod
    def from_rekognition(cls, score: float) -> "ConfidenceScore":
        """
        Factory for Rekognition scores (0-100 range).
        
        WHY: Explicit conversion from infrastructure format to domain format.
        Different vision providers may use different scales (0-1, 0-100, etc).
        """
        return cls(value=score)

    @classmethod
    def from_normalized(cls, score: float) -> "ConfidenceScore":
        """
        Factory for normalized scores (0.0-1.0 range).
        
        WHY: Some models (TFLite, custom) return 0-1 scores.
        This factory handles the conversion explicitly.
        """
        return cls(value=score * 100.0)
