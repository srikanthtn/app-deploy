# Dealer Hygiene Vision Pipeline

## Architecture Overview

This project implements a **Clean Architecture** vision pipeline for automated dealer facility hygiene audits using Amazon Rekognition.

### Design Principles
- **Hexagonal Architecture**: Business logic isolated from infrastructure
- **Dependency Inversion**: Domain layer has zero external dependencies
- **Strategy Pattern**: Vision providers are pluggable (Rekognition, TFLite, custom models)
- **Adapter Pattern**: All AWS services accessed through abstractions
- **Repository Pattern**: Audit persistence abstracted from storage implementation

### Layer Dependencies (Dependency Rule)
```
API Layer → Application Layer → Domain Layer
                ↓
        Infrastructure Layer
```

**Critical Rule**: Dependencies point INWARD only. Domain layer imports nothing from outer layers.

### Technology Stack
- **API**: FastAPI
- **Language**: Python 3.11+
- **Vision**: Amazon Rekognition (primary), Google Gemini (fallback)
- **Storage**: Amazon S3
- **Serialization**: Pydantic
- **DI**: Python `dependency-injector`
- **Testing**: pytest, moto (AWS mocking)

### Vision Provider Options

The system supports multiple vision providers with automatic fallback:

**Available Providers**:
- `rekognition` - AWS Rekognition only (original)
- `gemini` - Google Gemini Vision only
- `fallback` - AWS Rekognition first, Gemini fallback ✅ **Recommended**

**Configuration** (in `.env`):
```bash
# Vision provider mode
VISION_PROVIDER=fallback

# Required for fallback or gemini modes
GEMINI_API_KEY=your_gemini_api_key_here
```

**Get Gemini API Key**: https://ai.google.dev/

### Folder Structure
```
stellantis-hygiene-vision/
├─ src/
│  ├─ api/                          # API Layer (FastAPI routes)
│  │  ├─ __init__.py
│  │  ├─ routes/
│  │  │  ├─ __init__.py
│  │  │  ├─ health.py              # Health check endpoint
│  │  │  └─ hygiene.py             # Hygiene analysis endpoints
│  │  ├─ middleware/
│  │  │  ├─ __init__.py
│  │  │  ├─ correlation_id.py      # Request tracing
│  │  │  └─ error_handler.py       # Global exception handling
│  │  └─ dependencies.py            # FastAPI dependency injection
│  │
│  ├─ application/                  # Application Layer (Use Cases)
│  │  ├─ __init__.py
│  │  ├─ use_cases/
│  │  │  ├─ __init__.py
│  │  │  ├─ analyze_cleanliness.py # Core use case
│  │  │  └─ get_audit_history.py
│  │  └─ dto/
│  │     ├─ __init__.py
│  │     ├─ requests.py            # Request DTOs
│  │     └─ responses.py           # Response DTOs
│  │
│  ├─ domain/                       # Domain Layer (Business Logic)
│  │  ├─ __init__.py
│  │  ├─ entities/
│  │  │  ├─ __init__.py
│  │  │  ├─ audit_result.py       # Core domain entity
│  │  │  ├─ checkpoint.py
│  │  │  └─ dealer.py
│  │  ├─ value_objects/
│  │  │  ├─ __init__.py
│  │  │  ├─ cleanliness_status.py
│  │  │  ├─ confidence_score.py
│  │  │  └─ image_metadata.py
│  │  ├─ services/
│  │  │  ├─ __init__.py
│  │  │  └─ cleanliness_evaluator.py  # Domain service
│  │  ├─ ports/
│  │  │  ├─ __init__.py
│  │  │  ├─ vision_provider.py     # Port for vision analysis
│  │  │  ├─ storage_provider.py    # Port for S3
│  │  │  └─ audit_repository.py    # Port for persistence
│  │  └─ exceptions/
│  │     ├─ __init__.py
│  │     └─ domain_exceptions.py
│  │
│  ├─ infrastructure/                # Infrastructure Layer (Adapters)
│  │  ├─ __init__.py
│  │  ├─ vision/
│  │  │  ├─ __init__.py
│  │  │  ├─ rekognition_adapter.py # AWS Rekognition implementation
│  │  │  ├─ gemini_adapter.py      # Google Gemini implementation
│  │  │  ├─ fallback_vision_provider.py # Fallback wrapper
│  │  │  └─ tflite_adapter.py      # Future: TensorFlow Lite
│  │  ├─ storage/
│  │  │  ├─ __init__.py
│  │  │  └─ s3_adapter.py          # S3 implementation
│  │  ├─ persistence/
│  │  │  ├─ __init__.py
│  │  │  └─ dynamodb_repository.py # DynamoDB audit storage
│  │  └─ config/
│  │     ├─ __init__.py
│  │     └─ settings.py            # Environment configuration
│  │
│  ├─ shared/                        # Shared utilities
│  │  ├─ __init__.py
│  │  ├─ logging.py
│  │  └─ metrics.py
│  │
│  └─ main.py                        # FastAPI application factory
│
├─ tests/
│  ├─ unit/
│  │  ├─ domain/
│  │  ├─ application/
│  │  └─ infrastructure/
│  ├─ integration/
│  └─ conftest.py
│
├─ docs/
│  ├─ architecture/
│  │  ├─ adr/                       # Architectural Decision Records
│  │  └─ diagrams/
│  ├─ iam-policies/
│  │  └─ rekognition-policy.json
│  └─ deployment/
│
├─ requirements.txt
├─ requirements-dev.txt
├─ pyproject.toml
├─ Dockerfile
└─ .env.example
```

### Key Design Decisions

#### Why Hexagonal Architecture?
- **Testability**: Mock vision providers without AWS credentials
- **Flexibility**: Replace Rekognition with custom models without touching business logic
- **Maintainability**: Domain rules centralized and protected from infrastructure changes

#### Why Strategy Pattern for Vision?
- Different dealers may require different models (general cleanliness vs specialized equipment)
- A/B testing between models
- Gradual migration from Rekognition to custom models

#### Why Repository Pattern?
- Abstract audit storage (DynamoDB today, RDS tomorrow)
- Enable offline testing with in-memory repositories
- Support multi-region replication strategies

### Next Steps
1. Implement domain layer (zero dependencies)
2. Define ports (interfaces)
3. Build application use cases
4. Create infrastructure adapters
5. Wire up FastAPI endpoints
