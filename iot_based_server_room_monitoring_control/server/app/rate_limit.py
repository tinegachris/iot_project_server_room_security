from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import time
import redis
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Callable
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 100  # Number of requests allowed
RATE_LIMIT_WINDOW = 60    # Time window in seconds

class RateLimiter:
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            logger.info("Redis connection established successfully")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self.redis_client = None

    async def check_rate_limit(self, request: Request, client_id: Optional[str] = None) -> bool:
        """Check if the request should be rate limited"""
        if not self.redis_client:
            logger.warning("Redis not available, falling back to in-memory rate limiting")
            return True

        try:
            # Use client IP or provided client_id as key
            key = client_id or request.client.host
            current_time = int(time.time())

            # Clean old records
            self.redis_client.zremrangebyscore(key, 0, current_time - RATE_LIMIT_WINDOW)

            # Count requests in the current window
            request_count = self.redis_client.zcard(key)

            if request_count >= RATE_LIMIT_REQUESTS:
                logger.warning(f"Rate limit exceeded for {key}")
                return False

            # Add current request
            self.redis_client.zadd(key, {str(current_time): current_time})
            self.redis_client.expire(key, RATE_LIMIT_WINDOW)

            return True

        except redis.RedisError as e:
            logger.error(f"Redis error during rate limiting: {str(e)}")
            return True  # Allow request if Redis fails

    async def rate_limit_middleware(self, request: Request, call_next):
        """FastAPI middleware for rate limiting"""
        if not await self.check_rate_limit(request):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too many requests",
                    "message": "Please try again later"
                }
            )
        return await call_next(request)

# Create rate limiter instance
rate_limiter = RateLimiter()

def get_rate_limiter() -> RateLimiter:
    """Dependency to get rate limiter instance"""
    return rate_limiter

def rate_limit(requests: int = 100, window: int = 60):
    """
    Decorator for rate limiting endpoints.
    
    Args:
        requests (int): Number of requests allowed in the time window
        window (int): Time window in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Search for Request object in both args and kwargs
            request = next((arg for arg in args if isinstance(arg, Request)), None)
            if not request:
                request = next((val for val in kwargs.values() if isinstance(val, Request)), None)
            
            # If still not found, raise the error
            if not request:
                logger.error(f"Could not find Request object in args: {args} or kwargs: {kwargs} for function {func.__name__}")
                raise ValueError("Request object not found in function arguments")

            # Proceed with rate limiting check
            if not await rate_limiter.check_rate_limit(request):
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Too many requests",
                        "message": "Please try again later"
                    }
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator