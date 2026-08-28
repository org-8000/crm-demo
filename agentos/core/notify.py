"""通知抽象：飞书/Slack webhook + Insight 格式化。

纯 Python（仅标准库），可离线测试格式化逻辑；实际发送用标准库 urllib。
"""

from __future__ import annotations

import json
import os
from typing import Protocol
from urllib.request import Request, urlopen

from core.models import Insight, ModuleId

_MODULE_LABEL = {
    ModuleId.M1_INTEL: "行业情报",
    ModuleId.M2_TENDER: "招标监控",
    ModuleId.M3_PROFILE: "客户研判",
    ModuleId.M4_SUMMIT: "峰会商机",
    ModuleId.M5_COMPLIANCE: "合规准入",
    ModuleId.M6_OUTREACH: "智能获客",
}


def format_insight(insight: Insight) -> str:
    """把 Insight 格式化为一段可读通知文本（含证据数量与是否需接管）。"""
    label = _MODULE_LABEL.get(insight.module, str(insight.module))
    lines = [
        f"【{label}】{insight.subject}",
        f"置信度 {insight.confidence:.2f}"
        + ("｜⚠ 需人工接管" if insight.needs_human else ""),
    ]
    if insight.risk_flags:
        lines.append("风险：" + "、".join(insight.risk_flags))
    lines.append(f"证据 {len(insight.evidence)} 条")
    return "\n".join(lines)


class NotificationSink(Protocol):
    def send(self, text: str) -> bool: ...


class NullSink:
    """未配置 webhook 时的空实现（返回 False 表示未发送）。"""

    def send(self, text: str) -> bool:  # noqa: ARG002
        return False


class WebhookSink:
    """飞书/Slack 兼容的文本 webhook。

    飞书自定义机器人载荷：{"msg_type":"text","content":{"text": ...}}
    Slack incoming webhook 载荷：{"text": ...}
    通过 provider 区分。
    """

    def __init__(self, url: str, provider: str = "lark"):
        self.url = url
        self.provider = provider

    def _payload(self, text: str) -> dict:
        if self.provider == "lark":
            return {"msg_type": "text", "content": {"text": text}}
        return {"text": text}  # slack

    def send(self, text: str) -> bool:
        data = json.dumps(self._payload(text)).encode("utf-8")
        req = Request(self.url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=10) as resp:  # noqa: S310 (webhook 由运维配置)
                return 200 <= resp.status < 300
        except Exception:  # noqa: BLE001 - 通知失败不应阻塞主流程
            return False


def default_sink() -> NotificationSink:
    """按环境变量选择通知目标；未配置则 NullSink。"""
    url = os.getenv("LARK_WEBHOOK_URL")
    if url:
        return WebhookSink(url, provider="lark")
    url = os.getenv("SLACK_WEBHOOK_URL")
    if url:
        return WebhookSink(url, provider="slack")
    return NullSink()


def notify_insight(insight: Insight, sink: NotificationSink | None = None) -> bool:
    """格式化并发送一条 Insight 通知。"""
    sink = sink or default_sink()
    return sink.send(format_insight(insight))
