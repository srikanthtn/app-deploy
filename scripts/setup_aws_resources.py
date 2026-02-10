import sys
import os
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Add parent directory to path to load .env correctly
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv()

def setup_resources():
    print("🚀 Setting up AWS resources...")
    region = os.getenv("AWS_REGION", "us-east-1")
    s3 = boto3.client("s3", region_name=region)
    bucket_name = os.getenv("S3_BUCKET")

    if not bucket_name:
        print("❌ S3_BUCKET not defined in .env")
        return

    print(f"Checking bucket: {bucket_name} in {region}")
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' already exists and is accessible.")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"Bucket '{bucket_name}' does not exist. Creating...")
            try:
                if region == "us-east-1":
                    s3.create_bucket(Bucket=bucket_name)
                else:
                    s3.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': region}
                    )
                print(f"✅ Bucket '{bucket_name}' created successfully.")
            except ClientError as create_error:
                print(f"❌ Failed to create bucket: {create_error}")
        elif error_code == '403':
            print(f"❌ Access Denied to bucket '{bucket_name}'. It might exist but you don't have permission.")
        else:
            print(f"❌ Error checking bucket: {e}")

if __name__ == "__main__":
    setup_resources()
