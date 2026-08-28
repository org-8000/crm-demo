"""合规网关：数据源分级、feature flags、PII TTL、采集前校验、审计。

合规是一等公民：任何采集必须先过网关校验，高风险能力默认关闭。
纯 Python，无外部依赖，便于单测。
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

from core.models import ComplianceLevel, SourceType


class ComplianceError(RuntimeError):
    """合规校验未通过时抛出。"""


# 数据源类型 → 默认合规等级
SOURCE_LEVEL: dict[SourceType, ComplianceLevel] = {
    SourceType.WEB: ComplianceLevel.GREEN,
    SourceType.REGULATOR: ComplianceLevel.GREEN,
    SourceType.DOC: ComplianceLevel.GREEN,
    SourceType.SEARCH: ComplianceLevel.GREEN,
    SourceType.SOCIAL: ComplianceLevel.YELLOW,
    SourceType.GROUP: ComplianceLevel.RED,
    SourceType.LINKEDIN: ComplianceLevel.RED,
}

# 高风险能力 → 控制其开启的环境变量（默认关闭）
FEATURE_FLAGS: dict[str, str] = {
    "M2_GROUP_MONITOR": "ENABLE_M2_GROUP_MONITOR",  # ②群聊/私域招标监控
    "M6_AUTOSEND": "ENABLE_M6_AUTOSEND",            # ⑥LinkedIn 自动发送
    "SOCIAL_DEEP_SCRAPE": "ENABLE_SOCIAL_DEEP_SCRAPE",  # ①②深度社媒抓取
}

# PII 默认留存期限（天）
DEFAULT_PII_TTL_DAYS = 90


def flag_enabled(name: str) -> bool:
    """判断高风险能力是否显式开启（默认 False）。"""
    env = FEATURE_FLAGS.get(name)
    if not env:
        return False
    return os.getenv(env, "false").strip().lower() in {"1", "true", "yes", "on"}


def level_for(source_type: SourceType) -> ComplianceLevel:
    return SOURCE_LEVEL.get(source_type, ComplianceLevel.RED)


def pii_expiry(ttl_days: int = DEFAULT_PII_TTL_DAYS) -> datetime:
    """计算 PII 到期时间，用于 person.pii_ttl。"""
    return datetime.now(UTC) + timedelta(days=ttl_days)


class ComplianceGateway:
    """采集前的合规闸门。

    - GREEN：放行。
    - YELLOW：默认放行，但要求提供 legal_basis（可通过 require_legal_basis 收紧）。
    - RED：必须显式开启对应 feature flag，否则拒绝。
    """

    def __init__(self, require_legal_basis: bool = True, blacklist_domains: set[str] | None = None):
        self.require_legal_basis = require_legal_basis
        self.blacklist_domains = blacklist_domains or set()

    def check(
        self,
        source_type: SourceType,
        url: str | None = None,
        legal_basis: str | None = None,
        feature: str | None = None,
    ) -> ComplianceLevel:
        """校验一次采集是否合规；不合规抛 ComplianceError，合规返回其等级。"""
        level = level_for(source_type)

        if url:
            host = _host(url)
            if host and host in self.blacklist_domains:
                raise ComplianceError(f"域名在黑名单：{host}")

        if level is ComplianceLevel.RED:
            if not feature or not flag_enabled(feature):
                raise ComplianceError(
                    f"高风险源 {source_type.value} 需显式开启 feature flag "
                    f"({FEATURE_FLAGS.get(feature or '', '未指定')})，当前关闭"
                )

        if level is ComplianceLevel.YELLOW and self.require_legal_basis and not legal_basis:
            raise ComplianceError(f"中风险源 {source_type.value} 需提供 legal_basis")

        return level


def _host(url: str) -> str:
    from urllib.parse import urlparse

    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""
