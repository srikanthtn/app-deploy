"""
Analyze Cleanliness Use Case

WHY: This is an APPLICATION SERVICE (Use Case) in Clean Architecture.

Key responsibilities:
1. Orchestrate domain objects and infrastructure
2. Define transaction boundaries
3. Coordinate multiple operations
4. NO business logic (that's in domain layer)

This is the Command pattern - each use case is a command.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import uuid4

from ...domain.entities import AuditResult
from ...domain.services import CleanlinessEvaluator, CleanlinessRules
from ...domain.ports import VisionProvider, StorageProvider, AuditRepository
from ...domain.value_objects import ImageMetadata

logger = logging.getLogger(__name__)


@dataclass
class AnalyzeCleanlinessCommand:
    """
    Command DTO for cleanliness analysis.
    
    WHY: Encapsulates all input parameters.
    This is the "request" object for the use case.
    """
    dealer_id: str
    checkpoint_id: str
    uploader_id: str
    image_bytes: bytes
    content_type: str = "image/jpeg"
    
    # Optional overrides
    min_confidence: float = 70.0
    max_labels: int = 50
    manual_override: Optional[bool] = None
    
    # Custom rules (if dealer has special requirements)
    custom_rules: Optional[CleanlinessRules] = None


class AnalyzeCleanlinessUseCase:
    """
    Use Case: Analyze facility image for cleanliness compliance.
    
    WHY: Application service that orchestrates:
    1. Storage (upload image to S3)
    2. Vision (analyze with Rekognition)
    3. Domain (evaluate cleanliness)
    4. Persistence (save audit result)
    
    Design: Constructor injection for dependencies.
    WHY: Enables testing with mocks.
    """

    def __init__(
        self,
        vision_provider: VisionProvider,
        storage_provider: StorageProvider,
        audit_repository: AuditRepository,
        default_bucket: str,
        default_rules: Optional[CleanlinessRules] = None
    ):
        """
        Initialize use case with dependencies.
        
        WHY: Dependencies injected, not created.
        This follows Dependency Inversion Principle.
        
        Args:
            vision_provider: Strategy for vision analysis
            storage_provider: Strategy for storage
            audit_repository: Repository for persistence
            default_bucket: S3 bucket for images
            default_rules: Default cleanliness rules
        """
        self.vision_provider = vision_provider
        self.storage_provider = storage_provider
        self.audit_repository = audit_repository
        self.default_bucket = default_bucket
        self.default_rules = default_rules or CleanlinessRules()
        
        logger.info(
            f"Initialized AnalyzeCleanlinessUseCase with "
            f"provider={vision_provider.get_provider_name()}"
        )

    async def execute(self, command: AnalyzeCleanlinessCommand) -> AuditResult:
        """
        Execute the use case.
        
        WHY: This is the orchestration logic - the "application flow".
        
        Flow:
        1. Generate metadata
        2. Upload image to S3
        3. Analyze with vision provider
        4. Evaluate cleanliness (domain service)
        5. Save audit result
        6. Return result
        
        All steps logged for observability.
        
        Args:
            command: Input parameters
        
        Returns:
            Complete AuditResult
        
        Raises:
            Various infrastructure errors (S3Error, RekognitionError, etc)
        """
        correlation_id = str(uuid4())
        
        logger.info(
            "Starting cleanliness analysis",
            extra={
                "correlation_id": correlation_id,
                "dealer_id": command.dealer_id,
                "checkpoint_id": command.checkpoint_id,
                "uploader_id": command.uploader_id
            }
        )
        
        try:
            # Step 1: Create image metadata
            image_id = uuid4()
            now = datetime.utcnow()
            
            # WHY: Build S3 key using consistent structure
            s3_key = f"{command.dealer_id}/{command.checkpoint_id}/{now.strftime('%Y%m%d_%H%M%S')}_{image_id}.jpg"
            
            image_metadata = ImageMetadata(
                image_id=image_id,
                dealer_id=command.dealer_id,
                checkpoint_id=command.checkpoint_id,
                s3_bucket=self.default_bucket,
                s3_key=s3_key,
                uploader_id=command.uploader_id,
                captured_at=now,  # Assuming image captured now (could be passed in command)
                uploaded_at=now,
                file_size_bytes=len(command.image_bytes),
                content_type=command.content_type
            )
            
            logger.debug(f"Created image metadata: {image_metadata.s3_uri()}")
            
            # Step 2: Upload to S3
            storage_metadata = await self.storage_provider.upload_image(
                image_bytes=command.image_bytes,
                destination_key=s3_key,
                content_type=command.content_type,
                metadata={
                    "dealer_id": command.dealer_id,
                    "checkpoint_id": command.checkpoint_id,
                    "uploader_id": command.uploader_id,
                    "correlation_id": correlation_id
                }
            )
            
            logger.info(f"Uploaded image: {storage_metadata.size_bytes} bytes")
            
            # Step 3: Analyze with vision provider
            # WHY: Use S3 URI for Rekognition - faster and cheaper than uploading bytes
            vision_result = await self.vision_provider.analyze_image_from_s3(
                bucket=self.default_bucket,
                key=s3_key,
                max_labels=command.max_labels,
                min_confidence=command.min_confidence
            )
            
            logger.info(f"Vision analysis complete: {len(vision_result.labels)} labels detected")
            
            # Step 4: Evaluate cleanliness (DOMAIN LOGIC)
            rules = command.custom_rules or self.default_rules
            evaluator = CleanlinessEvaluator(rules=rules)
            
            audit_result = evaluator.evaluate(
                vision_result=vision_result,
                image_metadata=image_metadata,
                manual_override=command.manual_override
            )
            
            logger.info(
                f"Cleanliness evaluation: {audit_result.status.value}",
                extra={
                    "status": audit_result.status.value,
                    "confidence": audit_result.overall_confidence.value,
                    "negative_labels_count": len(audit_result.negative_labels)
                }
            )
            
            # Step 5: Persist audit result
            await self.audit_repository.save(audit_result)
            
            logger.info(f"Saved audit result: {audit_result.audit_id}")
            
            # Step 6: Return result
            return audit_result
        
        except Exception as e:
            logger.error(
                f"Cleanliness analysis failed: {str(e)}",
                extra={"correlation_id": correlation_id},
                exc_info=True
            )
            # WHY: Re-raise - let API layer handle error responses
            raise


# WHY: Optional - background processing version for async workflows
class AnalyzeCleanlinessAsyncUseCase(AnalyzeCleanlinessUseCase):
    """
    Variant: Queue-based async processing.
    
    WHY: For high-volume scenarios:
    1. API returns immediately with job ID
    2. Worker processes analysis asynchronously
    3. Client polls for results
    
    Implementation: Publish to SQS/SNS instead of executing synchronously.
    """
    
    async def execute(self, command: AnalyzeCleanlinessCommand) -> str:
        """
        Queue analysis job and return job ID.
        
        WHY: Decouple API response from processing time.
        Enables better scalability and fault tolerance.
        
        Returns:
            Job ID (correlation ID) for status polling
        """
        # Implementation: Publish command to SQS
        # Return correlation ID
        # Separate worker consumes queue and runs parent execute()
        pass
