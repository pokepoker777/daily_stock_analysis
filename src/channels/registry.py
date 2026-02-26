# -*- coding: utf-8 -*-
"""
Channel Registry — auto-discovers and instantiates notification channels
from the application ``Config``.

Usage::

    registry = ChannelRegistry.from_config()
    for ch in registry.enabled_channels():
        result = ch.send(markdown_content)
"""

from __future__ import annotations

import logging
from typing import List

from src.channels.base import BaseChannel, ChannelSendResult

logger = logging.getLogger(__name__)


class ChannelRegistry:
    """Holds all instantiated channels and exposes helpers for bulk send."""

    def __init__(self, channels: List[BaseChannel] | None = None):
        self._channels: List[BaseChannel] = channels or []

    # ------------------------------------------------------------------ #
    #  Factory
    # ------------------------------------------------------------------ #

    @classmethod
    def from_config(cls) -> "ChannelRegistry":
        """
        Build a registry by reading the current ``Config`` singleton.

        Each channel is instantiated and kept only if ``is_configured()``
        returns True.
        """
        from src.config import get_config

        cfg = get_config()
        candidates: List[BaseChannel] = []

        # --- WeChat ---
        from src.channels.wechat import WeChatChannel

        candidates.append(
            WeChatChannel(
                webhook_url=cfg.wechat_webhook_url,
                msg_type=getattr(cfg, "wechat_msg_type", "markdown"),
                max_bytes=getattr(cfg, "wechat_max_bytes", 4000),
            )
        )

        # --- Feishu ---
        from src.channels.feishu import FeishuChannel

        candidates.append(
            FeishuChannel(
                webhook_url=getattr(cfg, "feishu_webhook_url", None),
                secret=getattr(cfg, "feishu_webhook_secret", None),
                max_bytes=getattr(cfg, "feishu_max_bytes", 20000),
            )
        )

        # --- Telegram ---
        from src.channels.telegram import TelegramChannel

        candidates.append(
            TelegramChannel(
                bot_token=getattr(cfg, "telegram_bot_token", None),
                chat_id=getattr(cfg, "telegram_chat_id", None),
                message_thread_id=getattr(cfg, "telegram_message_thread_id", None),
            )
        )

        # --- Email ---
        from src.channels.email_channel import EmailChannel

        candidates.append(
            EmailChannel(
                sender=cfg.email_sender,
                sender_name=getattr(cfg, "email_sender_name", "daily_stock_analysis股票分析助手"),
                password=cfg.email_password,
                receivers=cfg.email_receivers or ([cfg.email_sender] if cfg.email_sender else []),
            )
        )

        # --- Pushover ---
        from src.channels.pushover_channel import PushoverChannel

        candidates.append(
            PushoverChannel(
                user_key=getattr(cfg, "pushover_user_key", None),
                api_token=getattr(cfg, "pushover_api_token", None),
            )
        )

        # --- PushPlus ---
        from src.channels.pushplus_channel import PushPlusChannel

        candidates.append(
            PushPlusChannel(token=getattr(cfg, "pushplus_token", None))
        )

        # --- Server酱3 ---
        from src.channels.serverchan3_channel import ServerChan3Channel

        candidates.append(
            ServerChan3Channel(sendkey=getattr(cfg, "serverchan3_sendkey", None))
        )

        # --- Custom Webhook ---
        from src.channels.custom_webhook_channel import CustomWebhookChannel

        candidates.append(
            CustomWebhookChannel(
                webhook_urls=getattr(cfg, "custom_webhook_urls", []) or [],
                bearer_token=getattr(cfg, "custom_webhook_bearer_token", None),
            )
        )

        # --- Discord ---
        from src.channels.discord_channel import DiscordChannel

        candidates.append(
            DiscordChannel(
                bot_token=getattr(cfg, "discord_bot_token", None),
                channel_id=getattr(cfg, "discord_main_channel_id", None),
                webhook_url=getattr(cfg, "discord_webhook_url", None),
            )
        )

        # --- AstrBot ---
        from src.channels.astrbot_channel import AstrBotChannel

        candidates.append(
            AstrBotChannel(
                url=getattr(cfg, "astrbot_url", None),
                token=getattr(cfg, "astrbot_token", None),
            )
        )

        # Keep only configured channels
        enabled = [ch for ch in candidates if ch.is_configured()]
        if enabled:
            names = [ch.channel_name for ch in enabled]
            logger.info(f"ChannelRegistry: {len(enabled)} 渠道就绪 — {', '.join(names)}")
        else:
            logger.warning("ChannelRegistry: 未检测到任何已配置的通知渠道")

        return cls(channels=enabled)

    # ------------------------------------------------------------------ #
    #  Queries
    # ------------------------------------------------------------------ #

    def enabled_channels(self) -> List[BaseChannel]:
        """Return all channels that passed the ``is_configured`` check."""
        return list(self._channels)

    def get_channel(self, channel_id: str) -> BaseChannel | None:
        """Look up a single channel by its machine-readable id."""
        for ch in self._channels:
            if ch.channel_id == channel_id:
                return ch
        return None

    @property
    def count(self) -> int:
        return len(self._channels)

    # ------------------------------------------------------------------ #
    #  Bulk send
    # ------------------------------------------------------------------ #

    def send_all(self, content: str, **kwargs) -> List[ChannelSendResult]:
        """
        Send *content* to **every** enabled channel and collect results.

        This is intentionally synchronous; for async fan-out the caller
        should use ``concurrent.futures`` or ``asyncio``.
        """
        results: List[ChannelSendResult] = []
        for ch in self._channels:
            result = ch._safe_send(content, **kwargs)
            results.append(result)
            if result.success:
                logger.info(f"✅ [{ch.channel_name}] 推送成功")
            else:
                logger.warning(
                    f"❌ [{ch.channel_name}] 推送失败: {result.error}"
                )
        return results
