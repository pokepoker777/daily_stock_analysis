# -*- coding: utf-8 -*-
"""
Telegram Bot notification channel.

Sends messages via the Telegram Bot API with automatic chunking
for the 4096-character limit and MarkdownV2 escaping.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

import requests

from src.channels.base import BaseChannel, ChannelSendResult

logger = logging.getLogger(__name__)

_TELEGRAM_MAX_CHARS = 4096


class TelegramChannel(BaseChannel):
    """Push messages through a Telegram Bot."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        message_thread_id: Optional[str] = None,
    ):
        self._bot_token = bot_token or ""
        self._chat_id = chat_id or ""
        self._message_thread_id = message_thread_id

    # -- Identity ----------------------------------------------------------

    @property
    def channel_name(self) -> str:
        return "Telegram"

    @property
    def channel_id(self) -> str:
        return "telegram"

    # -- Config guard ------------------------------------------------------

    def is_configured(self) -> bool:
        return bool(self._bot_token and self._chat_id)

    # -- Send --------------------------------------------------------------

    def send(self, content: str, **kwargs) -> ChannelSendResult:
        if not self.is_configured():
            return ChannelSendResult(
                success=False,
                channel_name=self.channel_name,
                error="Telegram bot_token 或 chat_id 未配置",
            )

        api_url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        chunks = self._split_text(content, _TELEGRAM_MAX_CHARS)
        total = len(chunks)
        sent = 0

        for chunk in chunks:
            ok = self._post(api_url, chunk)
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

    def _post(self, api_url: str, text: str) -> bool:
        try:
            payload = {
                "chat_id": self._chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            }
            if self._message_thread_id:
                payload["message_thread_id"] = self._message_thread_id

            resp = requests.post(api_url, json=payload, timeout=30)
            data = resp.json()
            if not data.get("ok"):
                # Fallback: retry without parse_mode
                logger.warning(
                    f"[Telegram] Markdown 发送失败, 降级为纯文本: "
                    f"{data.get('description', 'unknown')}"
                )
                payload["parse_mode"] = ""
                resp = requests.post(api_url, json=payload, timeout=30)
                data = resp.json()
                if not data.get("ok"):
                    logger.error(f"[Telegram] 纯文本也失败: {data}")
                    return False
            return True
        except Exception as exc:
            logger.error(f"[Telegram] 发送失败: {exc}")
            return False

    @staticmethod
    def _split_text(text: str, max_len: int) -> list[str]:
        """Split by character count, preferring line boundaries."""
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
