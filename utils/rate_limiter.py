import time
import threading
from typing import Dict, List, Optional
from collections import defaultdict, deque
from fastapi import HTTPException, status, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import structlog

logger = structlog.get_logger(__name__)

# Global rate limit storage
class RateLimitStore:
    def __init__(self):
        self._api_key_limits: Dict[str, deque] = defaultdict(deque)
        self._ip_limits: Dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()
    
    def cleanup_expired(self, window_seconds: int):
        """Clean up expired entries"""
        current_time = time.time()
        
        with self._lock:
            # Clean API key limits
            for key in list(self._api_key_limits.keys()):
                self._api_key_limits[key] = deque(
                    (timestamp, count) for timestamp, count in self._api_key_limits[key]
                    if current_time - timestamp < window_seconds
                )
                if not self._api_key_limits[key]:
                    del self._api_key_limits[key]
            
            # Clean IP limits
            for ip in list(self._ip_limits.keys()):
                self._ip_limits[ip] = deque(
                    (timestamp, count) for timestamp, count in self._ip_limits[ip]
                    if current_time - timestamp < window_seconds
                )
                if not self._ip_limits[ip]:
                    del self._ip_limits[ip]
    
    def check_rate_limit(self, identifier: str, limit: int, window_seconds: int, 
                        is_api_key: bool = True) -> bool:
        """Check if rate limit is exceeded"""
        current_time = time.time()
        store = self._api_key_limits if is_api_key else self._ip_limits
        
        with self._lock:
            # Remove expired entries
            store[identifier] = deque(
                (timestamp, count) for timestamp, count in store[identifier]
                if current_time - timestamp < window_seconds
            )
            
            # Check if limit exceeded
            if len(store[identifier]) >= limit:
                return False
            
            # Add current request
            store[identifier].append((current_time, 1))
            return True
    
    def get_remaining_requests(self, identifier: str, limit: int, window_seconds: int,
                             is_api_key: bool = True) -> int:
        """Get remaining requests for identifier"""
        current_time = time.time()
        store = self._api_key_limits if is_api_key else self._ip_limits
        
        with self._lock:
            # Remove expired entries
            store[identifier] = deque(
                (timestamp, count) for timestamp, count in store[identifier]
                if current_time - timestamp < window_seconds
            )
            
            return max(0, limit - len(store[identifier]))

# Global rate limit store
rate_limit_store = RateLimitStore()

# Create limiter instance
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])

class APIKeyRateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
    
    def check_rate_limit(self, api_key_id: str, rate_limit_per_minute: int, 
                        rate_limit_per_hour: int) -> tuple[bool, int, int]:
        """Check API key rate limits"""
        current_time = time.time()
        
        with self._lock:
            # Check per-minute limit
            minute_limit = rate_limit_store.check_rate_limit(
                f"api_key:{api_key_id}:minute", 
                rate_limit_per_minute, 
                60, 
                is_api_key=True
            )
            
            # Check per-hour limit
            hour_limit = rate_limit_store.check_rate_limit(
                f"api_key:{api_key_id}:hour", 
                rate_limit_per_hour, 
                3600, 
                is_api_key=True
            )
            
            # Get remaining requests
            remaining_minute = rate_limit_store.get_remaining_requests(
                f"api_key:{api_key_id}:minute", 
                rate_limit_per_minute, 
                60, 
                is_api_key=True
            )
            
            remaining_hour = rate_limit_store.get_remaining_requests(
                f"api_key:{api_key_id}:hour", 
                rate_limit_per_hour, 
                3600, 
                is_api_key=True
            )
            
            return minute_limit and hour_limit, remaining_minute, remaining_hour

# Global rate limiter instance
api_key_rate_limiter = APIKeyRateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware for API keys"""
    # Skip rate limiting for health check
    if request.url.path == "/":
        return await call_next(request)
    
    # Get API key from request state (set by auth middleware)
    api_key = getattr(request.state, 'api_key', None)
    
    if api_key:
        # Check rate limits
        allowed, remaining_minute, remaining_hour = api_key_rate_limiter.check_rate_limit(
            api_key.key_id,
            api_key.rate_limit_per_minute,
            api_key.rate_limit_per_hour
        )
        
        if not allowed:
            logger.warning("Rate limit exceeded", 
                         key_id=api_key.key_id,
                         endpoint=request.url.path,
                         method=request.method)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "remaining_minute": remaining_minute,
                    "remaining_hour": remaining_hour
                }
            )
        
        # Add rate limit info to response headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit-Minute"] = str(api_key.rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(remaining_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(api_key.rate_limit_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(remaining_hour)
        
        return response
    else:
        # If no API key, use IP-based rate limiting
        return await call_next(request)

def cleanup_expired_rate_limits():
    """Background task to clean up expired rate limit entries"""
    rate_limit_store.cleanup_expired(3600)  # Clean up entries older than 1 hour

# Dependency for rate limiting API keys
def check_api_key_rate_limit(api_key):
    """Dependency to check API key rate limit"""
    allowed, remaining_minute, remaining_hour = api_key_rate_limiter.check_rate_limit(
        api_key.key_id,
        api_key.rate_limit_per_minute,
        api_key.rate_limit_per_hour
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "remaining_minute": remaining_minute,
                "remaining_hour": remaining_hour
            }
        )
    
    return True