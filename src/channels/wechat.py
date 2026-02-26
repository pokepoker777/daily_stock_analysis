# -*- coding: utf-8 -*-
"""
Enterprise WeChat (企业微信) notification channel.

Sends Markdown or text messages via the WeChat Group Robot Webhook API.
Supports automatic chunking for messages exceeding the 4 KB limit.
"""

from __future__ import annotations

import logging
from typing import Optional

import requests

from src.channels.base import BaseChannel, ChannelSendResult

logger = logging.getLogger(__name__)

# 企业微信单条消息限制（字节）
_DEFAULT_MAX_BYTES = 4000


class WeChatChannel(BaseChannel):
    """Push messages to an Enterprise WeChat group robot webhook."""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        msg_type: str = "markdown",
        max_bytes: int = _DEFAULT_MAX_BYTES,
    ):
        self._webhook_url = webhook_url or ""
        self._msg_type = msg_type  # 'markdown' or 'text'
        self._max_bytes = max_bytes

    # -- Identity ----------------------------------------------------------

    @property
    def channel_name(self) -> str:
        return "企业微信"

    @property
    def channel_id(self) -> str:
        return "wechat"

    # -- Config guard ------------------------------------------------------

    def is_configured(self) -> bool:
        return bool(self._webhook_url)

    # -- Send --------------------------------------------------------------

    def send(self, content: str, **kwargs) -> ChannelSendResult:
        if not self.is_configured():
            return ChannelSendResult(
                success=False,
                channel_name=self.channel_name,
                error="未配置企业微信 Webhook URL",
            )

        chunks = self._chunk_by_bytes(content, self._max_bytes)
        total = len(chunks)
        sent = 0

        for idx, chunk in enumerate(chunks, 1):
            prefix = f"({idx}/{total}) " if total > 1 else ""
            ok = self._post_message(f"{prefix}{chunk}")
            if ok:
                sent += 1

        success = sent == total
        if not success:
            logger.warning(
                f"[{self.channel_name}] 部分分片发送失败 ({sent}/{total})"
            )

        return ChannelSendResult(
            success=success,
            channel_name=self.channel_name,
            chunks_sent=sent,
            chunks_total=total,
            error=None if success else f"{total - sent}/{total} chunks failed",
        )

    # -- Internal ----------------------------------------------------------

    def _post_message(self, text: str) -> bool:
        """Post a single message to the WeChat webhook."""
        try:
            if self._msg_type == "markdown":
                payload = {
                    "msgtype": "markdown",
                    "markdown": {"content": text},
                }
            else:
                payload = {
                    "msgtype": "text",
                    "text": {"content": text},
                }

            resp = requests.post(
                self._webhook_url,
                json=payload,
                timeout=30,
            )
            data = resp.json()
            if data.get("errcode", -1) != 0:
                logger.error(
                    f"[{self.channel_name}] API error: "
                    f"errcode={data.get('errcode')}, errmsg={data.get('errmsg')}"
                )
                return False
            return True
        except Exception as exc:
            logger.error(f"[{self.channel_name}] 发送失败: {exc}")
            return False
