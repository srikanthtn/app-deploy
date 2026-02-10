# 🚀 Quick Start Guide

Get the Dealer Hygiene Vision API running in 5 minutes!

## Prerequisites

- **Python 3.11+** installed
- **AWS Account** with:
  - Rekognition access
  - S3 bucket creation permissions
- **AWS CLI** configured (`aws configure`)

---

## Step 1: Clone & Setup (1 min)

```bash
# Clone repository
cd "e:/Project Files/Stellantis-Dealer-Hygiene-App"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## Step 2: Configure Environment (1 min)

```bash
# Copy example environment file
copy .env .env

# Edit .env with your settings
notepad .env
```

**Required settings**:
```bash
AWS_REGION=us-east-1
S3_BUCKET=stellantis-hygiene-images-YOUR-NAME  # Make it unique!
VISION_PROVIDER=rekognition
CONFIDENCE_THRESHOLD=80.0
AUTH_ENABLED=false  # For local development
```

---

## Step 3: Create S3 Bucket (30 sec)

```bash
# Create bucket (replace with your bucket name from .env)
aws s3 mb s3://stellantis-hygiene-images-YOUR-NAME --region us-east-1

# Verify bucket created
aws s3 ls | findstr stellantis-hygiene
```

---

## Step 4: Run Tests (1 min)

```bash
# Run unit tests (fast, no AWS needed)
pytest tests/unit/ -v

# Expected output: All tests pass ✓
```

**Sample output**:
```
tests/unit/domain/test_cleanliness_evaluator.py::TestCleanlinessEvaluator::test_clean_facility_with_no_negative_labels PASSED
tests/unit/domain/test_cleanliness_evaluator.py::TestCleanlinessEvaluator::test_not_clean_with_dirt_detected PASSED
tests/unit/domain/test_cleanliness_evaluator.py::TestCleanlinessEvaluator::test_manual_review_on_low_confidence PASSED
tests/unit/domain/test_cleanliness_evaluator.py::TestCleanlinessEvaluator::test_manual_override_clean PASSED
tests/unit/domain/test_cleanliness_evaluator.py::TestCleanlinessEvaluator::test_multiple_negative_labels PASSED

========== 5 passed in 0.12s ==========
```

---

## Step 5: Start API Server (30 sec)

```bash
# Run development server
python -m src.main
```

**Expected output**:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
🚀 Starting Dealer Hygiene Vision API
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## Step 6: Test API (1 min)

### Option A: Interactive Docs (Recommended)

1. **Open browser**: http://localhost:8000/docs
2. **Expand** `/api/v1/hygiene/analyze`
3. **Click** "Try it out"
4. **Fill in**:
   - `dealer_id`: dealer-001
   - `checkpoint_id`: reception
   - `image`: Upload any JPEG image
5. **Click** "Execute"

**Expected response**:
```json
{
  "audit_id": "123e4567-e89b-12d3-a456-426614174000",
  "dealer_id": "dealer-001",
  "checkpoint_id": "reception",
  "status": "CLEAN",
  "confidence": 92.5,
  "reason": "No cleanliness issues detected",
  "negative_labels": [],
  "analyzed_at": "2024-01-15T10:30:00Z"
}
```

### Option B: curl Command

```bash
# Download a sample image (or use your own)
curl -o test_image.jpg https://picsum.photos/800/600

# Test API
curl -X POST http://localhost:8000/api/v1/hygiene/analyze \
  -H "Authorization: Bearer valid-token" \
  -F "dealer_id=dealer-001" \
  -F "checkpoint_id=reception" \
  -F "image=@test_image.jpg"
```

### Option C: Python Script

### Option D: Smoke Test Script (Easiest)

We've included a script that mocks AWS dependencies for you:

```bash
python smoke_test.py
```

This will upload a dummy image and print the API response.

---

## ✅ Success Checklist

- [ ] Virtual environment created and activated
- [ ] Dependencies installed
- [ ] `.env` file configured
- [ ] S3 bucket created
- [ ] Unit tests pass
- [ ] API server running
- [ ] Test request returns valid response

---

## 🎯 Next Steps

### 1. Explore API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 2. Run All Tests
```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html

# View coverage report (Windows)
start htmlcov/index.html
```

### 3. Understand Architecture
Read these in order:
1. `README.md` - Project overview
2. `docs/architecture/adr/001-hexagonal-architecture.md` - Design decisions
3. `docs/architecture/diagrams/ARCHITECTURE_DIAGRAMS.md` - Visual diagrams
4. `docs/TESTING.md` - Testing strategy

### 4. Explore Code
Start here:
1. **Domain**: `src/domain/services/cleanliness_evaluator.py` (business logic)
2. **Use Case**: `src/application/use_cases/analyze_cleanliness.py` (orchestration)
3. **Adapter**: `src/infrastructure/vision/rekognition_adapter.py` (AWS integration)
4. **API**: `src/api/routes/hygiene.py` (endpoints)

### 5. Try Advanced Features

**Test different images**:
```bash
# Clean facility
curl ... -F "image=@clean_showroom.jpg"

# Dirty facility
curl ... -F "image=@messy_workshop.jpg"
```

**Adjust confidence threshold**:
```bash
curl ... -F "min_confidence=90.0" ...
```

**Check specific dealer stats**:
```bash
curl http://localhost:8000/api/v1/dealers/dealer-001/stats
```

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'src'"

**Solution**: Make sure you're in the project root and virtual environment is activated.
```bash
cd "e:/Project Files/Stellantis-Dealer-Hygiene-App"
venv\Scripts\activate
```

### Issue: "NoCredentialsError: Unable to locate credentials"

**Solution**: Configure AWS CLI with your credentials.
```bash
aws configure
# Enter:
#   AWS Access Key ID: YOUR_KEY
#   AWS Secret Access Key: YOUR_SECRET
#   Default region: us-east-1
#   Default output format: json
```

### Issue: "BucketAlreadyExists" or "BucketAlreadyOwnedByYou"

**Solution**: Use a unique bucket name in `.env`:
```bash
S3_BUCKET=stellantis-hygiene-YOUR-NAME-12345
```

### Issue: Tests fail with "moto" errors

**Solution**: Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

### Issue: "Port 8000 is already in use"

**Solution**: Kill existing process or use different port:
```bash
# Windows: Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port
uvicorn src.main:app --port 8001
```

---

## 📚 Additional Resources

### Documentation
- **Architecture**: `docs/architecture/`
- **Deployment**: `docs/deployment/DEPLOYMENT.md`
- **Testing**: `docs/TESTING.md`
- **Implementation**: `IMPLEMENTATION_SUMMARY.md`

### Code Examples
- **Unit Tests**: `tests/unit/domain/test_cleanliness_evaluator.py`
- **Integration Tests**: `tests/integration/test_rekognition_adapter.py`
- **Use Case**: `src/application/use_cases/analyze_cleanliness.py`

### AWS Resources
- [Amazon Rekognition Docs](https://docs.aws.amazon.com/rekognition/)
- [S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [IAM Policy Examples](docs/iam-policies/rekognition-policy.json)

### Learning Resources
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)

---

## 🎉 You're Ready!

You now have a production-grade vision pipeline running locally!

**What you have**:
- ✅ Clean Architecture with SOLID principles
- ✅ 80%+ test coverage
- ✅ Pluggable vision providers
- ✅ AWS Rekognition integration
- ✅ Comprehensive documentation
- ✅ Production-ready code

**What's next**:
1. Explore the codebase
2. Run integration tests
3. Try custom business rules
4. Deploy to AWS (see `docs/deployment/`)
5. Add custom ML models (see `tflite_adapter.py`)

---

## 💬 Need Help?

- **Issues**: Check `docs/` for detailed documentation
- **Architecture Questions**: See ADR in `docs/architecture/adr/`
- **AWS Setup**: See `docs/deployment/DEPLOYMENT.md`
- **Testing**: See `docs/TESTING.md`

---

**Happy coding! 🚀**
