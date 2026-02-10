import requests
import sys

def test_health():
    print("Testing Health Endpoint...")
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Health Check Passed!")
            print(response.json())
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
         print(f"❌ Connection Failed: {e}")

def test_analyze():
    print("\nTesting Analysis Endpoint...")
    
    # 1. Download a sample image dynamically so the user doesn't need one
    image_url = "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=500&q=80"
    print("Downloading sample image for testing...")
    try:
        img_response = requests.get(image_url)
        img_response.raise_for_status()
        image_bytes = img_response.content
    except Exception as e:
        print(f"❌ Failed to download sample image: {e}")
        return

    # 2. Send to API
    url = "http://localhost:8000/api/v1/hygiene/analyze"
    headers = {
        "Authorization": "Bearer valid-token" 
    }
    data = {
        "dealer_id": "TEST_DEALER_001",
        "checkpoint_id": "SERVICE_BAY_1",
        "min_confidence": 70.0
    }
    files = {
        "image": ("test_car.jpg", image_bytes, "image/jpeg")
    }

    print("Sending request to API...")
    try:
        response = requests.post(url, headers=headers, data=data, files=files)
        
        if response.status_code == 201:
            print("✅ Analysis Successful!")
            print("Response:")
            print(response.json())
        else:
            print(f"❌ Analysis Failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Request Failed: {e}")

if __name__ == "__main__":
    test_health()
    test_analyze()
