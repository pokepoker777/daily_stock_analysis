# -*- coding: utf-8 -*-
"""
Custom Webhook notification channel.

Sends POST requests with Markdown content to user-defined webhook URLs.
Supports optional Bearer token authentication.
"""

from __future__ import annotations

import logging
from typing import List, Optional

import requests

from src.channels.base import BaseChannel, ChannelSendResult

logger = logging.getLogger(__name__)


class CustomWebhookChannel(BaseChannel):
    """Push messages to one or more custom webhook endpoints."""

    def __init__(
        self,
        webhook_urls: Optional[List[str]] = None,
        bearer_token: Optional[str] = None,
    ):
        self._webhook_urls = webhook_urls or []
        self._bearer_token = bearer_token

    @property
    def channel_name(self) -> str:
        return "自定义Webhook"

    @property
    def channel_id(self) -> str:
        return "custom"

    def is_configured(self) -> bool:
        return bool(self._webhook_urls)

    def send(self, content: str, **kwargs) -> ChannelSendResult:
        if not self.is_configured():
            return ChannelSendResult(
                success=False, channel_name=self.channel_name,
                error="未配置自定义 Webhook URL",
            )

        total = len(self._webhook_urls)
        sent = 0
        errors: list[str] = []

        for url in self._webhook_urls:
            ok = self._post(url, content)
            if ok:
                sent += 1
            else:
                errors.append(url)

        success = sent == total
        return ChannelSendResult(
            success=success, channel_name=self.channel_name,
            chunks_sent=sent, chunks_total=total,
            error=None if success else f"Failed URLs: {errors}",
        )

    def _post(self, url: str, content: str) -> bool:
        try:
            headers = {"Content-Type": "application/json"}
            if self._bearer_token:
                headers["Authorization"] = f"Bearer {self._bearer_token}"

            payload = {
                "msgtype": "markdown",
                "markdown": {"content": content},
                "content": content,
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            if resp.status_code not in (200, 201, 204):
                logger.error(f"[CustomWebhook] HTTP {resp.status_code} for {url}")
                return False
            return True
        except Exception as exc:
            logger.error(f"[CustomWebhook] 发送失败 ({url}): {exc}")
            return False
