# -*- coding: utf-8 -*-
"""
Server酱3 (ServerChan3) notification channel.

Sends messages via the ServerChan3 HTTP API for mobile APP push.
"""

from __future__ import annotations

import logging
from typing import Optional

import requests

from src.channels.base import BaseChannel, ChannelSendResult

logger = logging.getLogger(__name__)

_SC3_API_TEMPLATE = "https://sctapi.ftqq.com/{sendkey}.send"


class ServerChan3Channel(BaseChannel):
    """Push messages via Server酱3."""

    def __init__(self, sendkey: Optional[str] = None):
        self._sendkey = sendkey or ""

    @property
    def channel_name(self) -> str:
        return "Server酱3"

    @property
    def channel_id(self) -> str:
        return "serverchan3"

    def is_configured(self) -> bool:
        return bool(self._sendkey)

    def send(self, content: str, **kwargs) -> ChannelSendResult:
        if not self.is_configured():
            return ChannelSendResult(
                success=False, channel_name=self.channel_name,
                error="Server酱3 sendkey 未配置",
            )

        title = kwargs.get("title", "股票分析报告")
        url = _SC3_API_TEMPLATE.format(sendkey=self._sendkey)
        try:
            resp = requests.post(
                url,
                json={"title": title, "desp": content},
                timeout=30,
            )
            data = resp.json()
            if data.get("code", -1) != 0:
                logger.error(f"[Server酱3] API error: {data}")
                return ChannelSendResult(
                    success=False, channel_name=self.channel_name,
                    error=str(data.get("message", "unknown")),
                )
            return ChannelSendResult(success=True, channel_name=self.channel_name)
        except Exception as exc:
            logger.error(f"[Server酱3] 发送失败: {exc}")
            return ChannelSendResult(
                success=False, channel_name=self.channel_name, error=str(exc),
            )
