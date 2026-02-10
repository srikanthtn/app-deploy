"""
Storage Provider Port (Interface)

WHY: Abstract S3 storage to enable testing and future migrations.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class StorageMetadata:
    """
    Metadata returned after successful upload.
    
    WHY: Domain needs to know WHERE the image is stored for audit trail.
    """
    bucket: str
    key: str
    version_id: Optional[str] = None
    etag: Optional[str] = None
    size_bytes: int = 0


class StorageProvider(ABC):
    """
    Port for cloud storage operations.
    
    WHY: Hexagonal architecture - domain defines storage contract,
    infrastructure provides S3/GCS/Azure implementation.
    """

    @abstractmethod
    async def upload_image(
        self,
        image_bytes: bytes,
        destination_key: str,
        content_type: str = "image/jpeg",
        metadata: Optional[dict] = None
    ) -> StorageMetadata:
        """
        Upload image to storage.
        
        WHY: Centralized upload logic with consistent error handling.
        
        Args:
            image_bytes: Raw image data
            destination_key: Storage path (e.g., "dealer-123/checkpoint-456/img.jpg")
            content_type: MIME type
            metadata: Additional metadata tags
        
        Returns:
            StorageMetadata with upload details
        
        Raises:
            StorageError: If upload fails
        """
        pass

    @abstractmethod
    async def download_image(self, bucket: str, key: str) -> bytes:
        """
        Download image from storage.
        
        WHY: Sometimes need to retrieve images (e.g., for TFLite local analysis).
        """
        pass

    @abstractmethod
    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expiration_seconds: int = 3600
    ) -> str:
        """
        Generate temporary download URL.
        
        WHY: Mobile app or auditors may need direct image access.
        Presigned URLs avoid exposing credentials.
        """
        pass

    @abstractmethod
    async def delete_image(self, bucket: str, key: str) -> bool:
        """
        Delete image from storage.
        
        WHY: GDPR/retention policies may require deletion.
        """
        pass

    @abstractmethod
    def get_storage_uri(self, bucket: str, key: str) -> str:
        """
        Get standardized storage URI.
        
        WHY: Consistent URI format for logs and references.
        Example: s3://my-bucket/path/to/image.jpg
        """
        pass
