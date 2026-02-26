# -*- coding: utf-8 -*-
"""
Pushover notification channel.

Sends push notifications to mobile/desktop devices via the Pushover API.
Supports automatic chunking for the 1024-character message limit.
"""

from __future__ import annotations

import logging
from typing import Optional

import requests

from src.channels.base import BaseChannel, ChannelSendResult

logger = logging.getLogger(__name__)

_PUSHOVER_MAX_CHARS = 1024
_PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"


class PushoverChannel(BaseChannel):
    """Push messages via the Pushover API."""

    def __init__(
        self,
        user_key: Optional[str] = None,
        api_token: Optional[str] = None,
    ):
        self._user_key = user_key or ""
        self._api_token = api_token or ""

    # -- Identity ----------------------------------------------------------

    @property
    def channel_name(self) -> str:
        return "Pushover"

    @property
    def channel_id(self) -> str:
        return "pushover"

    # -- Config guard ------------------------------------------------------

    def is_configured(self) -> bool:
        return bool(self._user_key and self._api_token)

    # -- Send --------------------------------------------------------------

    def send(self, content: str, **kwargs) -> ChannelSendResult:
        if not self.is_configured():
            return ChannelSendResult(
                success=False,
                channel_name=self.channel_name,
                error="Pushover user_key 或 api_token 未配置",
            )

        title = kwargs.get("title", "股票分析报告")

        # Strip markdown for Pushover (plain text works best)
        plain = self._strip_markdown(content)
        chunks = self._split_chars(plain, _PUSHOVER_MAX_CHARS)
        total = len(chunks)
        sent = 0

        for idx, chunk in enumerate(chunks, 1):
            chunk_title = f"{title} ({idx}/{total})" if total > 1 else title
            ok = self._post(chunk, chunk_title)
            if ok:
                sent += 1

        success = sent == total
        return ChannelSendResult(
            success=success,
            channel_name=self.channel_name,
            chunks_sent=sent,
            chunks_total=total,
            error=None if success else f"{total - sent}/{total} chunks failed",
        )

    # -- Internal ----------------------------------------------------------

    def _post(self, message: str, title: str) -> bool:
        try:
            resp = requests.post(
                _PUSHOVER_API_URL,
                data={
                    "token": self._api_token,
                    "user": self._user_key,
                    "title": title,
                    "message": message,
                    "html": 0,
                },
                timeout=30,
            )
            if resp.status_code != 200:
                data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                logger.error(f"[Pushover] HTTP {resp.status_code}: {data}")
                return False
            return True
        except Exception as exc:
            logger.error(f"[Pushover] 发送失败: {exc}")
            return False

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """Rough markdown stripping for plain-text channels."""
        import re
        text = re.sub(r"#{1,6}\s*", "", text)
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"\*(.*?)\*", r"\1", text)
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        return text.strip()

    @staticmethod
    def _split_chars(text: str, max_len: int) -> list[str]:
        if len(text) <= max_len:
            return [text]
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0
        for line in text.split("\n"):
            line_len = len(line) + 1
            if current_len + line_len > max_len and current:
                chunks.append("\n".join(current))
                current = []
                current_len = 0
            current.append(line)
            current_len += line_len
        if current:
            chunks.append("\n".join(current))
        return chunks
