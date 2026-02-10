"""
Unit Tests for CleanlinessEvaluator

WHY: Domain layer tests have ZERO external dependencies.
No AWS, no database, no network - pure business logic testing.

This demonstrates the power of Clean Architecture:
- Tests run instantly
- No mocks needed for infrastructure
- Test business rules in isolation
"""
import pytest
from src.domain.services import CleanlinessEvaluator, CleanlinessRules
from src.domain.value_objects import CleanlinessStatus, ConfidenceScore, ImageMetadata
from src.domain.ports import VisionAnalysisResult, VisionLabel
from datetime import datetime
from uuid import uuid4


class TestCleanlinessEvaluator:
    """
    Test suite for domain service.
    
    WHY: These tests validate BUSINESS LOGIC, not infrastructure.
    """
    
    def setup_method(self):
        """Setup test fixtures"""
        self.rules = CleanlinessRules(
            confidence_threshold=80.0,
            max_negative_labels=0
        )
        self.evaluator = CleanlinessEvaluator(rules=self.rules)
        
        self.image_metadata = ImageMetadata(
            image_id=uuid4(),
            dealer_id="dealer-001",
            checkpoint_id="reception",
            s3_bucket="test-bucket",
            s3_key="test/image.jpg",
            uploader_id="user-123",
            captured_at=datetime.utcnow(),
            uploaded_at=datetime.utcnow(),
            file_size_bytes=1024000
        )
    
    def test_clean_facility_with_no_negative_labels(self):
        """
        GIVEN: Image with only positive labels and high confidence
        WHEN: Evaluator analyzes it
        THEN: Status should be CLEAN
        
        WHY: Business rule - no issues = clean
        """
        vision_result = VisionAnalysisResult(
            labels=[
                VisionLabel(name="Clean Room", confidence=ConfidenceScore(95.0)),
                VisionLabel(name="Organized", confidence=ConfidenceScore(92.0)),
                VisionLabel(name="Modern", confidence=ConfidenceScore(88.0)),
            ],
            provider_name="rekognition",
            model_version="3.0"
        )
        
        result = self.evaluator.evaluate(vision_result, self.image_metadata)
        
        assert result.status == CleanlinessStatus.CLEAN
        assert len(result.negative_labels) == 0
        assert result.overall_confidence.value > 80.0
    
    def test_not_clean_with_dirt_detected(self):
        """
        GIVEN: Image with "Dirt" label detected
        WHEN: Evaluator analyzes it
        THEN: Status should be NOT_CLEAN
        
        WHY: Business rule - "Dirt" is a negative label
        """
        vision_result = VisionAnalysisResult(
            labels=[
                VisionLabel(name="Dirt", confidence=ConfidenceScore(85.0)),
                VisionLabel(name="Floor", confidence=ConfidenceScore(95.0)),
            ],
            provider_name="rekognition",
            model_version="3.0"
        )
        
        result = self.evaluator.evaluate(vision_result, self.image_metadata)
        
        assert result.status == CleanlinessStatus.NOT_CLEAN
        assert len(result.negative_labels) == 1
        assert result.negative_labels[0].name == "Dirt"
    
    def test_manual_review_on_low_confidence(self):
        """
        GIVEN: Image with low confidence (below threshold)
        WHEN: Evaluator analyzes it
        THEN: Status should be REQUIRES_MANUAL_REVIEW
        
        WHY: Business rule - uncertain results need human review
        """
        vision_result = VisionAnalysisResult(
            labels=[
                VisionLabel(name="Indoor", confidence=ConfidenceScore(60.0)),
                VisionLabel(name="Room", confidence=ConfidenceScore(55.0)),
            ],
            provider_name="rekognition",
            model_version="3.0"
        )
        
        result = self.evaluator.evaluate(vision_result, self.image_metadata)
        
        assert result.status == CleanlinessStatus.REQUIRES_MANUAL_REVIEW
        assert result.overall_confidence.value < 80.0
    
    def test_manual_override_clean(self):
        """
        GIVEN: Image with dirt detected BUT manual override says clean
        WHEN: Evaluator analyzes it with override
        THEN: Status should be CLEAN (override wins)
        
        WHY: Business rule - humans override AI
        """
        vision_result = VisionAnalysisResult(
            labels=[
                VisionLabel(name="Dirt", confidence=ConfidenceScore(85.0)),
            ],
            provider_name="rekognition",
            model_version="3.0"
        )
        
        result = self.evaluator.evaluate(
            vision_result,
            self.image_metadata,
            manual_override=True
        )
        
        assert result.status == CleanlinessStatus.CLEAN
        assert result.manual_override is True
    
    def test_multiple_negative_labels(self):
        """
        GIVEN: Image with multiple negative indicators
        WHEN: Evaluator analyzes it
        THEN: All negative labels should be identified for explainability
        
        WHY: Auditors need to know ALL issues, not just one
        """
        vision_result = VisionAnalysisResult(
            labels=[
                VisionLabel(name="Dirt", confidence=ConfidenceScore(85.0)),
                VisionLabel(name="Trash", confidence=ConfidenceScore(82.0)),
                VisionLabel(name="Stain", confidence=ConfidenceScore(78.0)),
                VisionLabel(name="Floor", confidence=ConfidenceScore(95.0)),
            ],
            provider_name="rekognition",
            model_version="3.0"
        )
        
        result = self.evaluator.evaluate(vision_result, self.image_metadata)
        
        assert result.status == CleanlinessStatus.NOT_CLEAN
        assert len(result.negative_labels) == 3
        negative_names = {label.name for label in result.negative_labels}
        assert negative_names == {"Dirt", "Trash", "Stain"}


# WHY: Demonstrates test execution
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
