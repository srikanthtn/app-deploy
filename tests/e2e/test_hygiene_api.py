"""
End-to-End API Test for Hygiene Analysis

WHY: Tests the full stack from API -> Application -> Domain -> Infrastructure.
Uses TestClient (no real network) and mocked Repository/S3.
"""
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import pytest
from src.main import app
from src.api.dependencies import get_vision_provider, get_audit_repository
from src.application.use_cases.analyze_cleanliness import AnalyzeCleanlinessUseCase
from src.domain.value_objects import ConfidenceScore, VisionLabel
from src.domain.ports import VisionAnalysisResult

client = TestClient(app)

# Mock image file
TEST_IMAGE = Path(__file__).parent / "fixtures" / "test_image.jpg"

@pytest.fixture
def mock_vision():
    """Mock vision provider to avoid AWS calls"""
    mock = MagicMock()
    # Configure mock to return a CLEAN result
    mock.analyze_image_from_s3.return_value = VisionAnalysisResult(
        labels=[
            VisionLabel(name="Clean Room", confidence=ConfidenceScore(95.0)),
            VisionLabel(name="Organized", confidence=ConfidenceScore(90.0))
        ],
        provider_name="mock-rekognition",
        model_version="test"
    )
    mock.get_provider_name.return_value = "mock"
    return mock

def test_analyze_cleanliness_endpoint(mock_vision, tmp_path):
    """
    Test POST /analyze endpoint success path.
    """
    # Create valid dummy image
    image_path = tmp_path / "test.jpg"
    image_path.write_bytes(b"fake image data")

    # Dependency Override: Inject mock vision provider
    app.dependency_overrides[get_vision_provider] = lambda: mock_vision
    
    # We use the real InMemoryRepository (default) so no need to mock repository
    
    with open(image_path, "rb") as f:
        response = client.post(
            "/api/v1/hygiene/analyze",
            data={
                "dealer_id": "dealer-test",
                "checkpoint_id": "reception",
                "min_confidence": 70.0
            },
            files={"image": ("test.jpg", f, "image/jpeg")}
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "CLEAN"
    assert data["dealer_id"] == "dealer-test"
    assert "audit_id" in data

    # Verify IDempotency / Persistence
    # GET /audits/{id} (Not fully implemented in routes yet but good to have test ready)
    # get_response = client.get(f"/audits/{data['audit_id']}")
    # assert get_response.status_code == 404  # As per implementation stub

# Clean up overrides
app.dependency_overrides = {}
