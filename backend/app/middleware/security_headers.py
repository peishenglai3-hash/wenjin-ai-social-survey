"""Security headers middleware — adds OWASP-recommended HTTP security headers."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        headers = {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
            "Cache-Control": "no-store, max-age=0",
            "Server": "",  # Hide server header
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob: https:; "
                "connect-src 'self' https:; "
                "font-src 'self'; "
                "frame-src 'self'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
        }

        for key, value in headers.items():
            if key not in response.headers:
                response.headers[key] = value

        return response
