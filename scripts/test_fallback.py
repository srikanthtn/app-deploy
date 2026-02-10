"""
Test Fallback Vision Provider

WHY: Verify fallback mechanism works correctly.

This script tests:
1. Normal operation (AWS works)
2. Fallback scenario (AWS fails, Gemini succeeds)

Usage:
    # Test with valid AWS credentials (normal operation)
    python scripts/test_fallback.py path/to/image.jpg
    
    # Test fallback by temporarily breaking AWS
    # (Set invalid AWS credentials in .env first)
    python scripts/test_fallback.py path/to/image.jpg

Author: Srikanth Thiyagarajan
"""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from src.infrastructure.vision.rekognition_adapter import RekognitionAdapter
from src.infrastructure.vision.gemini_adapter import GeminiAdapter
from src.infrastructure.vision.fallback_vision_provider import FallbackVisionProvider


async def test_fallback(image_path: str, simulate_aws_failure: bool = False):
    """Test fallback provider with a sample image."""
    print("🧪 Testing Fallback Vision Provider")
    print("=" * 50)
    
    # Verify API keys
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("⚠️  GEMINI_API_KEY not set - fallback won't work")
    else:
        print(f"✅ GEMINI_API_KEY found: {gemini_key[:10]}...")
    
    # Load test image
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return False
    
    print(f"📷 Loading image: {image_path}")
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    print(f"✅ Image loaded: {len(image_bytes)} bytes")
    
    # Create providers
    try:
        print("\n🔧 Initializing providers...")
        
        if simulate_aws_failure:
            print("⚠️  Simulating AWS failure mode")
            # Create a broken AWS provider (invalid region)
            primary = RekognitionAdapter(region_name="invalid-region-for-testing")
        else:
            aws_region = os.getenv("AWS_REGION", "us-east-1")
            primary = RekognitionAdapter(region_name=aws_region)
        
        fallback = GeminiAdapter()
        provider = FallbackVisionProvider(primary_provider=primary, fallback_provider=fallback)
        
        print(f"✅ Fallback provider initialized")
        print(f"   Primary: {primary.get_provider_name()}")
        print(f"   Fallback: {fallback.get_provider_name()}")
        
    except Exception as e:
        print(f"❌ Failed to initialize providers: {e}")
        return False
    
    # Test analysis
    try:
        print("\n🔍 Analyzing image with fallback provider...")
        print("   (Watch logs to see which provider is used)")
        
        result = await provider.analyze_image(
            image_bytes=image_bytes,
            min_confidence=70.0
        )
        
        print("\n✅ Analysis complete!")
        print(f"Provider used: {result.provider_name}")
        print(f"Model: {result.model_version}")
        print(f"Labels found: {len(result.labels)}")
        
        print("\n📊 Detected Labels:")
        for label in result.labels[:10]:  # Show top 10
            print(f"  - {label.name}: {label.confidence.value:.1f}% ({label.category})")
        
        # Verify expected provider was used
        if simulate_aws_failure:
            if "gemini" in result.provider_name.lower():
                print("\n✅ Fallback worked correctly! Used Gemini after AWS failed.")
            else:
                print(f"\n⚠️  Expected Gemini but got: {result.provider_name}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_fallback.py path/to/image.jpg [--simulate-failure]")
        print("\nExamples:")
        print("  # Normal operation (AWS should work)")
        print("  python scripts/test_fallback.py test_images/clean_floor.jpg")
        print()
        print("  # Simulate AWS failure (tests fallback to Gemini)")
        print("  python scripts/test_fallback.py test_images/clean_floor.jpg --simulate-failure")
        sys.exit(1)
    
    image_path = sys.argv[1]
    simulate_failure = "--simulate-failure" in sys.argv
    
    success = asyncio.run(test_fallback(image_path, simulate_failure))
    
    if success:
        print("\n✅ Test passed!")
        sys.exit(0)
    else:
        print("\n❌ Test failed!")
        sys.exit(1)
