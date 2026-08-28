"""采集 Tools 底座：统一 RawDocument、可插拔适配器协议、注册表。

上层 Agent 只依赖 `FetchAdapter` 协议与 `RawDocument`，
底层实现（Firecrawl / Crawl4AI / 监管站 / 社媒 / Proxycurl）可插拔替换，
数据源不稳定时只换适配器，不动上层逻辑。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from core.compliance import ComplianceGateway
from core.models import SourceType


@dataclass
class RawDocument:
    """采集层统一产出。"""

    source_type: SourceType
    url: str
    content: str
    fetched_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    raw_meta: dict = field(default_factory=dict)
    legal_basis: str | None = None


@runtime_checkable
class FetchAdapter(Protocol):
    """采集适配器协议。所有数据源实现该协议即可插拔。"""

    source_type: SourceType
    feature: str | None  # 若为高风险源，关联的 feature flag 名

    def fetch(self, target: str, **kwargs) -> RawDocument: ...


class AdapterRegistry:
    """适配器注册表：按 source_type 注册/查找，统一经合规网关校验。"""

    def __init__(self, gateway: ComplianceGateway | None = None):
        self._adapters: dict[SourceType, FetchAdapter] = {}
        self.gateway = gateway or ComplianceGateway()

    def register(self, adapter: FetchAdapter) -> None:
        if not isinstance(adapter, FetchAdapter):
            raise TypeError("适配器必须实现 FetchAdapter 协议")
        self._adapters[adapter.source_type] = adapter

    def get(self, source_type: SourceType) -> FetchAdapter:
        if source_type not in self._adapters:
            raise KeyError(f"未注册的采集源：{source_type.value}")
        return self._adapters[source_type]

    def fetch(self, source_type: SourceType, target: str, legal_basis: str | None = None, **kwargs) -> RawDocument:
        """先过合规网关，再调用对应适配器。"""
        adapter = self.get(source_type)
        # target 可能是 url 或 handle；仅当像 URL 时传给网关做黑名单校验
        url = target if str(target).startswith("http") else None
        self.gateway.check(
            source_type=source_type,
            url=url,
            legal_basis=legal_basis,
            feature=getattr(adapter, "feature", None),
        )
        doc = adapter.fetch(target, **kwargs)
        if legal_basis and not doc.legal_basis:
            doc.legal_basis = legal_basis
        return doc
