# -*- coding: utf-8 -*-
"""
===================================
Modular Notification Channels
===================================

Each channel is a self-contained module that implements
``BaseChannel``.  The ``ChannelRegistry`` discovers and
instantiates channels based on the current ``Config``.

Usage::

    from src.channels import ChannelRegistry

    registry = ChannelRegistry.from_config()
    for ch in registry.enabled_channels():
        ch.send(markdown_content)
"""

from src.channels.base import BaseChannel, ChannelSendResult
from src.channels.registry import ChannelRegistry

__all__ = ["BaseChannel", "ChannelSendResult", "ChannelRegistry"]
