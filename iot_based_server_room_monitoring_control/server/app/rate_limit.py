from fastapi import HTTPException, Request
from datetime import datetime, timedelta
from typing import Dict, Tuple
import time

class RateLimiter:
    def __init__(self, requests: int, window: int):
        self.requests = requests
        self.window = window
        self.requests_per_ip: Dict[str, list] = {}

    def is_rate_limited(self, ip: str) -> Tuple[bool, int]:
        """Check if an IP is rate limited."""
        now = datetime.now()
        if ip not in self.requests_per_ip:
            self.requests_per_ip[ip] = []
        
        # Remove old timestamps
        self.requests_per_ip[ip] = [
            ts for ts in self.requests_per_ip[ip]
            if now - ts < timedelta(seconds=self.window)
        ]
        
        # Check if rate limit is exceeded
        if len(self.requests_per_ip[ip]) >= self.requests:
            return True, self.window - (now - self.requests_per_ip[ip][0]).seconds
        
        # Add new timestamp
        self.requests_per_ip[ip].append(now)
        return False, 0

# Create rate limiter instances
rate_limiters: Dict[str, RateLimiter] = {}

def rate_limit(requests: int, window: int):
    """Rate limiting decorator."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = next((arg for arg in args if isinstance(arg, Request)), None)
            if not request:
                return await func(*args, **kwargs)
            
            ip = request.client.host
            limiter_key = f"{func.__name__}:{ip}"
            
            if limiter_key not in rate_limiters:
                rate_limiters[limiter_key] = RateLimiter(requests, window)
            
            is_limited, wait_time = rate_limiters[limiter_key].is_rate_limited(ip)
            
            if is_limited:
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many requests. Please wait {wait_time} seconds."
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator 