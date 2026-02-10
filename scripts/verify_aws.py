import sys
import os
import boto3
from dotenv import load_dotenv

# Add parent directory to path to load .env correctly if script is run from scripts/
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv()

def verify_aws():
    print("Locked and loaded AWS credentials...")
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    if access_key:
        print(f"DEBUG: Found AWS_ACCESS_KEY_ID={access_key[:4]}...{access_key[-4:]}")
    else:
        print("DEBUG: AWS_ACCESS_KEY_ID not found in environment!")
    try:
        # Check STS Identity
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        print(f"✅ STS Identity: {identity['Arn']}")
        
        # Check Rekognition Access (using list_collections as a simple read check)
        # Note: The provided credentials must have permission for this.
        rekognition = boto3.client("rekognition", region_name=os.getenv("AWS_REGION", "us-east-1"))
        print("✅ Rekognition client initialized.")
        try:
             # Just checking if we can call the service, even if empty
            cols = rekognition.list_collections(MaxResults=1)
            print("✅ Rekognition connection successful.")
        except Exception as e:
            print(f"⚠️ Rekognition connection failed (might be permissions): {e}")

        # Check S3 Access
        s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))
        bucket_name = os.getenv("S3_BUCKET")
        if bucket_name:
            print(f"Checking access to bucket: {bucket_name}")
            try:
                s3.head_bucket(Bucket=bucket_name)
                print(f"✅ S3 Bucket '{bucket_name}' accessible.")
            except Exception as e:
                print(f"⚠️ S3 Bucket check failed: {e}")
        else:
            print("⚠️ S3_BUCKET not set in .env")

    except Exception as e:
        print(f"❌ AWS Authentication Failed: {e}")

if __name__ == "__main__":
    verify_aws()
