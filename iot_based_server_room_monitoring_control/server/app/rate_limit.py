from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import time
import redis
import os
from dotenv import load_dotenv
import logging
from typing import Optional

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