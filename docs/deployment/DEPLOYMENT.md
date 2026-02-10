# Deployment Guide

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- AWS Account with Rekognition access
- AWS CLI configured with credentials

### Setup

1. **Clone repository**
```bash
git clone <repo-url>
cd stellantis-hygiene-vision
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. **Configure environment**
```bash
cp .env .env
# Edit .env with your AWS settings
```

5. **Create S3 bucket**
```bash
aws s3 mb s3://stellantis-hygiene-images
```

6. **Run application**
```bash
python -m src.main
```

7. **Access API**
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Run Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires moto)
pytest tests/integration/ -v

# All tests with coverage
pytest --cov=src --cov-report=html
```

---

## Production Deployment

### Option 1: AWS Lambda + API Gateway

**WHY**: Serverless, auto-scaling, pay-per-request

#### Using AWS SAM

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  HygieneAPI:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: src.main.handler
      Runtime: python3.11
      MemorySize: 1024
      Timeout: 30
      Environment:
        Variables:
          S3_BUCKET: !Ref ImageBucket
          AWS_REGION: !Ref AWS::Region
      Policies:
        - S3CrudPolicy:
            BucketName: !Ref ImageBucket
        - Statement:
            - Effect: Allow
              Action:
                - rekognition:DetectLabels
              Resource: '*'
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY

  ImageBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: stellantis-hygiene-images
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: DeleteOldImages
            Status: Enabled
            ExpirationInDays: 2555  # 7 years retention
```

**Deploy**:
```bash
sam build
sam deploy --guided
```

**Cost**: ~$0.20 per 1,000 requests + Rekognition costs

---

### Option 2: AWS ECS Fargate

**WHY**: Containerized, more control, better for long-running processes

#### Prerequisites
```bash
# Build and push Docker image
docker build -t hygiene-api:latest .

# Tag and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag hygiene-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/hygiene-api:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/hygiene-api:latest
```

#### ECS Task Definition
```json
{
  "family": "hygiene-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "hygiene-api",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/hygiene-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "AWS_REGION", "value": "us-east-1"},
        {"name": "S3_BUCKET", "value": "stellantis-hygiene-images"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/hygiene-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**Deploy**:
```bash
aws ecs create-service \
  --cluster hygiene-cluster \
  --service-name hygiene-api \
  --task-definition hygiene-api \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

**Cost**: ~$35/month for 2 tasks (0.25 vCPU, 0.5 GB)

---

### Option 3: AWS App Runner

**WHY**: Simplest deployment, automatic scaling from source

```bash
# Create App Runner service
aws apprunner create-service \
  --service-name hygiene-api \
  --source-configuration '{
    "CodeRepository": {
      "RepositoryUrl": "https://github.com/your-org/hygiene-api",
      "SourceCodeVersion": {"Type": "BRANCH", "Value": "main"},
      "CodeConfiguration": {
        "ConfigurationSource": "API",
        "CodeConfigurationValues": {
          "Runtime": "PYTHON_3",
          "BuildCommand": "pip install -r requirements.txt",
          "StartCommand": "uvicorn src.main:app --host 0.0.0.0 --port 8000",
          "Port": "8000"
        }
      }
    }
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  }'
```

**Cost**: Pay-per-use, ~$25/month for low traffic

---

## Infrastructure as Code

### Terraform Example

```hcl
# main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# S3 Bucket
resource "aws_s3_bucket" "hygiene_images" {
  bucket = "stellantis-hygiene-images"
}

resource "aws_s3_bucket_versioning" "hygiene_images" {
  bucket = aws_s3_bucket.hygiene_images.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Lambda Function
resource "aws_lambda_function" "hygiene_api" {
  filename      = "deployment.zip"
  function_name = "hygiene-api"
  role          = aws_iam_role.lambda_role.arn
  handler       = "src.main.handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 1024

  environment {
    variables = {
      S3_BUCKET  = aws_s3_bucket.hygiene_images.id
      AWS_REGION = "us-east-1"
    }
  }
}

# API Gateway
resource "aws_apigatewayv2_api" "hygiene_api" {
  name          = "hygiene-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id           = aws_apigatewayv2_api.hygiene_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.hygiene_api.invoke_arn
}
```

**Deploy**:
```bash
terraform init
terraform plan
terraform apply
```

---

## Monitoring & Observability

### CloudWatch Dashboards

```python
# Create custom metrics
import boto3

cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='HygieneAPI',
    MetricData=[
        {
            'MetricName': 'AnalysisLatency',
            'Value': 1.5,
            'Unit': 'Seconds',
            'Dimensions': [
                {'Name': 'DealerId', 'Value': 'dealer-001'}
            ]
        }
    ]
)
```

### CloudWatch Alarms

```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name hygiene-api-high-errors \
  --alarm-description "Alert when error rate exceeds 5%" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

---

## Cost Optimization

### Rekognition Costs
- **Price**: $1.00 per 1,000 images (first 1M)
- **Optimization**: 
  - Cache results (don't re-analyze same image)
  - Use S3 URIs (no data transfer)
  - Implement request throttling

### S3 Costs
- **Storage**: $0.023 per GB/month
- **Optimization**:
  - Lifecycle policies (delete after 7 years)
  - Use S3 Intelligent-Tiering
  - Compress images before upload

### Example Monthly Cost (10,000 dealers, 100 images/month each)
- **Images**: 1,000,000 images/month
- **Rekognition**: $1,000
- **S3 Storage**: ~$50 (assuming 50GB average)
- **Lambda/API Gateway**: ~$100
- **Total**: ~$1,150/month

---

## Security Checklist

- [ ] Use IAM roles, not access keys
- [ ] Enable S3 bucket versioning
- [ ] Enable S3 server-side encryption
- [ ] Restrict S3 bucket policies to specific roles
- [ ] Enable CloudTrail logging
- [ ] Use VPC for ECS/Lambda
- [ ] Implement rate limiting
- [ ] Enable CORS only for trusted origins
- [ ] Use Secrets Manager for sensitive config
- [ ] Enable AWS WAF for DDoS protection

---

## Rollback Strategy

### Lambda
```bash
# Rollback to previous version
aws lambda update-alias \
  --function-name hygiene-api \
  --name prod \
  --function-version 5  # Previous stable version
```

### ECS
```bash
# Update service to previous task definition
aws ecs update-service \
  --cluster hygiene-cluster \
  --service hygiene-api \
  --task-definition hygiene-api:5  # Previous version
```

---

## Support

**Runbook**: See `docs/runbook.md`  
**Architecture**: See `docs/architecture/`  
**API Docs**: https://api.stellantis-hygiene.com/docs
