# -*- coding: utf-8 -*-
"""
===================================
API Authentication Middleware
===================================

Provides optional API key authentication for the FastAPI application.
When API_AUTH_TOKEN is set in environment variables, all /api/* endpoints
require a valid Bearer token or X-API-Key header.

Public endpoints (health check, root, static files) are always accessible.

Usage:
    # In .env
    API_AUTH_TOKEN=your-secret-token-here

    # Client request
    curl -H "Authorization: Bearer your-secret-token-here" http://localhost:8000/api/v1/...
    # or
    curl -H "X-API-Key: your-secret-token-here" http://localhost:8000/api/v1/...
"""

import hashlib
import hmac
import logging
import os
import secrets
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Paths that never require authentication
PUBLIC_PATHS = frozenset({
    "/",
    "/api/health",
    "/docs",
    "/redoc",
    "/openapi.json",
})

# Path prefixes that never require authentication
PUBLIC_PREFIXES = (
    "/assets/",
    "/static/",
)


def _constant_time_compare(a: str, b: str) -> bool:
    """Timing-safe string comparison to prevent timing attacks."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


class APIAuthMiddleware(BaseHTTPMiddleware):
    """
    Optional API key authentication middleware.

    Behavior:
    - If API_AUTH_TOKEN is NOT set: all requests pass through (no auth).
    - If API_AUTH_TOKEN is set: /api/* requests must provide valid credentials.
    - Health check, docs, and static files are always public.

    Accepted credential formats:
    1. Authorization: Bearer <token>
    2. X-API-Key: <token>
    3. Query parameter: ?api_key=<token>
    """

    def __init__(self, app, auth_token: Optional[str] = None):
        super().__init__(app)
        self._auth_token = auth_token or os.getenv("API_AUTH_TOKEN", "")
        if self._auth_token:
            logger.info("[Auth] API authentication enabled (API_AUTH_TOKEN is set)")
        else:
            logger.info("[Auth] API authentication disabled (API_AUTH_TOKEN not set, all requests allowed)")

    def _is_public_path(self, path: str) -> bool:
        """Check if the path is public (no auth required)."""
        if path in PUBLIC_PATHS:
            return True
        for prefix in PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return True
        # Non-API paths (frontend SPA routes) are public
        if not path.startswith("/api/"):
            return True
        return False

    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract authentication token from request headers or query params."""
        # 1. Authorization: Bearer <token>
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            return auth_header[7:].strip()

        # 2. X-API-Key header
        api_key = request.headers.get("x-api-key", "")
        if api_key:
            return api_key.strip()

        # 3. Query parameter fallback
        api_key_param = request.query_params.get("api_key", "")
        if api_key_param:
            return api_key_param.strip()

        return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Authenticate API requests when API_AUTH_TOKEN is configured."""
        # No auth token configured -> pass through
        if not self._auth_token:
            return await call_next(request)

        # Public paths -> pass through
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Extract and validate token
        provided_token = self._extract_token(request)

        if not provided_token:
            logger.warning(f"[Auth] Unauthenticated request to {request.url.path} from {request.client.host}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": "unauthorized",
                    "message": "Authentication required. Provide API key via "
                               "'Authorization: Bearer <token>' header or 'X-API-Key' header.",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not _constant_time_compare(provided_token, self._auth_token):
            logger.warning(f"[Auth] Invalid API key for {request.url.path} from {request.client.host}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "forbidden",
                    "message": "Invalid API key.",
                },
            )

        # Token valid
        return await call_next(request)


def generate_api_token() -> str:
    """Generate a cryptographically secure API token (utility function)."""
    return secrets.token_urlsafe(32)
