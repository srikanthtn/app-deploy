"""
Correlation ID Middleware

WHY: Distributed tracing - track requests across services.

Every request gets a unique correlation ID:
- Logged with every log message
- Returned in response headers
- Passed to downstream services
- Essential for debugging in production
"""
import uuid
from contextvars import ContextVar
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# WHY: ContextVar is thread-safe storage for correlation ID
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default=None)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Inject correlation ID into every request.
    
    Flow:
    1. Check if client sent X-Correlation-ID header
    2. If not, generate new UUID
    3. Store in context variable (accessible to all loggers)
    4. Add to response headers
    """
    
    async def dispatch(self, request: Request, call_next):
        # Get or generate correlation ID
        correlation_id = request.headers.get('X-Correlation-ID') or str(uuid.uuid4())
        
        # Store in context
        correlation_id_var.set(correlation_id)
        
        # Add to request state (accessible in endpoints)
        request.state.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add to response headers
        response.headers['X-Correlation-ID'] = correlation_id
        
        return response


def get_correlation_id() -> str:
    """
    Get current correlation ID.
    
    WHY: Loggers/services can retrieve correlation ID without passing it explicitly.
    """
    return correlation_id_var.get()
