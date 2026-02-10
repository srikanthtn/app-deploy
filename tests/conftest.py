"""Test configuration and shared fixtures"""
import pytest
from pathlib import Path


@pytest.fixture
def sample_image_bytes():
    """
    Load sample test image.
    
    WHY: Consistent test data across all test files.
    """
    # In production, add actual test images
    # For now, return minimal JPEG
    return bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"JFIF" + b"\x00" * 100


@pytest.fixture
def test_data_dir():
    """Path to test data directory"""
    return Path(__file__).parent / "fixtures"
