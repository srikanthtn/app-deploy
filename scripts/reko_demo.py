import sys
import os
import boto3
import requests
from dotenv import load_dotenv
from io import BytesIO

# Add parent directory to path to load .env correctly
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv()

def demo_rekognition():
    print("🚀 Starting Rekognition Demo...")
    
    # 1. Get a sample image
    image_url = "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80" # Car image
    print("Downloading sample image...")
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        image_bytes = response.content
        print(f"Downloaded {len(image_bytes)} bytes.")
    except Exception as e:
        print(f"❌ Failed to download image: {e}")
        return

    # 2. Upload to S3
    s3 = boto3.client("s3")
    bucket_name = os.getenv("S3_BUCKET")
    key = "demo/car_sample.jpg"
    
    print(f"Uploading to s3://{bucket_name}/{key}...")
    try:
        s3.put_object(Bucket=bucket_name, Key=key, Body=image_bytes)
        print("✅ Upload successful.")
    except Exception as e:
        print(f"❌ Failed to upload to S3: {e}")
        return

    # 3. Call Rekognition
    print("Analyzing likely cleanliness with Rekognition...")
    rekognition = boto3.client("rekognition")
    
    try:
        response = rekognition.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': key
                }
            },
            MaxLabels=10,
            MinConfidence=75
        )
        
        print("\n🔍 Analysis Result:")
        print(f"Model Version: {response['LabelModelVersion']}")
        for label in response['Labels']:
            print(f"- {label['Name']}: {label['Confidence']:.2f}%")
            
        print("\n✅ Rekognition usage confirmed!")
        
    except Exception as e:
        print(f"❌ Rekognition analysis failed: {e}")

if __name__ == "__main__":
    demo_rekognition()
