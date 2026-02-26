# -*- coding: utf-8 -*-
"""
Email (SMTP) notification channel.

Sends HTML-rendered Markdown reports via SMTP with automatic
server detection based on the sender's email domain.
"""

from __future__ import annotations

import logging
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import List, Optional

from src.channels.base import BaseChannel, ChannelSendResult

logger = logging.getLogger(__name__)

# Auto-detected SMTP configurations
SMTP_CONFIGS = {
    "qq.com": {"server": "smtp.qq.com", "port": 465, "ssl": True},
    "foxmail.com": {"server": "smtp.qq.com", "port": 465, "ssl": True},
    "163.com": {"server": "smtp.163.com", "port": 465, "ssl": True},
    "126.com": {"server": "smtp.126.com", "port": 465, "ssl": True},
    "gmail.com": {"server": "smtp.gmail.com", "port": 587, "ssl": False},
    "outlook.com": {"server": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    "hotmail.com": {"server": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    "live.com": {"server": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    "sina.com": {"server": "smtp.sina.com", "port": 465, "ssl": True},
    "sohu.com": {"server": "smtp.sohu.com", "port": 465, "ssl": True},
    "aliyun.com": {"server": "smtp.aliyun.com", "port": 465, "ssl": True},
    "139.com": {"server": "smtp.139.com", "port": 465, "ssl": True},
}


class EmailChannel(BaseChannel):
    """Send analysis reports via SMTP email."""

    def __init__(
        self,
        sender: Optional[str] = None,
        sender_name: str = "daily_stock_analysis股票分析助手",
        password: Optional[str] = None,
        receivers: Optional[List[str]] = None,
    ):
        self._sender = sender or ""
        self._sender_name = sender_name
        self._password = password or ""
        self._receivers = receivers or ([self._sender] if self._sender else [])

    # -- Identity ----------------------------------------------------------

    @property
    def channel_name(self) -> str:
        return "邮件"

    @property
    def channel_id(self) -> str:
        return "email"

    # -- Config guard ------------------------------------------------------

    def is_configured(self) -> bool:
        return bool(self._sender and self._password)

    # -- Send --------------------------------------------------------------

    def send(self, content: str, **kwargs) -> ChannelSendResult:
        subject = kwargs.get("subject") or self._extract_subject(content)

        if not self.is_configured():
            return ChannelSendResult(
                success=False,
                channel_name=self.channel_name,
                error="邮件发送人或授权码未配置",
            )

        smtp_cfg = self._detect_smtp()
        if not smtp_cfg:
            return ChannelSendResult(
                success=False,
                channel_name=self.channel_name,
                error=f"无法识别 SMTP 服务器: {self._sender}",
            )

        try:
            import markdown2
            html_body = markdown2.markdown(
                content,
                extras=["tables", "fenced-code-blocks", "strike"],
            )
            html_body = self._wrap_html(html_body)

            msg = MIMEMultipart("alternative")
            msg["Subject"] = Header(subject, "utf-8")
            msg["From"] = formataddr(
                (self._sender_name, self._sender), charset="utf-8"
            )
            msg["To"] = ", ".join(self._receivers)

            msg.attach(MIMEText(content, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            server = smtp_cfg["server"]
            port = smtp_cfg["port"]
            use_ssl = smtp_cfg["ssl"]

            if use_ssl:
                smtp = smtplib.SMTP_SSL(server, port, timeout=30)
            else:
                smtp = smtplib.SMTP(server, port, timeout=30)
                smtp.starttls()

            smtp.login(self._sender, self._password)
            smtp.sendmail(self._sender, self._receivers, msg.as_string())
            smtp.quit()

            logger.info(f"[{self.channel_name}] 发送成功 → {self._receivers}")
            return ChannelSendResult(success=True, channel_name=self.channel_name)

        except Exception as exc:
            logger.error(f"[{self.channel_name}] 发送失败: {exc}")
            return ChannelSendResult(
                success=False,
                channel_name=self.channel_name,
                error=str(exc),
            )

    # -- Internal ----------------------------------------------------------

    def _detect_smtp(self) -> Optional[dict]:
        domain = self._sender.split("@")[-1].lower() if "@" in self._sender else ""
        return SMTP_CONFIGS.get(domain)

    @staticmethod
    def _extract_subject(content: str) -> str:
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                return line.lstrip("# ").strip()
        return "股票智能分析报告"

    @staticmethod
    def _wrap_html(body: str) -> str:
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
       max-width: 800px; margin: 0 auto; padding: 20px; color: #333; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background-color: #f5f5f5; }}
h1 {{ color: #1a73e8; }} h2 {{ color: #34a853; }} h3 {{ color: #ea4335; }}
blockquote {{ border-left: 4px solid #1a73e8; margin: 10px 0; padding: 10px 15px;
             background-color: #f8f9fa; }}
code {{ background-color: #f1f3f4; padding: 2px 6px; border-radius: 4px; }}
hr {{ border: none; border-top: 1px solid #e0e0e0; margin: 15px 0; }}
</style></head><body>{body}</body></html>"""
