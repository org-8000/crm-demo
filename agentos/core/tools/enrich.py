"""联系人富化适配器（Proxycurl）。

Proxycurl 是合规付费的人/公司数据 API（付费换合规），因此 source_type=ENRICH(🟢)。
- 无 PROXYCURL_API_KEY 时返回空结果（不阻塞），并标注未启用。
- 返回统一 RawDocument（content 为 JSON 文本），供上层解析为联系人。
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable

from core.models import SourceType
from core.tools.base import RawDocument


class ProxycurlEnrichAdapter:
    source_type = SourceType.ENRICH
    feature = None  # 🟢 合规付费 API

    def __init__(self, fetch_json: Callable[[str], dict] | None = None):
        self.api_key = os.getenv("PROXYCURL_API_KEY")
        self._fetch_json = fetch_json  # 可注入（测试/替换）

    def fetch(self, target: str, **kwargs) -> RawDocument:
        """target 为 LinkedIn 个人/公司 URL 或机构域名。"""
        if self._fetch_json is not None:
            data = self._fetch_json(target)
        elif self.api_key:  # pragma: no cover - 需真实 key/网络
            data = self._call_proxycurl(target)
        else:
            data = {"_enabled": False, "note": "未配置 PROXYCURL_API_KEY，跳过富化"}
        return RawDocument(
            source_type=self.source_type,
            url=target,
            content=json.dumps(data, ensure_ascii=False),
            raw_meta={"provider": "proxycurl", "enabled": bool(self.api_key or self._fetch_json)},
            legal_basis="proxycurl compliant paid API",
        )

    def _call_proxycurl(self, target: str) -> dict:  # pragma: no cover
        from urllib.parse import urlencode
        from urllib.request import Request, urlopen

        base = "https://nubela.co/proxycurl/api/v2/linkedin"
        url = f"{base}?{urlencode({'url': target})}"
        req = Request(url, headers={"Authorization": f"Bearer {self.api_key}"})
        with urlopen(req, timeout=20) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))


def parse_contacts(doc: RawDocument) -> list[dict]:
    """从富化 RawDocument 解析出联系人列表（title/full_name/linkedin_url）。"""
    try:
        data = json.loads(doc.content)
    except json.JSONDecodeError:
        return []
    if not data or data.get("_enabled") is False:
        return []
    # 兼容单人对象或 {"people":[...]}
    people = data.get("people") if isinstance(data, dict) else None
    if people is None and isinstance(data, dict) and (data.get("full_name") or data.get("name")):
        people = [data]
    out = []
    for p in people or []:
        out.append(
            {
                "full_name": p.get("full_name") or p.get("name"),
                "title": p.get("occupation") or p.get("title"),
                "linkedin_url": p.get("linkedin_profile_url") or p.get("url"),
            }
        )
    return out
