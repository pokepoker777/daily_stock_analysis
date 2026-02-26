# -*- coding: utf-8 -*-
"""
Discord notification channel.

Supports both Discord Webhook and Bot Token modes.
Automatically chunks messages to respect the 2000-character limit.
"""

from __future__ import annotations

import logging
from typing import Optional

import requests

from src.channels.base import BaseChannel, ChannelSendResult

logger = logging.getLogger(__name__)

_DISCORD_MAX_CHARS = 2000


class DiscordChannel(BaseChannel):
    """Push messages via Discord Webhook or Bot API."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        channel_id: Optional[str] = None,
        webhook_url: Optional[str] = None,
    ):
        self._bot_token = bot_token or ""
        self._channel_id = channel_id or ""
        self._webhook_url = webhook_url or ""

    @property
    def channel_name(self) -> str:
        return "Discord机器人"

    @property
    def channel_id_str(self) -> str:
        return "discord"

    # Satisfy ABC
    @property
    def channel_id(self) -> str:
        return "discord"

    def is_configured(self) -> bool:
        bot_ok = bool(self._bot_token and self._channel_id)
        webhook_ok = bool(self._webhook_url)
        return bot_ok or webhook_ok

    def send(self, content: str, **kwargs) -> ChannelSendResult:
        if not self.is_configured():
            return ChannelSendResult(
                success=False, channel_name=self.channel_name,
                error="Discord bot_token/channel_id 或 webhook_url 未配置",
            )

        chunks = self._split_chars(content, _DISCORD_MAX_CHARS)
        total = len(chunks)
        sent = 0

        for chunk in chunks:
            ok = self._send_webhook(chunk) if self._webhook_url else self._send_bot(chunk)
            if ok:
                sent += 1

        success = sent == total
        return ChannelSendResult(
            success=success, channel_name=self.channel_name,
            chunks_sent=sent, chunks_total=total,
            error=None if success else f"{total - sent}/{total} chunks failed",
        )

    # -- Internal ----------------------------------------------------------

    def _send_webhook(self, text: str) -> bool:
        try:
            resp = requests.post(
                self._webhook_url,
                json={"content": text},
                timeout=30,
            )
            if resp.status_code not in (200, 204):
                logger.error(f"[Discord Webhook] HTTP {resp.status_code}: {resp.text[:200]}")
                return False
            return True
        except Exception as exc:
            logger.error(f"[Discord Webhook] 发送失败: {exc}")
            return False

    def _send_bot(self, text: str) -> bool:
        try:
            url = f"https://discord.com/api/v10/channels/{self._channel_id}/messages"
            headers = {"Authorization": f"Bot {self._bot_token}"}
            resp = requests.post(url, json={"content": text}, headers=headers, timeout=30)
            if resp.status_code not in (200, 201):
                logger.error(f"[Discord Bot] HTTP {resp.status_code}: {resp.text[:200]}")
                return False
            return True
        except Exception as exc:
            logger.error(f"[Discord Bot] 发送失败: {exc}")
            return False

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
