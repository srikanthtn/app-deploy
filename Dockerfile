# ============================================================================
# Multi-Stage Dockerfile for Clone-it Backend
# Supports AWS Rekognition + Gemini Vision Fallback
# Author: Srikanth Thiyagarajan
# ============================================================================

# === Stage 1: Builder ===
# WHY: Build dependencies in separate stage to reduce final image size by 60-80%
FROM python:3.13-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /build

# Install build dependencies
# WHY: gcc needed for some Python packages (psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching optimization)
COPY requirements.txt .

# Install Python dependencies to /install
# WHY: --prefix=/install allows us to copy only installed packages to final image
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================================================
# === Stage 2: Runtime ===
# WHY: Minimal runtime image without build tools
FROM python:3.13-slim

# Metadata
LABEL maintainer="Srikanth Thiyagarajan"
LABEL description="Clone-it Backend API with AWS Rekognition + Gemini Vision Fallback"
LABEL version="2.0.0"
LABEL org.opencontainers.image.source="https://github.com/yourusername/clone-it"

# Install runtime dependencies only
# WHY: curl for health checks, libpq for PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
# WHY: Never run containers as root in production (security best practice)
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser scripts/ /app/scripts/
COPY --chown=appuser:appuser run.py /app/

# Create logs directory
RUN mkdir -p /app/logs && chown appuser:appuser /app/logs

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
# WHY: Container orchestrators (ECS, K8s) use this to determine service health
# Checks every 30s, timeout after 10s, wait 40s before first check, fail after 3 retries
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Environment variables
# WHY: PYTHONUNBUFFERED ensures logs appear immediately (critical for debugging)
# WHY: PYTHONDONTWRITEBYTECODE prevents .pyc files (smaller image, faster startup)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000

# Production startup command
# WHY: uvicorn with multiple workers for production performance
# Workers = (2 x CPU cores) + 1 is a good starting point
# --workers 4 works well for most deployments on 2-core instances
# For high-traffic, increase workers or use gunicorn + uvicorn workers
CMD ["uvicorn", "src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--log-level", "info", \
     "--access-log", \
     "--no-use-colors"]

# ============================================================================
# Build Instructions:
# docker build -t clone-it-backend:latest .
#
# Run Instructions (Development - with .env file):
# docker run -p 8000:8000 --env-file .env clone-it-backend:latest
#
# Run Instructions (Production - with environment variables):
# docker run -p 8000:8000 \
#   -e AWS_ACCESS_KEY_ID=your_key \
#   -e AWS_SECRET_ACCESS_KEY=your_secret \
#   -e GEMINI_API_KEY=your_gemini_key \
#   -e VISION_PROVIDER=fallback \
#   -e DATABASE_URL=your_database_url \
#   clone-it-backend:latest
#
# Debug Shell:
# docker run -it --entrypoint /bin/bash clone-it-backend:latest
# ============================================================================
