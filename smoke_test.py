"""
Script to simulate a local API request manually.
Does NOT require running uvicorn server.
Directly invokes the FastAPI app instance using TestClient.
"""
import sys
import os

# Add local src to path to ensure imports work
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from fastapi.testclient import TestClient
from src.main import app
from src.api.dependencies import get_vision_provider, get_storage_provider
from unittest.mock import MagicMock, AsyncMock
from src.domain.ports import VisionAnalysisResult, VisionLabel, StorageMetadata
from src.domain.value_objects import ConfidenceScore

def main():
    print("🚀 Starting manual integration test...")
    
    client = TestClient(app)
    
    # Mock the Vision Provider
    mock_vision = MagicMock()
    mock_vision.analyze_image_from_s3 = AsyncMock(return_value=VisionAnalysisResult(
        labels=[
            VisionLabel(name="Clean Room", confidence=ConfidenceScore(95.0)),
            VisionLabel(name="Organized", confidence=ConfidenceScore(90.0))
        ],
        provider_name="mock-rekognition",
        model_version="test"
    ))
    mock_vision.get_provider_name.return_value = "mock"
    
    # Mock the Storage Provider
    mock_storage = MagicMock()
    # Async methods must be awaited, so use AsyncMock if possible or return a future
    # However, since we're mocking the interface, let's just make the return value a coroutine or use AsyncMock
    mock_storage.upload_image = AsyncMock(return_value=StorageMetadata(
        bucket="test-bucket",
        key="test-key",
        size_bytes=1024
    ))
    
    # Override dependencies
    app.dependency_overrides[get_vision_provider] = lambda: mock_vision
    app.dependency_overrides[get_storage_provider] = lambda: mock_storage
    print("✅ Mocked Vision and Storage Providers injected.")

    # Create dummy image
    dummy_image = b"fake image bytes"
    
    print("📤 Sending POST /api/v1/hygiene/analyze...")
    response = client.post(
        "/api/v1/hygiene/analyze",
        headers={"Authorization": "Bearer valid-token"},
        data={
            "dealer_id": "DEALER-MANUAL-TEST",
            "checkpoint_id": "TEST-LOCATION",
            "min_confidence": 75.0
        },
        files={"image": ("manual_test.jpg", dummy_image, "image/jpeg")}
    )
    
    if response.status_code == 201:
        print("✅ SUCCESS! API returned 201 Created")
        print("Response JSON:")
        print(response.json())
    else:
        print(f"❌ FAILED. Status Code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()
