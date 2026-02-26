# -*- coding: utf-8 -*-
"""
Feishu (飞书) notification channel.

Sends rich-text or interactive card messages via the Feishu Group Robot
Webhook API.  Supports automatic chunking for the 30 KB payload limit.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from typing import Optional

import requests

from src.channels.base import BaseChannel, ChannelSendResult

logger = logging.getLogger(__name__)

_DEFAULT_MAX_BYTES = 20000  # 飞书单条消息建议上限


class FeishuChannel(BaseChannel):
    """Push messages to a Feishu group robot webhook."""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        secret: Optional[str] = None,
        max_bytes: int = _DEFAULT_MAX_BYTES,
    ):
        self._webhook_url = webhook_url or ""
        self._secret = secret
        self._max_bytes = max_bytes

    # -- Identity ----------------------------------------------------------

    @property
    def channel_name(self) -> str:
        return "飞书"

    @property
    def channel_id(self) -> str:
        return "feishu"

    # -- Config guard ------------------------------------------------------

    def is_configured(self) -> bool:
        return bool(self._webhook_url)

    # -- Send --------------------------------------------------------------

    def send(self, content: str, **kwargs) -> ChannelSendResult:
        if not self.is_configured():
            return ChannelSendResult(
                success=False,
                channel_name=self.channel_name,
                error="未配置飞书 Webhook URL",
            )

        chunks = self._chunk_by_bytes(content, self._max_bytes)
        total = len(chunks)
        sent = 0

        for idx, chunk in enumerate(chunks, 1):
            title = f"分析报告 ({idx}/{total})" if total > 1 else "分析报告"
            ok = self._post_message(chunk, title=title)
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

    def _gen_sign(self) -> Optional[dict]:
        """Generate timestamp + sign header fields for signed webhooks."""
        if not self._secret:
            return None
        timestamp = str(int(time.time()))
        string_to_sign = f"{timestamp}\n{self._secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
        ).digest()
        import base64

        sign = base64.b64encode(hmac_code).decode("utf-8")
        return {"timestamp": timestamp, "sign": sign}

    def _post_message(self, text: str, title: str = "分析报告") -> bool:
        """Post a single interactive-card message."""
        try:
            # Build rich text payload (interactive card)
            payload: dict = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {"tag": "plain_text", "content": title},
                        "template": "blue",
                    },
                    "elements": [
                        {
                            "tag": "markdown",
                            "content": text,
                        }
                    ],
                },
            }

            sign_fields = self._gen_sign()
            if sign_fields:
                payload.update(sign_fields)

            resp = requests.post(
                self._webhook_url,
                json=payload,
                timeout=30,
            )
            data = resp.json()
            code = data.get("code", data.get("StatusCode", -1))
            if code != 0:
                logger.error(
                    f"[{self.channel_name}] API error: "
                    f"code={code}, msg={data.get('msg', data.get('StatusMessage', ''))}"
                )
                return False
            return True
        except Exception as exc:
            logger.error(f"[{self.channel_name}] 发送失败: {exc}")
            return False
