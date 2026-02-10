"""
Fallback Vision Provider

WHY: This wrapper implements a resilient vision provider that tries multiple 
backends in order of preference.

Strategy:
1. Try AWS Rekognition (primary - cost-effective for production)
2. Fallback to Gemini if AWS fails (backup - ensure reliability)

This ensures maximum uptime while minimizing costs.

Author: Srikanth Thiyagarajan
"""
import logging
from typing import Optional

from ...domain.ports import VisionProvider, VisionAnalysisResult

logger = logging.getLogger(__name__)


class FallbackVisionProvider(VisionProvider):
    """
    Vision provider that implements automatic fallback strategy.
    
    WHY: Single point of resilience - if primary provider fails,
    automatically try backup provider.
    
    Design decisions:
    - Transparent to consumers - looks like any other VisionProvider
    - Logs which provider was used for audit trail
    - Graceful degradation if all providers fail
    """

    def __init__(
        self,
        primary_provider: VisionProvider,
        fallback_provider: Optional[VisionProvider] = None
    ):
        """
        Initialize fallback vision provider.
        
        Args:
            primary_provider: Primary vision provider (e.g., Rekognition)
            fallback_provider: Fallback provider (e.g., Gemini)
        """
        self.primary = primary_provider
        self.fallback = fallback_provider
        
        logger.info(
            f"Initialized fallback provider: "
            f"primary={primary_provider.get_provider_name()}, "
            f"fallback={fallback_provider.get_provider_name() if fallback_provider else 'None'}"
        )

    async def analyze_image(
        self,
        image_bytes: bytes,
        max_labels: int = 50,
        min_confidence: float = 70.0
    ) -> VisionAnalysisResult:
        """
        Analyze image with automatic fallback.
        
        WHY: Try primary first (cheaper/faster), fallback if it fails.
        """
        # Try primary provider
        try:
            logger.info(f"Attempting analysis with primary provider: {self.primary.get_provider_name()}")
            result = await self.primary.analyze_image(image_bytes, max_labels, min_confidence)
            logger.info(f"✅ Primary provider succeeded: {self.primary.get_provider_name()}")
            return result
        
        except Exception as primary_error:
            logger.warning(
                f"❌ Primary provider failed: {self.primary.get_provider_name()}",
                extra={"error": str(primary_error)},
                exc_info=True
            )
            
            # Try fallback provider if available
            if self.fallback:
                try:
                    logger.info(f"🔄 Falling back to: {self.fallback.get_provider_name()}")
                    result = await self.fallback.analyze_image(image_bytes, max_labels, min_confidence)
                    logger.info(f"✅ Fallback provider succeeded: {self.fallback.get_provider_name()}")
                    return result
                
                except Exception as fallback_error:
                    logger.error(
                        f"❌ Fallback provider also failed: {self.fallback.get_provider_name()}",
                        extra={"error": str(fallback_error)},
                        exc_info=True
                    )
                    # Both failed - raise the fallback error
                    raise Exception(
                        f"All vision providers failed. "
                        f"Primary ({self.primary.get_provider_name()}): {str(primary_error)}. "
                        f"Fallback ({self.fallback.get_provider_name()}): {str(fallback_error)}"
                    )
            else:
                # No fallback available - re-raise primary error
                logger.error("❌ No fallback provider configured")
                raise primary_error

    async def analyze_image_from_s3(
        self,
        bucket: str,
        key: str,
        max_labels: int = 50,
        min_confidence: float = 70.0
    ) -> VisionAnalysisResult:
        """
        Analyze image from S3 with automatic fallback.
        
        WHY: Same fallback logic for S3-based analysis.
        """
        # Try primary provider
        try:
            logger.info(
                f"Attempting S3 analysis with primary provider: {self.primary.get_provider_name()}",
                extra={"bucket": bucket, "key": key}
            )
            result = await self.primary.analyze_image_from_s3(bucket, key, max_labels, min_confidence)
            logger.info(f"✅ Primary provider succeeded: {self.primary.get_provider_name()}")
            return result
        
        except Exception as primary_error:
            logger.warning(
                f"❌ Primary provider failed: {self.primary.get_provider_name()}",
                extra={"error": str(primary_error), "bucket": bucket, "key": key},
                exc_info=True
            )
            
            # Try fallback provider if available
            if self.fallback:
                try:
                    logger.info(f"🔄 Falling back to: {self.fallback.get_provider_name()}")
                    result = await self.fallback.analyze_image_from_s3(bucket, key, max_labels, min_confidence)
                    logger.info(f"✅ Fallback provider succeeded: {self.fallback.get_provider_name()}")
                    return result
                
                except Exception as fallback_error:
                    logger.error(
                        f"❌ Fallback provider also failed: {self.fallback.get_provider_name()}",
                        extra={"error": str(fallback_error)},
                        exc_info=True
                    )
                    # Both failed - raise combined error
                    raise Exception(
                        f"All vision providers failed. "
                        f"Primary ({self.primary.get_provider_name()}): {str(primary_error)}. "
                        f"Fallback ({self.fallback.get_provider_name()}): {str(fallback_error)}"
                    )
            else:
                # No fallback available - re-raise primary error
                logger.error("❌ No fallback provider configured")
                raise primary_error

    def get_provider_name(self) -> str:
        """
        WHY: Report as 'fallback' to indicate this is a composite provider.
        """
        return f"fallback({self.primary.get_provider_name()}->{self.fallback.get_provider_name() if self.fallback else 'none'})"

    def get_model_version(self) -> str:
        """
        WHY: Report primary model version by default.
        """
        return f"primary:{self.primary.get_model_version()}"
