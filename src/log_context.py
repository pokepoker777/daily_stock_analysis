# -*- coding: utf-8 -*-
"""
===================================
Structured Logging with Correlation IDs
===================================

Provides request-scoped correlation IDs so that every log line
produced during a single stock analysis run (or API request) can
be traced back to the same logical operation.

Usage::

    from src.log_context import correlation_ctx, get_correlation_id

    with correlation_ctx(stock_code="600519"):
        logger.info("Starting analysis")   # auto-tagged with correlation_id
        ...

The correlation ID is stored in a ``contextvars.ContextVar`` so it
is safe to use with both threading and asyncio.
"""

from __future__ import annotations

import logging
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Optional

# ------------------------------------------------------------------ #
#  Context variable (thread + async safe)
# ------------------------------------------------------------------ #

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
_stock_code: ContextVar[str] = ContextVar("stock_code", default="")


def get_correlation_id() -> str:
    """Return the current correlation ID, or empty string if unset."""
    return _correlation_id.get()


def get_stock_code() -> str:
    """Return the current stock code context, or empty string if unset."""
    return _stock_code.get()


@contextmanager
def correlation_ctx(
    stock_code: str = "",
    cid: Optional[str] = None,
):
    """
    Context manager that sets a correlation ID for the current scope.

    Parameters
    ----------
    stock_code : str
        Optional stock code to include in every log line.
    cid : str, optional
        Explicit correlation ID.  If *None* a new UUID-based short ID
        is generated automatically.
    """
    cid = cid or _make_short_id()
    tok_cid = _correlation_id.set(cid)
    tok_code = _stock_code.set(stock_code)
    try:
        yield cid
    finally:
        _correlation_id.reset(tok_cid)
        _stock_code.reset(tok_code)


# ------------------------------------------------------------------ #
#  Custom log filter (injects fields into every LogRecord)
# ------------------------------------------------------------------ #

class CorrelationFilter(logging.Filter):
    """
    Logging filter that adds ``correlation_id`` and ``stock_code``
    attributes to every ``LogRecord``.

    Attach it to the root logger (or any handler) once at startup::

        logging.getLogger().addFilter(CorrelationFilter())

    Then use the fields in your format string::

        fmt = "%(asctime)s [%(correlation_id)s] %(stock_code)s %(message)s"
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = _correlation_id.get()  # type: ignore[attr-defined]
        record.stock_code = _stock_code.get()  # type: ignore[attr-defined]
        return True


# ------------------------------------------------------------------ #
#  Setup helper
# ------------------------------------------------------------------ #

def install_correlation_filter(logger_name: Optional[str] = None) -> None:
    """
    Convenience function to install ``CorrelationFilter`` on the
    given logger (default: root logger).

    Safe to call multiple times — duplicate filters are skipped.
    """
    target = logging.getLogger(logger_name)
    if not any(isinstance(f, CorrelationFilter) for f in target.filters):
        target.addFilter(CorrelationFilter())


# ------------------------------------------------------------------ #
#  Internals
# ------------------------------------------------------------------ #

def _make_short_id() -> str:
    """Generate a short 8-char hex correlation ID."""
    return uuid.uuid4().hex[:8]
