"""
FastAPI Dependency Injection

WHY: Wire up dependencies for API endpoints.
This is where we choose WHICH implementations to inject.

In production, use python-dependency-injector for more sophisticated DI.
"""
import os
from functools import lru_cache
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..infrastructure.vision.rekognition_adapter import RekognitionAdapter
from ..infrastructure.storage.s3_adapter import S3Adapter
from ..application.use_cases.analyze_cleanliness import AnalyzeCleanlinessUseCase
from ..domain.services import CleanlinessRules


# === Configuration ===

@lru_cache()
def get_settings():
    """
    Load configuration from environment variables.
    
    WHY: 12-factor app - configuration via environment.
    lru_cache ensures singleton.
    """
    return {
        "aws_region": os.getenv("AWS_REGION", "us-east-1"),
        "s3_bucket": os.getenv("S3_BUCKET", "stellantis-hygiene-images"),
        "confidence_threshold": float(os.getenv("CONFIDENCE_THRESHOLD", "80.0")),
        "max_labels": int(os.getenv("MAX_LABELS", "50")),
        "auth_enabled": os.getenv("AUTH_ENABLED", "true").lower() == "true",
        "database_url": os.getenv("DATABASE_URL", "sqlite:///./sql_app.db") # Default to SQLite for dev
    }


# === Infrastructure Dependencies ===

@lru_cache()
def get_vision_provider():
    """
    Factory for vision provider.
    
    WHY: Strategy pattern - can swap implementations via environment variable.
    
    Options:
    - rekognition: AWS Rekognition only
    - gemini: Google Gemini only
    - fallback: Try AWS first, fall back to Gemini (recommended)
    - tflite: TensorFlow Lite (existing)
    """
    settings = get_settings()
    provider_type = os.getenv("VISION_PROVIDER", "rekognition")
    
    if provider_type == "rekognition":
        return RekognitionAdapter(region_name=settings["aws_region"])
    
    elif provider_type == "gemini":
        from ..infrastructure.vision.gemini_adapter import GeminiAdapter
        return GeminiAdapter()
    
    elif provider_type == "fallback":
        from ..infrastructure.vision.gemini_adapter import GeminiAdapter
        from ..infrastructure.vision.fallback_vision_provider import FallbackVisionProvider
        
        # Create primary (AWS) and fallback (Gemini) providers
        try:
            primary = RekognitionAdapter(region_name=settings["aws_region"])
        except Exception as e:
            # If AWS setup fails, fall back to Gemini only
            import logging
            logging.warning(f"Failed to initialize AWS Rekognition: {e}. Using Gemini only.")
            return GeminiAdapter()
        
        try:
            fallback = GeminiAdapter()
        except Exception as e:
            # If Gemini setup fails, use AWS only
            import logging
            logging.warning(f"Failed to initialize Gemini: {e}. Using AWS Rekognition only.")
            return primary
        
        return FallbackVisionProvider(primary_provider=primary, fallback_provider=fallback)
    
    else:
        raise ValueError(f"Unknown vision provider: {provider_type}")



@lru_cache()
def get_storage_provider():
    """Factory for storage provider"""
    settings = get_settings()
    return S3Adapter(
        default_bucket=settings["s3_bucket"],
        region_name=settings["aws_region"]
    )


# === Database Dependency ===

from ..infrastructure.persistence.database import Database

_db_instance = None

def get_db_instance():
    """Singleton database instance"""
    global _db_instance
    if _db_instance is None:
        settings = get_settings()
        _db_instance = Database(settings["database_url"])
    return _db_instance

def get_db_session():
    """
    FastAPI dependency for DB session.
    """
    db_instance = get_db_instance()
    yield from db_instance.get_db()


from ..infrastructure.persistence.in_memory_repository import InMemoryAuditRepository
# from ..infrastructure.persistence.dynamodb_repository import DynamoDBAuditRepository

# Global singleton for in-memory DB (simulates persistent storage during runtime)
_in_memory_repo = InMemoryAuditRepository()

@lru_cache()
def get_audit_repository():
    """
    Factory for audit repository.
    
    WHY: Repository pattern - can swap DynamoDB/RDS/in-memory.
    
    Default: Returns InMemoryAuditRepository for immediate local dev.
    Production: Config via REPOSITORY_TYPE env var.
    """
    settings = get_settings()
    repo_type = os.getenv("REPOSITORY_TYPE", "memory")
    
    if repo_type == "memory":
        return _in_memory_repo
    elif repo_type == "dynamodb":
        # return DynamoDBAuditRepository(
        #     table_name=os.getenv("DYNAMODB_TABLE"),
        #     region_name=settings["aws_region"]
        # )
        raise NotImplementedError("DynamoDB repository not fully implemented")
    else:
        return _in_memory_repo


# === Application Dependencies ===

def get_analyze_use_case(
    vision_provider=Depends(get_vision_provider),
    storage_provider=Depends(get_storage_provider),
    audit_repository=Depends(get_audit_repository)
) -> AnalyzeCleanlinessUseCase:
    """
    Factory for AnalyzeCleanlinessUseCase.
    
    WHY: Dependency injection - FastAPI injects all dependencies.
    Each request gets a fresh use case instance (request-scoped).
    """
    settings = get_settings()
    
    # Create default rules from configuration
    default_rules = CleanlinessRules(
        confidence_threshold=settings["confidence_threshold"]
    )
    
    return AnalyzeCleanlinessUseCase(
        vision_provider=vision_provider,
        storage_provider=storage_provider,
        audit_repository=audit_repository,
        default_bucket=settings["s3_bucket"],
        default_rules=default_rules
    )


# === Authentication Dependencies ===

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Authenticate user from bearer token.
    
    WHY: Security - only authenticated users can submit audits.
    
    In production:
    1. Validate JWT token
    2. Verify signature with AWS Cognito / Auth0
    3. Extract user claims
    4. Check permissions (RBAC)
    
    For now: Mock implementation for demonstration.
    """
    settings = get_settings()
    
    if not settings["auth_enabled"]:
        # Development mode - skip auth
        return {
            "user_id": "dev-user",
            "dealer_id": "dev-dealer",
            "roles": ["auditor"]
        }
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    from ..infrastructure.security.jwt_token import decode_access_token
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "roles": ["auditor"] # Default role for now
    }
