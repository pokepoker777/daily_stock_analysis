# -*- coding: utf-8 -*-
"""
AstrBot notification channel.

Sends messages to an AstrBot instance via its HTTP API.
"""

from __future__ import annotations

import logging
from typing import Optional

import requests

from src.channels.base import BaseChannel, ChannelSendResult

logger = logging.getLogger(__name__)


class AstrBotChannel(BaseChannel):
    """Push messages via AstrBot HTTP API."""

    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
    ):
        self._url = url or ""
        self._token = token or ""

    @property
    def channel_name(self) -> str:
        return "ASTRBOT机器人"

    @property
    def channel_id(self) -> str:
        return "astrbot"

    def is_configured(self) -> bool:
        return bool(self._url)

    def send(self, content: str, **kwargs) -> ChannelSendResult:
        if not self.is_configured():
            return ChannelSendResult(
                success=False, channel_name=self.channel_name,
                error="AstrBot URL 未配置",
            )

        try:
            headers = {"Content-Type": "application/json"}
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"

            api_url = self._url.rstrip("/") + "/api/message/send"
            payload = {"message": [{"type": "text", "data": {"text": content}}]}

            resp = requests.post(api_url, json=payload, headers=headers, timeout=30)
            if resp.status_code not in (200, 201):
                logger.error(f"[AstrBot] HTTP {resp.status_code}: {resp.text[:200]}")
                return ChannelSendResult(
                    success=False, channel_name=self.channel_name,
                    error=f"HTTP {resp.status_code}",
                )
            return ChannelSendResult(success=True, channel_name=self.channel_name)
        except Exception as exc:
            logger.error(f"[AstrBot] 发送失败: {exc}")
            return ChannelSendResult(
                success=False, channel_name=self.channel_name, error=str(exc),
            )
