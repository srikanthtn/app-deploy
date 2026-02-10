"""
Gemini Vision Adapter

WHY: This is an ADAPTER in Hexagonal Architecture.
It implements the VisionProvider port using Google Gemini Vision API.

Key principles:
1. Implements domain interface (VisionProvider)
2. Translates Gemini responses to domain objects
3. Handles Gemini-specific errors and retries
4. Contains NO business logic

Author: Srikanth Thiyagarajan
"""
import logging
from typing import List, Optional
import os
import io
import time
import json
from PIL import Image
from google import genai
from google.genai import types

from ...domain.ports import VisionProvider, VisionAnalysisResult, VisionLabel
from ...domain.value_objects import ConfidenceScore

logger = logging.getLogger(__name__)


class GeminiError(Exception):
    """Raised when Gemini API fails"""
    pass


class GeminiAdapter(VisionProvider):
    """
    Google Gemini Vision implementation of VisionProvider.
    
    WHY: Adapter pattern - adapts Gemini API to domain interface.
    
    Design decisions:
    - Uses google-genai client for Gemini 2.5 Flash
    - Async wrapper around sync Gemini client
    - Comprehensive error handling with retries for quota errors
    - Structured logging for observability
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash-exp",
        max_retries: int = 3
    ):
        """
        Initialize Gemini client.
        
        WHY: Configurable API key and model for flexibility.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model: Gemini model to use
            max_retries: Number of retry attempts for quota errors
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise GeminiError("GEMINI_API_KEY environment variable not set")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model = model
        self.max_retries = max_retries
        
        logger.info(f"Initialized Gemini adapter with model {model}")

    async def analyze_image(
        self,
        image_bytes: bytes,
        max_labels: int = 50,
        min_confidence: float = 70.0
    ) -> VisionAnalysisResult:
        """
        Analyze image from raw bytes.
        
        WHY async: Even though Gemini client is sync, we wrap in async for consistency
        with application layer.
        """
        try:
            logger.info(
                "Analyzing image with Gemini",
                extra={
                    "size_bytes": len(image_bytes),
                    "model": self.model,
                    "min_confidence": min_confidence
                }
            )
            
            # Convert bytes to PIL Image for Gemini
            image_pil = Image.open(io.BytesIO(image_bytes))
            
            # WHY: Gemini uses a classification prompt to determine cleanliness
            result = self._classify_with_retry(image_pil, min_confidence)
            
            return self._parse_response(result, min_confidence)
        
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}", exc_info=True)
            raise GeminiError(f"Gemini analysis failed: {str(e)}")

    async def analyze_image_from_s3(
        self,
        bucket: str,
        key: str,
        max_labels: int = 50,
        min_confidence: float = 70.0
    ) -> VisionAnalysisResult:
        """
        Analyze image from S3.
        
        WHY: Gemini doesn't support direct S3 access, so we download first.
        This is less efficient than Rekognition's S3 integration.
        """
        try:
            logger.info(
                "Downloading image from S3 for Gemini analysis",
                extra={"bucket": bucket, "key": key}
            )
            
            # Download from S3
            import boto3
            s3_client = boto3.client('s3')
            response = s3_client.get_object(Bucket=bucket, Key=key)
            image_bytes = response['Body'].read()
            
            # Delegate to analyze_image
            return await self.analyze_image(image_bytes, max_labels, min_confidence)
        
        except Exception as e:
            logger.error(f"S3 download error for Gemini: {str(e)}", exc_info=True)
            raise GeminiError(f"Failed to download from S3: {str(e)}")

    def _classify_with_retry(self, image_pil: Image.Image, min_confidence: float) -> dict:
        """
        Classify image with retry logic for quota errors.
        
        WHY: Gemini has rate limits - retry on 429 errors.
        """
        clean_indicators = [
            "clean floor", "showroom", "organized", "polished surface", 
            "clear space", "vehicle showroom", "tidy", "pristine"
        ]
        messy_indicators = [
            "trash", "clutter", "dirt", "stain", "garbage", "spill", 
            "damaged floor", "debris", "untidy", "disorganized"
        ]

        prompt = f"""
        Analyze this image for cleanliness. Is it 'Clean' or 'Messy'?
        
        Clean criteria: {', '.join(clean_indicators)}
        Messy criteria: {', '.join(messy_indicators)}
        
        Return JSON with this exact structure:
        {{
            "classification": "Clean"|"Messy",
            "confidence": 0.0-1.0,
            "reasoning": "Brief explanation",
            "detected_items": ["item1", "item2", ...]
        }}
        
        Be thorough in identifying all relevant items that indicate cleanliness or messiness.
        """

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[prompt, image_pil],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                return json.loads(response.text)
            
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    if attempt < self.max_retries:
                        wait_time = 5 * (attempt + 1)  # 5s, 10s, 15s
                        logger.warning(
                            f"Quota exceeded. Waiting {wait_time}s before retry {attempt + 1}/{self.max_retries}..."
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        raise GeminiError(
                            f"Quota exceeded after {self.max_retries} retries. Please try again later."
                        )
                else:
                    # Non-retriable error
                    raise e

    def _parse_response(self, result: dict, min_confidence: float) -> VisionAnalysisResult:
        """
        Parse Gemini response into domain object.
        
        WHY: Anti-corruption layer - translate Gemini format to domain format.
        Domain layer never sees Gemini response structure.
        
        Gemini response format:
        {
            "classification": "Clean"|"Messy",
            "confidence": 0.0-1.0,
            "reasoning": "...",
            "detected_items": [...]
        }
        """
        classification = result.get("classification", "Unknown")
        confidence = result.get("confidence", 0.0)
        detected_items = result.get("detected_items", [])
        reasoning = result.get("reasoning", "")
        
        # WHY: Convert confidence from 0-1 to 0-100 for consistency with Rekognition
        confidence_score = confidence * 100.0
        
        # Create primary classification label
        labels = [
            VisionLabel(
                name=classification,
                confidence=ConfidenceScore(confidence_score),
                category="cleanliness"
            )
        ]
        
        # Add detected items as additional labels
        # WHY: Provide granular information like Rekognition does
        for item in detected_items:
            if confidence_score >= min_confidence:
                labels.append(
                    VisionLabel(
                        name=item,
                        confidence=ConfidenceScore(confidence_score * 0.9),  # Slightly lower confidence for sub-items
                        category="detected_item"
                    )
                )
        
        logger.info(
            f"Gemini classification: {classification} ({confidence_score:.1f}% confidence)",
            extra={"detected_items": detected_items, "reasoning": reasoning}
        )
        
        return VisionAnalysisResult(
            labels=labels,
            provider_name="gemini",
            model_version=self.model,
            processing_time_ms=0  # Gemini doesn't report this
        )

    def get_provider_name(self) -> str:
        """WHY: Audit trail - which provider generated this result"""
        return "gemini"

    def get_model_version(self) -> str:
        """
        WHY: Gemini model version affects accuracy.
        Important for debugging and A/B testing.
        """
        return self.model
