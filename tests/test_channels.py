# -*- coding: utf-8 -*-
"""Unit tests for the modular notification channel abstraction."""

import unittest

from src.channels.base import BaseChannel, ChannelSendResult


class DummyChannel(BaseChannel):
    """Concrete test double for BaseChannel."""

    def __init__(self, name="Test", cid="test", configured=True, fail=False):
        self._name = name
        self._cid = cid
        self._configured = configured
        self._fail = fail
        self.send_calls: list[str] = []

    @property
    def channel_name(self) -> str:
        return self._name

    @property
    def channel_id(self) -> str:
        return self._cid

    def is_configured(self) -> bool:
        return self._configured

    def send(self, content: str, **kwargs) -> ChannelSendResult:
        self.send_calls.append(content)
        if self._fail:
            return ChannelSendResult(
                success=False, channel_name=self._name, error="forced failure"
            )
        return ChannelSendResult(success=True, channel_name=self._name)


class TestBaseChannel(unittest.TestCase):
    def test_byte_len(self):
        self.assertEqual(BaseChannel._byte_len("abc"), 3)
        self.assertEqual(BaseChannel._byte_len("你好"), 6)

    def test_chunk_by_bytes_no_split(self):
        chunks = BaseChannel._chunk_by_bytes("hello", 100)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], "hello")

    def test_chunk_by_bytes_splits(self):
        content = "line1\nline2\nline3\nline4"
        # each line ~ 5-6 bytes + newline, set limit low
        chunks = BaseChannel._chunk_by_bytes(content, 12)
        self.assertGreater(len(chunks), 1)
        reconstructed = "\n".join(chunks)
        self.assertEqual(reconstructed, content)

    def test_safe_send_catches_exception(self):
        class CrashChannel(DummyChannel):
            def send(self, content, **kwargs):
                raise RuntimeError("boom")

        ch = CrashChannel()
        result = ch._safe_send("test")
        self.assertFalse(result.success)
        self.assertIn("boom", result.error)


class TestChannelSendResult(unittest.TestCase):
    def test_default_chunks(self):
        r = ChannelSendResult(success=True, channel_name="test")
        self.assertEqual(r.chunks_sent, 1)
        self.assertEqual(r.chunks_total, 1)

    def test_error_field(self):
        r = ChannelSendResult(success=False, channel_name="x", error="timeout")
        self.assertEqual(r.error, "timeout")


class TestChannelRegistry(unittest.TestCase):
    def test_enabled_channels(self):
        from src.channels.registry import ChannelRegistry

        ch1 = DummyChannel("A", "a", configured=True)
        ch2 = DummyChannel("B", "b", configured=False)
        ch3 = DummyChannel("C", "c", configured=True)
        registry = ChannelRegistry(channels=[ch1, ch2, ch3])
        # Registry stores what's passed in; from_config filters, but
        # direct construction keeps all.
        self.assertEqual(registry.count, 3)

    def test_get_channel(self):
        from src.channels.registry import ChannelRegistry

        ch1 = DummyChannel("A", "alpha")
        ch2 = DummyChannel("B", "beta")
        reg = ChannelRegistry(channels=[ch1, ch2])
        self.assertIs(reg.get_channel("alpha"), ch1)
        self.assertIs(reg.get_channel("beta"), ch2)
        self.assertIsNone(reg.get_channel("gamma"))

    def test_send_all(self):
        from src.channels.registry import ChannelRegistry

        ch1 = DummyChannel("A", "a")
        ch2 = DummyChannel("B", "b", fail=True)
        reg = ChannelRegistry(channels=[ch1, ch2])
        results = reg.send_all("hello")
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0].success)
        self.assertFalse(results[1].success)
        self.assertEqual(ch1.send_calls, ["hello"])
        self.assertEqual(ch2.send_calls, ["hello"])


class TestWeChatChannel(unittest.TestCase):
    def test_not_configured(self):
        from src.channels.wechat import WeChatChannel

        ch = WeChatChannel(webhook_url="")
        self.assertFalse(ch.is_configured())
        result = ch.send("test")
        self.assertFalse(result.success)

    def test_configured(self):
        from src.channels.wechat import WeChatChannel

        ch = WeChatChannel(webhook_url="https://example.com/hook")
        self.assertTrue(ch.is_configured())
        self.assertEqual(ch.channel_id, "wechat")
        self.assertEqual(ch.channel_name, "企业微信")


class TestTelegramChannel(unittest.TestCase):
    def test_not_configured(self):
        from src.channels.telegram import TelegramChannel

        ch = TelegramChannel()
        self.assertFalse(ch.is_configured())

    def test_configured(self):
        from src.channels.telegram import TelegramChannel

        ch = TelegramChannel(bot_token="123:ABC", chat_id="456")
        self.assertTrue(ch.is_configured())

    def test_split_text(self):
        from src.channels.telegram import TelegramChannel

        # Use multiline text so line-based splitting can chunk it
        long_text = "\n".join(["line " + str(i) for i in range(1000)])
        chunks = TelegramChannel._split_text(long_text, 4096)
        self.assertGreater(len(chunks), 1)
        # Reconstructed text should match original
        self.assertEqual("\n".join(chunks), long_text)


class TestFeishuChannel(unittest.TestCase):
    def test_not_configured(self):
        from src.channels.feishu import FeishuChannel

        ch = FeishuChannel()
        self.assertFalse(ch.is_configured())

    def test_identity(self):
        from src.channels.feishu import FeishuChannel

        ch = FeishuChannel(webhook_url="https://open.feishu.cn/hook/xxx")
        self.assertEqual(ch.channel_id, "feishu")
        self.assertEqual(ch.channel_name, "飞书")


class TestEmailChannel(unittest.TestCase):
    def test_not_configured(self):
        from src.channels.email_channel import EmailChannel

        ch = EmailChannel()
        self.assertFalse(ch.is_configured())

    def test_configured(self):
        from src.channels.email_channel import EmailChannel

        ch = EmailChannel(sender="user@qq.com", password="secret")
        self.assertTrue(ch.is_configured())

    def test_extract_subject(self):
        from src.channels.email_channel import EmailChannel

        content = "# 2025-01-01 股票报告\n\n内容"
        subj = EmailChannel._extract_subject(content)
        self.assertEqual(subj, "2025-01-01 股票报告")


class TestDiscordChannel(unittest.TestCase):
    def test_webhook_configured(self):
        from src.channels.discord_channel import DiscordChannel

        ch = DiscordChannel(webhook_url="https://discord.com/api/webhooks/xxx")
        self.assertTrue(ch.is_configured())

    def test_bot_configured(self):
        from src.channels.discord_channel import DiscordChannel

        ch = DiscordChannel(bot_token="xxx", channel_id="123")
        self.assertTrue(ch.is_configured())

    def test_not_configured(self):
        from src.channels.discord_channel import DiscordChannel

        ch = DiscordChannel()
        self.assertFalse(ch.is_configured())


class TestPushPlusChannel(unittest.TestCase):
    def test_not_configured(self):
        from src.channels.pushplus_channel import PushPlusChannel

        ch = PushPlusChannel()
        self.assertFalse(ch.is_configured())
        result = ch.send("test")
        self.assertFalse(result.success)


class TestServerChan3Channel(unittest.TestCase):
    def test_not_configured(self):
        from src.channels.serverchan3_channel import ServerChan3Channel

        ch = ServerChan3Channel()
        self.assertFalse(ch.is_configured())


class TestAstrBotChannel(unittest.TestCase):
    def test_not_configured(self):
        from src.channels.astrbot_channel import AstrBotChannel

        ch = AstrBotChannel()
        self.assertFalse(ch.is_configured())

    def test_configured(self):
        from src.channels.astrbot_channel import AstrBotChannel

        ch = AstrBotChannel(url="http://localhost:6185")
        self.assertTrue(ch.is_configured())


if __name__ == "__main__":
    unittest.main()
