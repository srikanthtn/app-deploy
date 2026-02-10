"""
Vision Provider Port (Interface)

WHY: This is the PRIMARY abstraction that makes the architecture flexible.
Domain doesn't know about Rekognition - it only knows this contract.

This is the Hexagonal Architecture "port" - the domain defines WHAT it needs,
infrastructure provides HOW (through adapters).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from ..value_objects import ConfidenceScore


@dataclass
class VisionLabel:
    """
    Provider-agnostic label representation.
    
    WHY: Different vision providers return different formats:
    - Rekognition: {'Name': 'Dirt', 'Confidence': 95.5}
    - TFLite: {0: 0.955, 1: 0.045} (index-based)
    - Custom: varies
    
    This dataclass normalizes ALL formats into domain language.
    """
    name: str
    confidence: ConfidenceScore
    category: str = "general"  # e.g., "cleanliness", "safety", "equipment"


@dataclass
class VisionAnalysisResult:
    """
    Complete vision analysis result.
    
    WHY: Encapsulates everything a vision provider returns.
    Domain uses this to make business decisions.
    """
    labels: List[VisionLabel]
    moderation_labels: List[VisionLabel] = None  # e.g., explicit content detection
    text_detections: List[str] = None  # OCR results (future use)
    provider_name: str = "unknown"
    model_version: str = "unknown"
    processing_time_ms: int = 0

    @property
    def highest_confidence_label(self) -> VisionLabel:
        """WHY: Often need the most confident prediction"""
        return max(self.labels, key=lambda x: x.confidence.value)


class VisionProvider(ABC):
    """
    Port (interface) for vision analysis providers.
    
    WHY: Strategy Pattern implementation.
    - Application layer depends on THIS interface, not concrete implementations
    - Infrastructure layer provides adapters (RekognitionAdapter, TFLiteAdapter)
    - We can swap providers without touching domain/application code
    
    Design Decision: async/await for I/O-bound operations.
    WHY: Rekognition API calls are network I/O - async enables concurrency.
    """

    @abstractmethod
    async def analyze_image(
        self,
        image_bytes: bytes,
        max_labels: int = 50,
        min_confidence: float = 70.0
    ) -> VisionAnalysisResult:
        """
        Analyze image and return detected labels.
        
        Args:
            image_bytes: Raw image data (JPEG/PNG)
            max_labels: Maximum number of labels to return
            min_confidence: Minimum confidence threshold (0-100)
        
        Returns:
            VisionAnalysisResult with detected labels
        
        Raises:
            VisionProviderError: If analysis fails
        
        WHY async: Network calls to Rekognition/external services are I/O-bound.
        """
        pass

    @abstractmethod
    async def analyze_image_from_s3(
        self,
        bucket: str,
        key: str,
        max_labels: int = 50,
        min_confidence: float = 70.0
    ) -> VisionAnalysisResult:
        """
        Analyze image directly from S3.
        
        WHY: Rekognition supports S3 URIs directly - avoids downloading images.
        Saves bandwidth and latency.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            max_labels: Maximum number of labels to return
            min_confidence: Minimum confidence threshold
        
        Returns:
            VisionAnalysisResult
        
        Raises:
            VisionProviderError: If analysis fails
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """WHY: Audit trail - record which provider generated results"""
        pass

    @abstractmethod
    def get_model_version(self) -> str:
        """WHY: Different model versions may have different accuracy"""
        pass
