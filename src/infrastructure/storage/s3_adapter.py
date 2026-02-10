"""
S3 Storage Adapter

WHY: Implements StorageProvider port using Amazon S3.
Handles uploads, downloads, and presigned URLs.
"""
import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError

from ...domain.ports import StorageProvider, StorageMetadata

logger = logging.getLogger(__name__)


class S3Error(Exception):
    """Raised when S3 operations fail"""
    pass


class S3Adapter(StorageProvider):
    """
    AWS S3 implementation of StorageProvider.
    
    WHY: Adapter pattern - adapts S3 API to domain interface.
    
    Design decisions:
    - Organized folder structure: {dealer_id}/{checkpoint_id}/{timestamp}_{image_id}.jpg
    - Tagging for lifecycle policies and cost allocation
    - Server-side encryption by default
    - Presigned URLs for secure client access
    """

    def __init__(
        self,
        default_bucket: str,
        region_name: str = "us-east-1",
        encryption: str = "AES256"
    ):
        """
        Initialize S3 client.
        
        Args:
            default_bucket: Default S3 bucket for uploads
            region_name: AWS region
            encryption: Server-side encryption algorithm
        """
        self.default_bucket = default_bucket
        self.region_name = region_name
        self.encryption = encryption
        
        from botocore.config import Config
        config = Config(region_name=region_name)
        
        self.client = boto3.client('s3', config=config)
        logger.info(f"Initialized S3 adapter for bucket {default_bucket}")

    async def upload_image(
        self,
        image_bytes: bytes,
        destination_key: str,
        content_type: str = "image/jpeg",
        metadata: Optional[dict] = None
    ) -> StorageMetadata:
        """
        Upload image to S3.
        
        WHY: Centralized upload with consistent settings:
        - Server-side encryption
        - Metadata tagging for governance
        - Proper content-type for browser viewing
        """
        try:
            logger.info(
                "Uploading image to S3",
                extra={
                    "bucket": self.default_bucket,
                    "key": destination_key,
                    "size_bytes": len(image_bytes)
                }
            )
            
            # Build upload parameters
            extra_args = {
                'ContentType': content_type,
                'ServerSideEncryption': self.encryption,
            }
            
            # WHY: Metadata for governance and lifecycle policies
            if metadata:
                # S3 metadata keys must be lowercase
                extra_args['Metadata'] = {
                    k.lower(): str(v) for k, v in metadata.items()
                }
            
            # Perform upload
            response = self.client.put_object(
                Bucket=self.default_bucket,
                Key=destination_key,
                Body=image_bytes,
                **extra_args
            )
            
            logger.info(f"Successfully uploaded to {destination_key}")
            
            return StorageMetadata(
                bucket=self.default_bucket,
                key=destination_key,
                version_id=response.get('VersionId'),
                etag=response.get('ETag'),
                size_bytes=len(image_bytes)
            )
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"S3 upload error: {error_code}", exc_info=True)
            raise S3Error(f"Failed to upload image: {error_code}")

    async def download_image(self, bucket: str, key: str) -> bytes:
        """
        Download image from S3.
        
        WHY: Needed for providers that can't read directly from S3 (e.g., TFLite).
        """
        try:
            logger.info(f"Downloading image from s3://{bucket}/{key}")
            
            response = self.client.get_object(Bucket=bucket, Key=key)
            image_bytes = response['Body'].read()
            
            logger.debug(f"Downloaded {len(image_bytes)} bytes")
            return image_bytes
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'NoSuchKey':
                raise S3Error(f"Image not found: s3://{bucket}/{key}")
            else:
                logger.error(f"S3 download error: {error_code}", exc_info=True)
                raise S3Error(f"Failed to download image: {error_code}")

    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expiration_seconds: int = 3600
    ) -> str:
        """
        Generate temporary download URL.
        
        WHY: Mobile app or auditors need to view images without AWS credentials.
        Presigned URLs provide time-limited access.
        
        Security: URLs expire after expiration_seconds.
        """
        try:
            url = self.client.generate_presigned_url(
                ClientMethod='get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration_seconds
            )
            
            logger.debug(f"Generated presigned URL for {key} (expires in {expiration_seconds}s)")
            return url
        
        except ClientError as e:
            logger.error("Failed to generate presigned URL", exc_info=True)
            raise S3Error(f"Failed to generate presigned URL: {str(e)}")

    async def delete_image(self, bucket: str, key: str) -> bool:
        """
        Delete image from S3.
        
        WHY: GDPR/retention policies may require deletion.
        
        Returns:
            True if deleted, False if not found
        """
        try:
            self.client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Deleted s3://{bucket}/{key}")
            return True
        
        except ClientError as e:
            logger.error("Failed to delete image", exc_info=True)
            # S3 delete is idempotent - doesn't fail if object doesn't exist
            return False

    def get_storage_uri(self, bucket: str, key: str) -> str:
        """Get standardized S3 URI"""
        return f"s3://{bucket}/{key}"

    def build_image_key(
        self,
        dealer_id: str,
        checkpoint_id: str,
        image_id: str,
        extension: str = "jpg"
    ) -> str:
        """
        Build standardized S3 key for audit images.
        
        WHY: Consistent folder structure enables:
        - S3 lifecycle policies (e.g., delete after 7 years)
        - IAM policies scoped to specific dealers
        - Cost allocation by dealer
        - Easy backup/restore
        
        Structure: {dealer_id}/{checkpoint_id}/{image_id}.{extension}
        Example: dealer-001/checkpoint-reception/2024-01-15_uuid.jpg
        """
        return f"{dealer_id}/{checkpoint_id}/{image_id}.{extension}"
