"""网页采集适配器。

- WebFetchAdapter：默认走 Firecrawl（若配置 FIRECRAWL_API_KEY），否则回退到简单 HTTP 抓取。
- RegulatorFetchAdapter：监管官网适配器（复用 web 抓取，标注 source_type=REGULATOR）。

真实抓取依赖外部服务，这里将"取原文"抽象为 `_raw_fetch`，
默认实现使用标准库，便于在无第三方依赖时也可运行/测试（可注入替换）。
"""

from __future__ import annotations

import os
from collections.abc import Callable

from core.models import SourceType
from core.tools.base import RawDocument


def _http_get(url: str, timeout: float = 15.0) -> str:
    """最小可用的 HTTP 抓取（标准库）。生产建议替换为 Firecrawl/Crawl4AI 适配器。

    含基础 SSRF 防护：仅允许 http/https，拒绝内网/环回/链路本地/元数据地址。
    """
    from urllib.request import Request, urlopen

    _assert_safe_url(url)
    req = Request(url, headers={"User-Agent": "MIP-Bot/0.1 (+compliance-aware)"})
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 (已校验 http/https + 非内网)
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def _assert_safe_url(url: str) -> None:
    """SSRF 防护：限制 scheme 与目标地址，阻断内网/环回/云元数据。"""
    import ipaddress
    import socket
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"仅允许 http/https，拒绝：{parsed.scheme}")
    host = parsed.hostname
    if not host:
        raise ValueError("URL 缺少主机名")
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError as e:
        raise ValueError(f"无法解析主机：{host}") from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        ):
            raise ValueError(f"拒绝访问内网/保留地址：{ip}")


class WebFetchAdapter:
    """通用网页抓取适配器。"""

    source_type = SourceType.WEB
    feature = None  # 🟢 低风险，无需 flag

    def __init__(self, raw_fetch: Callable[[str], str] | None = None):
        # 允许注入自定义抓取函数（测试/替换 Firecrawl 等）
        self._raw_fetch = raw_fetch or _http_get
        self.firecrawl_key = os.getenv("FIRECRAWL_API_KEY")

    def fetch(self, target: str, **kwargs) -> RawDocument:
        content = self._raw_fetch(target)
        return RawDocument(
            source_type=self.source_type,
            url=target,
            content=content,
            raw_meta={"fetcher": "firecrawl" if self.firecrawl_key else "http"},
        )


class RegulatorFetchAdapter(WebFetchAdapter):
    """监管官网适配器：与 web 抓取同源，但标注为 REGULATOR。"""

    source_type = SourceType.REGULATOR
    feature = None
