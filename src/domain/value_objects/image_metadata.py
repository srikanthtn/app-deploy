"""
Image Metadata Value Object

WHY: Encapsulates all image-related metadata needed for audit traceability.
Ensures consistent structure across the domain.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class ImageMetadata:
    """
    Immutable metadata about analyzed images.
    
    WHY: Audit requirements demand complete traceability:
    - WHO uploaded the image (uploader_id)
    - WHEN it was captured (captured_at)
    - WHERE it's stored (s3_key)
    - WHICH dealer/checkpoint it belongs to
    """
    image_id: UUID
    dealer_id: str
    checkpoint_id: str
    s3_bucket: str
    s3_key: str
    uploader_id: str  # Mobile app user ID
    captured_at: datetime
    uploaded_at: datetime
    file_size_bytes: int
    content_type: str = "image/jpeg"
    width_px: Optional[int] = None
    height_px: Optional[int] = None

    def s3_uri(self) -> str:
        """WHY: Standardized S3 URI for logging and debugging"""
        return f"s3://{self.s3_bucket}/{self.s3_key}"

    def is_valid_for_analysis(self) -> bool:
        """
        Domain rule: Image must meet minimum requirements.
        
        WHY: Business rule to prevent analysis of invalid images.
        Saves Rekognition costs on obviously bad images.
        """
        # Max 15MB for Rekognition
        if self.file_size_bytes > 15 * 1024 * 1024:
            return False
        
        # Minimum resolution for meaningful analysis
        if self.width_px and self.height_px:
            if self.width_px < 640 or self.height_px < 480:
                return False
        
        return True

    def age_in_days(self, reference_time: datetime) -> int:
        """WHY: Audit retention policies may need this"""
        delta = reference_time - self.captured_at
        return delta.days
