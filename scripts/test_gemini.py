"""
Test Gemini Adapter

WHY: Verify Gemini adapter works independently before testing fallback.

Usage:
    python scripts/test_gemini.py path/to/test/image.jpg

Author: Srikanth Thiyagarajan
"""
import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from src.infrastructure.vision.gemini_adapter import GeminiAdapter


async def test_gemini(image_path: str):
    """Test Gemini adapter with a sample image."""
    print("🧪 Testing Gemini Adapter")
    print("=" * 50)
    
    # Verify API key is set
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set in .env file")
        print("Please add: GEMINI_API_KEY=your_api_key_here")
        return False
    
    print(f"✅ GEMINI_API_KEY found: {api_key[:10]}...")
    
    # Load test image
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return False
    
    print(f"📷 Loading image: {image_path}")
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    print(f"✅ Image loaded: {len(image_bytes)} bytes")
    
    # Create adapter
    try:
        adapter = GeminiAdapter()
        print(f"✅ Gemini adapter initialized: {adapter.get_provider_name()}")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini adapter: {e}")
        return False
    
    # Test analysis
    try:
        print("\n🔍 Analyzing image with Gemini...")
        result = await adapter.analyze_image(
            image_bytes=image_bytes,
            min_confidence=70.0
        )
        
        print("\n✅ Analysis complete!")
        print(f"Provider: {result.provider_name}")
        print(f"Model: {result.model_version}")
        print(f"Labels found: {len(result.labels)}")
        
        print("\n📊 Detected Labels:")
        for label in result.labels[:10]:  # Show top 10
            print(f"  - {label.name}: {label.confidence.value:.1f}% ({label.category})")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_gemini.py path/to/image.jpg")
        print("\nExample:")
        print("  python scripts/test_gemini.py test_images/clean_floor.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    success = asyncio.run(test_gemini(image_path))
    
    if success:
        print("\n✅ Test passed!")
        sys.exit(0)
    else:
        print("\n❌ Test failed!")
        sys.exit(1)
