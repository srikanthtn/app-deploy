"""
FastAPI Application Factory

WHY: Application factory pattern enables:
1. Multiple environments (dev/staging/prod)
2. Testing with different configurations
3. Dependency injection customization
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .api.routes import hygiene, auth
from .api.routers import manual_audit_router, manager_portal_router
from .api.middleware.correlation_id import CorrelationIDMiddleware


# === Logging Configuration ===

def configure_logging():
    """
    Configure structured logging.
    
    WHY: Production-grade logging:
    - JSON format for log aggregation (CloudWatch, Datadog)
    - Correlation IDs for request tracing
    - Log levels from environment
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Silence noisy libraries
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# === Lifespan Events ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    
    WHY: Initialize/cleanup resources on startup/shutdown.
    - Warm up connection pools
    - Verify AWS credentials
    - Health checks
    """
    # Startup
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting Dealer Hygiene Vision API")
    
    # TODO: Verify AWS credentials and permissions
    # TODO: Warm up Rekognition (optional)
    
    # Initialize Database Tables
    from .infrastructure.persistence.models import Base, UserModel
    from .infrastructure.database.manual_audit_db import create_tables as create_manual_audit_tables
    from .api.dependencies import get_db_instance
    
    try:
        db_instance = get_db_instance()
        # Create all tables (User, etc.)
        Base.metadata.create_all(bind=db_instance.engine)
        logger.info("Database tables verified/created")

        # Create manual audit tables
        create_manual_audit_tables()
        logger.info("Manual audit tables verified/created")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Dealer Hygiene Vision API")
    # TODO: Close database connections, flush metrics, etc.


# === Application Factory ===

def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    WHY: Factory pattern - enables testing with different configs.
    """
    app = FastAPI(
        title="Dealer Hygiene Vision API",
        description="""
        ## 🏭 Industrial-Grade Vision Pipeline for Dealer Hygiene Audits
        
        **Architecture**: Clean Architecture / Hexagonal Architecture
        
        **Features**:
        - 📸 Image upload and storage (S3)
        - 🤖 AI-powered cleanliness analysis (Amazon Rekognition)
        - ✅ Business rule evaluation
        - 📊 Audit trail and reporting
        - 👤 Manual override capability
        
        **Tech Stack**:
        - Amazon Rekognition for vision analysis
        - Amazon S3 for secure image storage
        - FastAPI for high-performance API
        - Pydantic for data validation
        
        **Security**: IAM-based authentication, encrypted storage
        """,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=[
            {
                "name": "Hygiene Analysis",
                "description": "Image analysis and cleanliness evaluation"
            },
            {
                "name": "Health",
                "description": "Health checks and monitoring"
            }
        ]
    )
    
    # === Middleware ===
    
    # CORS (for mobile app/web dashboard)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Correlation ID tracking
    app.add_middleware(CorrelationIDMiddleware)
    
    # Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # === Routes ===
    
    app.include_router(hygiene.router)
    app.include_router(auth.router)
    app.include_router(manual_audit_router.router)  # Manual Audit endpoints
    app.include_router(manager_portal_router.router)  # Manager Portal endpoints

    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Health check endpoint.
        
        WHY: Load balancers and orchestrators need this.
        Returns 200 if service is healthy.
        """
        return {
            "status": "healthy",
            "service": "dealer-hygiene-vision-api",
            "version": "1.0.0"
        }
    
    @app.get("/", tags=["Health"])
    async def root():
        """Root endpoint - redirects to docs"""
        return {
            "message": "Dealer Hygiene Vision API",
            "docs": "/docs",
            "health": "/health"
        }
    
    return app


# === Application Instance ===

app = create_app()


# === Entry Point ===

if __name__ == "__main__":
    import uvicorn
    
    # WHY: Uvicorn for production-grade ASGI serving
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Dev only
        log_level="info"
    )
