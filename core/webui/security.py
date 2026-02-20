"""
WebUI Security Middleware
=========================
Middlewares de seguridad para FastAPI.
"""
import time
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from core.config import get_settings
from core.logging_config import get_logger

logger = get_logger("MININA.WebUI.Security")


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, requests_per_minute: int = 60, window_seconds: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.requests: Dict[str, list[float]] = {}
    
    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        """Check if request is allowed. Returns (allowed, retry_after)."""
        now = time.time()
        window_start = now - self.window_seconds
        
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]
        
        if len(self.requests[client_id]) >= self.requests_per_minute:
            retry_after = int(self.requests[client_id][0] + self.window_seconds - now)
            return False, max(1, retry_after)
        
        self.requests[client_id].append(now)
        return True, 0
    
    def cleanup_old_entries(self):
        """Clean up entries older than window."""
        now = time.time()
        window_start = now - self.window_seconds
        for client_id in list(self.requests.keys()):
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > window_start
            ]
            if not self.requests[client_id]:
                del self.requests[client_id]


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # HTTPS enforcement
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdnjs.cloudflare.com;"
        )
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=()"
        )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app):
        super().__init__(app)
        settings = get_settings()
        self.limiter = RateLimiter(
            requests_per_minute=settings.WEBUI_RATE_LIMIT,
            window_seconds=settings.WEBUI_RATE_LIMIT_WINDOW
        )
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        client_id = forwarded.split(",")[0].strip() if forwarded else client_ip
        
        # Check rate limit
        allowed, retry_after = self.limiter.is_allowed(client_id)
        
        if not allowed:
            logger.warning("Rate limit exceeded", extra={
                "client_id": client_id,
                "path": request.url.path
            })
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please slow down.",
                headers={"Retry-After": str(retry_after)}
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, get_settings().WEBUI_RATE_LIMIT - len(self.limiter.requests.get(client_id, [])))
        response.headers["X-RateLimit-Limit"] = str(get_settings().WEBUI_RATE_LIMIT)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
