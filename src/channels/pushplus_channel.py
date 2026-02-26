# -*- coding: utf-8 -*-
"""
PushPlus (国内推送服务) notification channel.

Sends messages via the PushPlus HTTP API.
"""

from __future__ import annotations

import logging
from typing import Optional

import requests

from src.channels.base import BaseChannel, ChannelSendResult

logger = logging.getLogger(__name__)

_PUSHPLUS_API_URL = "http://www.pushplus.plus/send"


class PushPlusChannel(BaseChannel):
    """Push messages via PushPlus."""

    def __init__(self, token: Optional[str] = None):
        self._token = token or ""

    @property
    def channel_name(self) -> str:
        return "PushPlus"

    @property
    def channel_id(self) -> str:
        return "pushplus"

    def is_configured(self) -> bool:
        return bool(self._token)

    def send(self, content: str, **kwargs) -> ChannelSendResult:
        if not self.is_configured():
            return ChannelSendResult(
                success=False, channel_name=self.channel_name,
                error="PushPlus token 未配置",
            )

        title = kwargs.get("title", "股票分析报告")
        try:
            resp = requests.post(
                _PUSHPLUS_API_URL,
                json={"token": self._token, "title": title,
                      "content": content, "template": "markdown"},
                timeout=30,
            )
            data = resp.json()
            if data.get("code", -1) != 200:
                logger.error(f"[PushPlus] API error: {data}")
                return ChannelSendResult(
                    success=False, channel_name=self.channel_name,
                    error=str(data.get("msg", "unknown")),
                )
            return ChannelSendResult(success=True, channel_name=self.channel_name)
        except Exception as exc:
            logger.error(f"[PushPlus] 发送失败: {exc}")
            return ChannelSendResult(
                success=False, channel_name=self.channel_name, error=str(exc),
            )
