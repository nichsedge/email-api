from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
import structlog
import time
import os
from contextlib import asynccontextmanager

from models.database import create_tables, get_db
from utils.auth import get_current_api_key
from utils.rate_limiter import rate_limit_middleware
from api.endpoints import router as api_router
from schemas import HealthCheckResponse, ErrorResponse

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global variables for uptime tracking
start_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Email API application")
    create_tables()
    logger.info("Database tables created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Email API application")

# Create FastAPI app
app = FastAPI(
    title="Secure Email API",
    description="A secure FastAPI email service with authentication and rate limiting",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add HTTPS redirect middleware (for production)
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log request
    logger.info(
        "Request processed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time,
        client_ip=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )
    
    # Add processing time to response headers
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url),
        method=request.method,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP Error",
            message=str(exc.detail),
            details={"url": str(request.url), "method": request.method}
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(
        "Unexpected error occurred",
        error=str(exc),
        url=str(request.url),
        method=request.method,
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            message="An unexpected error occurred",
            details={"url": str(request.url), "method": request.method}
        ).dict()
    )

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Secure Email API is running",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "operational"
    }

# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - start_time
    
    return HealthCheckResponse(
        status="healthy",
        timestamp=time.time(),
        version="2.0.0",
        database="connected",
        uptime=uptime
    )

# API key authentication dependency
async def get_authenticated_api_key(request: Request):
    """Get authenticated API key from request"""
    # Extract authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    # Parse authorization header
    try:
        scheme, credentials = auth_header.split(" ", 1)
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        
        # Split credentials into key_id and secret_key
        if ":" not in credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization format. Use: Bearer key_id:secret_key"
            )
        
        key_id, secret_key = credentials.split(":", 1)
        
        # Verify API key
        from models.database import APIKey
        from utils.auth import verify_api_key
        
        db = next(get_db())
        api_key = verify_api_key(key_id, secret_key, db)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive API key"
            )
        
        # Store API key in request state for rate limiting
        request.state.api_key = api_key
        
        return api_key
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

# Apply authentication to all API routes (except health check)
@app.middleware("http")
async def authenticate_api_requests(request: Request, call_next):
    """Authenticate API requests"""
    # Skip authentication for health check and root endpoint
    if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    # Check if it's an API route
    if request.url.path.startswith("/api/"):
        try:
            await get_authenticated_api_key(request)
        except HTTPException:
            # Return 401 for unauthenticated API requests
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=ErrorResponse(
                    error="Authentication Required",
                    message="Valid API key authentication is required"
                ).dict()
            )
    
    return await call_next(request)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to responses"""
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Add Content Security Policy (adjust as needed for your use case)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    
    return response

# Metrics endpoint (for monitoring)
@app.get("/api/v1/metrics")
async def get_metrics():
    """Get application metrics"""
    # This would typically integrate with Prometheus or similar monitoring
    return {
        "total_requests": 0,  # Would be tracked globally
        "active_connections": 0,  # Would be tracked
        "uptime": time.time() - start_time,
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_secure:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
        log_level="info"
    )