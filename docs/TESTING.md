# Testing Strategy

## Overview

This project uses a **multi-layered testing strategy** aligned with Clean Architecture:

```
                        Integration Tests
                       /                  \
                  Unit Tests          E2E Tests
                 /    |     \              |
            Domain  App  Infra          API
```

## Test Pyramid

### 1. Unit Tests (70% coverage target)

**Location**: `tests/unit/`

**Characteristics**:
- Test single units in isolation
- No external dependencies (no AWS, no DB, no network)
- Fast execution (< 1s total)
- Run on every commit

**Examples**:
- Domain value objects (`ConfidenceScore`, `CleanlinessStatus`)
- Domain services (`CleanlinessEvaluator`)
- Business rule validation

**Why Important**: Domain logic is the CORE of the application. Must be rock-solid.

**Running**:
```bash
pytest tests/unit/ -v
```

### 2. Integration Tests (20% coverage target)

**Location**: `tests/integration/`

**Characteristics**:
- Test adapters with mocked AWS services (moto)
- Verify infrastructure layer correctly implements ports
- Medium execution time (< 10s total)
- Run before merge to main

**Examples**:
- Rekognition adapter with moto
- S3 adapter with moto
- DynamoDB repository with moto

**Why Important**: Verifies we correctly use AWS APIs without actual API calls.

**Running**:
```bash
pytest tests/integration/ -v
```

### 3. End-to-End Tests (10% coverage target)

**Location**: `tests/e2e/`

**Characteristics**:
- Test complete workflows through API
- Use TestClient (no real HTTP)
- Can use real or mocked dependencies
- Slower execution (< 60s total)
- Run before release

**Examples**:
- Full analysis workflow: upload → analyze → retrieve result
- Authentication flows
- Error handling scenarios

**Running**:
```bash
pytest tests/e2e/ -v
```

## Test Organization

### Domain Layer Tests (`tests/unit/domain/`)

```python
# Test value objects
test_confidence_score.py
test_cleanliness_status.py
test_image_metadata.py

# Test entities
test_audit_result.py

# Test domain services
test_cleanliness_evaluator.py
```

**Key principle**: ZERO external dependencies. If you import boto3 in domain tests, you've failed.

### Infrastructure Layer Tests (`tests/integration/infrastructure/`)

```python
# Test adapters
test_rekognition_adapter.py
test_s3_adapter.py
test_dynamodb_repository.py

# Test with moto
@mock_rekognition
@mock_s3
def test_...():
    pass
```

**Key principle**: Use moto to mock AWS services. No real API calls in CI/CD.

### Application Layer Tests (`tests/unit/application/`)

```python
# Test use cases
test_analyze_cleanliness_use_case.py

# Mock all dependencies
@pytest.fixture
def mock_vision_provider():
    return Mock(spec=VisionProvider)
```

**Key principle**: Mock infrastructure using ports (interfaces). Test orchestration logic only.

## Mocking Strategy

### Why Mock?

1. **Speed**: Real AWS calls = slow tests
2. **Cost**: Rekognition charges per API call
3. **Reliability**: Tests shouldn't fail due to network issues
4. **Determinism**: Mocks return predictable data

### What to Mock?

#### Domain Layer: NOTHING
- Domain has no external dependencies
- Pure business logic

#### Application Layer: PORTS
```python
# Mock the PORT (interface), not the adapter
mock_vision = Mock(spec=VisionProvider)
mock_vision.analyze_image.return_value = VisionAnalysisResult(...)
```

#### Infrastructure Layer: AWS Services
```python
# Use moto for AWS
@mock_rekognition
def test_rekognition_adapter():
    # boto3 calls go to moto, not real AWS
    pass
```

## Test Fixtures

### Shared Fixtures (`tests/conftest.py`)

```python
@pytest.fixture
def sample_image_bytes():
    """Valid JPEG bytes for testing"""
    return Path("tests/fixtures/test_image.jpg").read_bytes()

@pytest.fixture
def sample_image_metadata():
    """Standard ImageMetadata for tests"""
    return ImageMetadata(...)

@pytest.fixture
def mock_vision_provider():
    """Mock VisionProvider"""
    return Mock(spec=VisionProvider)
```

## Coverage Goals

### Overall: 80%

- **Domain Layer**: 95% (critical business logic)
- **Application Layer**: 85% (use case orchestration)
- **Infrastructure Layer**: 70% (adapters)
- **API Layer**: 60% (mainly integration tests)

### Running Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src
      
      - name: Run integration tests
        run: pytest tests/integration/ -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test-Driven Development (TDD)

### Red-Green-Refactor Cycle

1. **Red**: Write failing test first
   ```python
   def test_clean_facility():
       # This will fail - not implemented yet
       result = evaluator.evaluate(...)
       assert result.status == CleanlinessStatus.CLEAN
   ```

2. **Green**: Implement minimum code to pass
   ```python
   def evaluate(...):
       return CleanlinessStatus.CLEAN  # Hardcoded
   ```

3. **Refactor**: Improve implementation
   ```python
   def evaluate(...):
       # Actual business logic
       if negative_labels:
           return CleanlinessStatus.NOT_CLEAN
       return CleanlinessStatus.CLEAN
   ```

### Benefits

- Forces you to think about interfaces first
- Prevents over-engineering
- Living documentation via tests
- Confidence to refactor

## Property-Based Testing (Advanced)

Use `hypothesis` for property-based tests:

```python
from hypothesis import given, strategies as st

@given(
    confidence=st.floats(min_value=0.0, max_value=100.0)
)
def test_confidence_score_value_object(confidence):
    """ConfidenceScore should work for any valid float"""
    score = ConfidenceScore(value=confidence)
    assert 0.0 <= score.value <= 100.0
```

**Why**: Finds edge cases you didn't think of.

## Performance Testing

### Load Testing with Locust

```python
from locust import HttpUser, task, between

class HygieneUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def analyze_image(self):
        with open("test_image.jpg", "rb") as f:
            self.client.post(
                "/api/v1/hygiene/analyze",
                files={"image": f},
                data={
                    "dealer_id": "dealer-001",
                    "checkpoint_id": "reception"
                }
            )
```

**Run**: `locust -f tests/performance/locustfile.py`

**Targets**:
- p50 latency: < 1s
- p95 latency: < 2s
- p99 latency: < 3s
- Throughput: > 100 req/s

## Testing Best Practices

### ✅ DO

- Test behavior, not implementation
- Use descriptive test names: `test_should_return_not_clean_when_dirt_detected`
- Arrange-Act-Assert pattern
- One assertion per test (when possible)
- Mock at architectural boundaries (ports)

### ❌ DON'T

- Test private methods directly
- Mock internal implementation details
- Write tests that depend on execution order
- Hardcode environment-specific values
- Skip tests (fix or delete them)

## Example: Complete Test Suite

```python
# tests/unit/domain/test_cleanliness_evaluator.py
import pytest
from src.domain.services import CleanlinessEvaluator

class TestCleanlinessEvaluator:
    """Test domain service in isolation"""
    
    @pytest.fixture
    def evaluator(self):
        return CleanlinessEvaluator(rules=CleanlinessRules())
    
    def test_clean_facility(self, evaluator):
        """Should return CLEAN when no issues detected"""
        # Arrange
        vision_result = create_vision_result(labels=["Clean", "Organized"])
        
        # Act
        result = evaluator.evaluate(vision_result, image_metadata)
        
        # Assert
        assert result.status == CleanlinessStatus.CLEAN
        assert len(result.negative_labels) == 0
```

## Resources

- **pytest docs**: https://docs.pytest.org
- **moto docs**: https://docs.getmoto.org
- **hypothesis docs**: https://hypothesis.readthedocs.io
- **Clean Architecture Testing**: https://blog.cleancoder.com/uncle-bob/2017/05/05/TestDefinitions.html
