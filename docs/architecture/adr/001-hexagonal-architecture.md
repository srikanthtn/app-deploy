# Architecture Decision Record: Hexagonal Architecture for Vision Pipeline

**Date**: 2024-01-15  
**Status**: Accepted  
**Context**: Designing vision pipeline for dealer hygiene audit system

## Decision

We will implement the vision pipeline using **Hexagonal Architecture** (Ports and Adapters), also known as Clean Architecture.

## Context

### Requirements
- Analyze facility images using Amazon Rekognition
- Must support future ML model replacements (TensorFlow Lite, custom models)
- Needs to be testable without AWS credentials
- Business rules must be isolated and protected
- Scale to millions of images across thousands of dealers

### Options Considered

#### Option 1: Monolithic FastAPI App ❌
```python
# Everything in one file
@app.post("/analyze")
async def analyze(image: UploadFile):
    # Upload to S3 directly
    s3.upload(...)
    
    # Call Rekognition directly
    rekognition.detect_labels(...)
    
    # Business logic inline
    if "Dirt" in labels:
        return {"status": "NOT_CLEAN"}
```

**Pros**:
- Fast to implement initially
- Fewer files/abstractions

**Cons**:
- AWS SDK coupled to controllers
- Business logic scattered
- Impossible to test without AWS
- Cannot swap vision providers
- Violates SOLID principles

#### Option 2: Service Layer Pattern ❌
```python
# Better separation, but still coupled
class HygieneService:
    def analyze(self, image):
        s3_client.upload(...)
        rekognition_client.detect_labels(...)
        return self._evaluate(labels)
```

**Pros**:
- Some separation of concerns
- Service layer for business logic

**Cons**:
- Still tightly coupled to AWS SDK
- Hard to swap providers
- Difficult to test in isolation

#### Option 3: Hexagonal Architecture ✅ (CHOSEN)
```python
# Domain layer - zero dependencies
class CleanlinessEvaluator:
    def evaluate(self, vision_result: VisionAnalysisResult):
        # Pure business logic
        
# Infrastructure layer - adapters
class RekognitionAdapter(VisionProvider):
    def analyze_image(self):
        # AWS-specific implementation
```

**Pros**:
- Business logic completely isolated
- Testable without AWS
- Pluggable vision providers
- SOLID compliance
- Future-proof for model changes

**Cons**:
- More files and abstractions upfront
- Learning curve for junior developers
- Requires discipline to maintain boundaries

## Decision Drivers

### 1. **Testability** (Critical)
- Domain tests must run without AWS credentials
- CI/CD must be fast (no real API calls)
- Developers need to test locally

### 2. **Extensibility** (Critical)
- Vision provider must be swappable
- Different dealers may need different models
- Cost optimization via custom models

### 3. **Maintainability** (High)
- Business rules centralized in domain layer
- Changes to AWS SDK don't affect domain
- Clear separation of concerns

### 4. **Team Scalability** (High)
- Multiple teams can work independently
- Domain experts work on domain layer
- Infrastructure experts work on adapters

## Implementation Strategy

### Layer Structure

```
Domain Layer (Core)
├── Entities (AuditResult)
├── Value Objects (CleanlinessStatus, ConfidenceScore)
├── Services (CleanlinessEvaluator)
└── Ports (VisionProvider, StorageProvider, AuditRepository)

Application Layer (Use Cases)
├── AnalyzeCleanlinessUseCase
└── GetAuditHistoryUseCase

Infrastructure Layer (Adapters)
├── RekognitionAdapter (implements VisionProvider)
├── S3Adapter (implements StorageProvider)
└── DynamoDBRepository (implements AuditRepository)

API Layer (Presentation)
├── FastAPI routes
├── Request/Response DTOs
└── Dependency injection
```

### Dependency Rule

**Critical**: Dependencies point INWARD only.

```
API → Application → Domain
         ↓
   Infrastructure
```

- API depends on Application
- Application depends on Domain
- Infrastructure depends on Domain (implements ports)
- Domain depends on NOTHING

### Key Patterns

1. **Strategy Pattern**: Vision providers are strategies
2. **Adapter Pattern**: Infrastructure adapts external services
3. **Repository Pattern**: Data access abstracted
4. **Dependency Injection**: All dependencies injected at boundaries

## Consequences

### Positive

✅ **Testability**: Domain tests run in milliseconds without AWS  
✅ **Flexibility**: Swap Rekognition for custom models via config change  
✅ **Maintainability**: Business rules isolated and protected  
✅ **Scalability**: Teams can work on different layers independently  
✅ **Documentation**: Architecture is self-documenting  

### Negative

⚠️ **Initial Complexity**: More files and abstractions upfront  
⚠️ **Learning Curve**: Team must understand layered architecture  
⚠️ **Discipline Required**: Easy to violate boundaries if not careful  

### Mitigation

- Comprehensive documentation (this ADR + README)
- Code reviews enforcing architectural boundaries
- Linting rules preventing cross-layer imports
- Onboarding guide for new developers

## Validation

### Success Criteria

1. ✅ Domain layer has zero infrastructure imports
2. ✅ Unit tests run without AWS credentials
3. ✅ Vision provider swappable via environment variable
4. ✅ Business logic testable in isolation
5. ✅ New features don't violate layer boundaries

### Metrics

- **Test Speed**: Unit tests < 1s
- **Test Coverage**: Domain layer > 95%
- **Coupling**: Domain layer has zero external dependencies
- **Changeability**: Swapping vision provider requires < 10 lines of code

## Alternatives Considered

### Why Not Clean Architecture?
Clean Architecture is essentially the same as Hexagonal Architecture. We chose the "Hexagonal" terminology because:
- Emphasizes ports and adapters
- More visual (hexagon diagram)
- Widespread in Python/FastAPI community

### Why Not Domain-Driven Design (DDD)?
DDD is compatible with Hexagonal Architecture. We incorporate DDD concepts:
- Entities (AuditResult)
- Value Objects (ConfidenceScore)
- Domain Services (CleanlinessEvaluator)
- Ubiquitous Language

But we don't use full DDD (aggregates, bounded contexts) because:
- Application is focused (single bounded context)
- Adds complexity without proportional benefit

## References

- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture by Uncle Bob](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Ports and Adapters Pattern](https://jmgarridopaz.github.io/content/hexagonalarchitecture.html)
- [FastAPI with Clean Architecture](https://github.com/zhanymkanov/fastapi-best-practices)

## Review

**Reviewers**: Architecture Team, Tech Leads  
**Next Review**: After 3 months of implementation  
**Changes**: None (initial version)
