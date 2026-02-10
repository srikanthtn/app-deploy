"""
Amazon Rekognition Adapter

WHY: This is an ADAPTER in Hexagonal Architecture.
It implements the VisionProvider port using AWS Rekognition.

Key principles:
1. Implements domain interface (VisionProvider)
2. Translates Rekognition responses to domain objects
3. Handles AWS-specific errors and retries
4. Contains NO business logic
"""
import logging
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError

from ...domain.ports import VisionProvider, VisionAnalysisResult, VisionLabel
from ...domain.value_objects import ConfidenceScore

logger = logging.getLogger(__name__)


class RekognitionError(Exception):
    """Raised when Rekognition API fails"""
    pass


class RekognitionAdapter(VisionProvider):
    """
    AWS Rekognition implementation of VisionProvider.
    
    WHY: Adapter pattern - adapts AWS Rekognition API to domain interface.
    
    Design decisions:
    - Uses boto3 client (not resource) for fine-grained control
    - Async wrapper around boto3 (boto3 is sync, we make it async)
    - Comprehensive error handling
    - Structured logging for observability
    """

    def __init__(
        self,
        region_name: str = "us-east-1",
        max_retries: int = 3,
        timeout_seconds: int = 30
    ):
        """
        Initialize Rekognition client.
        
        WHY: Configurable region/retries for multi-region deployments.
        
        Args:
            region_name: AWS region for Rekognition
            max_retries: Number of retry attempts
            timeout_seconds: Request timeout
        """
        self.region_name = region_name
        self.max_retries = max_retries
        
        # WHY: Using config for fine-grained control over retries and timeouts
        from botocore.config import Config
        config = Config(
            region_name=region_name,
            retries={'max_attempts': max_retries, 'mode': 'adaptive'},
            connect_timeout=timeout_seconds,
            read_timeout=timeout_seconds,
        )
        
        self.client = boto3.client('rekognition', config=config)
        logger.info(f"Initialized Rekognition adapter for region {region_name}")

    async def analyze_image(
        self,
        image_bytes: bytes,
        max_labels: int = 50,
        min_confidence: float = 70.0
    ) -> VisionAnalysisResult:
        """
        Analyze image from raw bytes.
        
        WHY async: Even though boto3 is sync, we wrap in async for consistency
        with application layer. In production, use aioboto3 for true async.
        """
        try:
            logger.info(
                "Analyzing image from bytes",
                extra={
                    "size_bytes": len(image_bytes),
                    "max_labels": max_labels,
                    "min_confidence": min_confidence
                }
            )
            
            # WHY: detect_labels is Rekognition's general object/scene detection API
            response = self.client.detect_labels(
                Image={'Bytes': image_bytes},
                MaxLabels=max_labels,
                MinConfidence=min_confidence,
                # WHY: Include image properties for quality assessment
                Features=['GENERAL_LABELS', 'IMAGE_PROPERTIES']
            )
            
            return self._parse_response(response)
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Rekognition API error: {error_code}", exc_info=True)
            
            # WHY: Translate AWS errors to domain errors
            if error_code == 'InvalidImageFormatException':
                raise RekognitionError("Invalid image format - must be JPEG or PNG")
            elif error_code == 'ImageTooLargeException':
                raise RekognitionError("Image too large - maximum 15MB")
            elif error_code == 'ThrottlingException':
                raise RekognitionError("Rate limited - try again later")
            else:
                raise RekognitionError(f"Rekognition error: {error_code}")
        
        except BotoCoreError as e:
            logger.error("Boto core error", exc_info=True)
            raise RekognitionError(f"AWS SDK error: {str(e)}")

    async def analyze_image_from_s3(
        self,
        bucket: str,
        key: str,
        max_labels: int = 50,
        min_confidence: float = 70.0
    ) -> VisionAnalysisResult:
        """
        Analyze image directly from S3.
        
        WHY: Rekognition can read directly from S3 - saves bandwidth and latency.
        No need to download image to Lambda/ECS container.
        
        IMPORTANT: Rekognition and S3 bucket must be in same region.
        """
        try:
            logger.info(
                "Analyzing image from S3",
                extra={
                    "bucket": bucket,
                    "key": key,
                    "max_labels": max_labels,
                    "min_confidence": min_confidence
                }
            )
            
            response = self.client.detect_labels(
                Image={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                },
                MaxLabels=max_labels,
                MinConfidence=min_confidence,
                Features=['GENERAL_LABELS', 'IMAGE_PROPERTIES']
            )
            
            return self._parse_response(response)
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Rekognition S3 error: {error_code}", exc_info=True)
            
            if error_code == 'AccessDeniedException':
                raise RekognitionError(
                    f"Rekognition cannot access s3://{bucket}/{key} - check IAM policy"
                )
            else:
                raise RekognitionError(f"Rekognition error: {error_code}")

    def _parse_response(self, response: dict) -> VisionAnalysisResult:
        """
        Parse Rekognition response into domain object.
        
        WHY: Anti-corruption layer - translate AWS format to domain format.
        Domain layer never sees AWS response structure.
        
        Rekognition response format:
        {
            'Labels': [
                {
                    'Name': 'Person',
                    'Confidence': 99.5,
                    'Instances': [...],
                    'Parents': [...]
                }
            ],
            'LabelModelVersion': '3.0'
        }
        """
        labels = [
            VisionLabel(
                name=label['Name'],
                confidence=ConfidenceScore.from_rekognition(label['Confidence']),
                category=self._determine_category(label)
            )
            for label in response.get('Labels', [])
        ]
        
        model_version = response.get('LabelModelVersion', 'unknown')
        
        logger.info(f"Detected {len(labels)} labels using model {model_version}")
        
        return VisionAnalysisResult(
            labels=labels,
            provider_name="rekognition",
            model_version=model_version,
            processing_time_ms=0  # Rekognition doesn't report this
        )

    def _determine_category(self, label: dict) -> str:
        """
        Categorize labels for better organization.
        
        WHY: Rekognition doesn't categorize labels - we add business context.
        """
        # WHY: Check parent labels to infer category
        parents = [p['Name'] for p in label.get('Parents', [])]
        
        if 'Person' in parents or label['Name'] == 'Person':
            return 'people'
        elif 'Vehicle' in parents:
            return 'vehicles'
        elif 'Furniture' in parents or 'Indoor' in parents:
            return 'indoor'
        elif 'Outdoor' in parents:
            return 'outdoor'
        else:
            return 'general'

    def get_provider_name(self) -> str:
        """WHY: Audit trail - which provider generated this result"""
        return "rekognition"

    def get_model_version(self) -> str:
        """
        WHY: Rekognition model version affects accuracy.
        Important for debugging and A/B testing.
        """
        return "latest"  # Rekognition uses latest by default
