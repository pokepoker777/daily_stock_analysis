# -*- coding: utf-8 -*-
"""
Abstract base class for all notification channels.

Every concrete channel (WeChat, Feishu, Telegram, …) must subclass
``BaseChannel`` and implement the required methods.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ChannelSendResult:
    """Result of a single send attempt."""

    success: bool
    channel_name: str
    error: Optional[str] = None
    chunks_sent: int = 1
    chunks_total: int = 1


class BaseChannel(ABC):
    """
    Contract that every notification channel must satisfy.

    Lifecycle
    ---------
    1. ``is_configured()`` – called once at startup to check availability.
    2. ``send(content)``   – called for each push; may be called concurrently.
    3. ``channel_name``    – human-readable label used in logs / UI.
    """

    # ------------------------------------------------------------------ #
    #  Identity
    # ------------------------------------------------------------------ #

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Human-readable channel name (e.g. '企业微信')."""
        ...

    @property
    @abstractmethod
    def channel_id(self) -> str:
        """Machine-readable identifier (e.g. 'wechat')."""
        ...

    # ------------------------------------------------------------------ #
    #  Configuration guard
    # ------------------------------------------------------------------ #

    @abstractmethod
    def is_configured(self) -> bool:
        """Return *True* when all required credentials / URLs are present."""
        ...

    # ------------------------------------------------------------------ #
    #  Send
    # ------------------------------------------------------------------ #

    @abstractmethod
    def send(self, content: str, **kwargs) -> ChannelSendResult:
        """
        Push *content* (Markdown) through this channel.

        Implementations should handle chunking, retries, and format
        conversion internally and **never** raise.  Errors are
        returned inside ``ChannelSendResult``.
        """
        ...

    # ------------------------------------------------------------------ #
    #  Helpers available to all subclasses
    # ------------------------------------------------------------------ #

    @staticmethod
    def _byte_len(text: str) -> int:
        """Return UTF-8 byte length of *text*."""
        return len(text.encode("utf-8"))

    @staticmethod
    def _chunk_by_bytes(text: str, max_bytes: int) -> list[str]:
        """
        Split *text* into chunks that each fit within *max_bytes* (UTF-8).

        Splitting is performed on line boundaries when possible.
        """
        if BaseChannel._byte_len(text) <= max_bytes:
            return [text]

        chunks: list[str] = []
        current_lines: list[str] = []
        current_size = 0

        for line in text.split("\n"):
            line_bytes = BaseChannel._byte_len(line) + 1  # +1 for '\n'
            if current_size + line_bytes > max_bytes and current_lines:
                chunks.append("\n".join(current_lines))
                current_lines = []
                current_size = 0
            current_lines.append(line)
            current_size += line_bytes

        if current_lines:
            chunks.append("\n".join(current_lines))

        return chunks

    def _safe_send(self, content: str, **kwargs) -> ChannelSendResult:
        """
        Wrapper that catches unexpected exceptions so the caller
        never has to worry about a single channel crashing the loop.
        """
        try:
            return self.send(content, **kwargs)
        except Exception as exc:
            logger.exception(f"[{self.channel_name}] 发送异常: {exc}")
            return ChannelSendResult(
                success=False,
                channel_name=self.channel_name,
                error=str(exc),
            )
