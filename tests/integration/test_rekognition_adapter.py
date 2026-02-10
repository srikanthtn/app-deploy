"""
Integration Test for Rekognition Adapter

WHY: Integration tests verify infrastructure adapters work with real AWS services.

Setup: Uses moto to mock AWS services (no real API calls).
"""
import pytest
from moto import mock_rekognition, mock_s3
import boto3
from src.infrastructure.vision.rekognition_adapter import RekognitionAdapter
from src.domain.value_objects import ConfidenceScore


@pytest.fixture
def mock_aws():
    """
    Setup mock AWS environment.
    
    WHY: moto provides in-memory AWS service mocks.
    Tests run without AWS credentials or network calls.
    """
    with mock_rekognition(), mock_s3():
        yield


@pytest.fixture
def sample_image_bytes():
    """
    Generate minimal valid JPEG.
    
    WHY: moto's Rekognition mock accepts any bytes.
    In real tests, use actual test images.
    """
    # Minimal JPEG header
    return bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"test image data"


@pytest.mark.asyncio
class TestRekognitionAdapter:
    """
    Test AWS Rekognition adapter.
    
    WHY: Verify adapter correctly translates AWS responses to domain objects.
    """
    
    async def test_analyze_image_from_bytes(self, mock_aws, sample_image_bytes):
        """
        GIVEN: Mock Rekognition service and image bytes
        WHEN: Adapter analyzes image
        THEN: Returns VisionAnalysisResult with labels
        
        WHY: Verify basic adapter functionality
        """
        adapter = RekognitionAdapter(region_name="us-east-1")
        
        result = await adapter.analyze_image(sample_image_bytes)
        
        assert result.provider_name == "rekognition"
        assert isinstance(result.labels, list)
        # moto returns canned responses with multiple labels
        assert len(result.labels) > 0
    
    async def test_analyze_image_from_s3(self, mock_aws, sample_image_bytes):
        """
        GIVEN: Mock S3 bucket with image
        WHEN: Adapter analyzes via S3 URI
        THEN: Returns analysis results
        
        WHY: Verify S3 integration path (preferred for production)
        """
        # Setup mock S3
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket = "test-bucket"
        key = "test/image.jpg"
        
        s3_client.create_bucket(Bucket=bucket)
        s3_client.put_object(Bucket=bucket, Key=key, Body=sample_image_bytes)
        
        # Test adapter
        adapter = RekognitionAdapter(region_name="us-east-1")
        result = await adapter.analyze_image_from_s3(bucket, key)
        
        assert result.provider_name == "rekognition"
        assert len(result.labels) > 0
    
    async def test_confidence_score_conversion(self, mock_aws, sample_image_bytes):
        """
        GIVEN: Rekognition returns labels with confidence scores
        WHEN: Adapter parses response
        THEN: Confidence scores are domain ConfidenceScore objects
        
        WHY: Verify anti-corruption layer translates AWS types to domain types
        """
        adapter = RekognitionAdapter(region_name="us-east-1")
        result = await adapter.analyze_image(sample_image_bytes)
        
        for label in result.labels:
            assert isinstance(label.confidence, ConfidenceScore)
            assert 0.0 <= label.confidence.value <= 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
