"""
Simple rate limiting middleware for DeskMate API.

Implements token bucket algorithm for rate limiting API requests.
"""

import time
import logging
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import config

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket implementation for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        now = time.time()

        # Refill tokens based on time elapsed
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        # Try to consume tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using token bucket algorithm."""

    def __init__(self, app, calls_per_minute: int = None):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute or config.security.rate_limit_per_minute
        self.buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(self.calls_per_minute, self.calls_per_minute / 60.0)
        )
        self.cleanup_interval = 300  # Clean up old buckets every 5 minutes
        self.last_cleanup = time.time()

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers (common in production)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        forwarded = request.headers.get("X-Forwarded")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct connection IP
        if hasattr(request.client, "host"):
            return request.client.host

        return "unknown"

    def cleanup_old_buckets(self):
        """Remove inactive buckets to prevent memory leaks."""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return

        # Remove buckets that haven't been used recently
        inactive_threshold = now - 3600  # 1 hour
        to_remove = []

        for ip, bucket in self.buckets.items():
            if bucket.last_refill < inactive_threshold:
                to_remove.append(ip)

        for ip in to_remove:
            del self.buckets[ip]

        self.last_cleanup = now
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} inactive rate limit buckets")

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/docs", "/openapi.json"] or request.url.path.startswith("/static"):
            return await call_next(request)

        # Get client IP
        client_ip = self.get_client_ip(request)

        # Clean up old buckets periodically
        self.cleanup_old_buckets()

        # Check rate limit
        bucket = self.buckets[client_ip]
        if not bucket.consume():
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {self.calls_per_minute} requests per minute allowed.",
                headers={"Retry-After": "60"}
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(int(bucket.tokens))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))

        return response