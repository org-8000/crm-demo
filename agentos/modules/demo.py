"""P1 端到端演示：③客户研判 → 串联 → ⑤合规准入。

默认离线（注入示例主页文本 + 内存知识库种子），确定性可复现；
传 --live 且配置 FIRECRAWL_API_KEY 时改用真实网页抓取。

运行：python -m modules.demo
"""

from __future__ import annotations

import json
import sys

from core.knowledge.kb import InMemoryKnowledgeBase
from core.models import SourceType
from core.tools.base import AdapterRegistry, RawDocument
from modules.m3_profile import ProfileEngine, country_for_compliance
from modules.m5_compliance import ComplianceEngine
from modules.seeds import seed_payment_ontology

# 示例机构主页文本（离线用；--live 时改真实抓取）
_SAMPLE_HOMEPAGE = (
    "Acme Payments is a Singapore-based cross-border acquiring and e-wallet provider. "
    "We are applying for an MPI license with MAS and upgrading to ISO 20022 messaging. "
    "Our compliance and AML program is expanding across Southeast Asia."
)


class _StaticWebAdapter:
    source_type = SourceType.WEB
    feature = None

    def __init__(self, text: str):
        self._text = text

    def fetch(self, target: str, **_) -> RawDocument:
        return RawDocument(source_type=SourceType.WEB, url=target, content=self._text)


def run_demo(live: bool = False) -> dict:
    # 知识库 + 种子
    kb = InMemoryKnowledgeBase()
    seed_payment_ontology(kb)

    # 采集注册表
    registry = AdapterRegistry()
    if live:
        from core.tools.web import WebFetchAdapter

        registry.register(WebFetchAdapter())
    else:
        registry.register(_StaticWebAdapter(_SAMPLE_HOMEPAGE))

    # ③ 客户研判
    profile_engine = ProfileEngine(registry=registry, knowledge=kb)
    profile = profile_engine.research(
        name="Acme Payments",
        homepage_url="https://acme.example.com",
        country="Singapore",
        business_mode="cross-border acquiring",
    )

    # 串联 → ⑤ 合规准入
    country = country_for_compliance(profile)
    compliance_engine = ComplianceEngine(knowledge=kb)
    admission = compliance_engine.assess(country, "cross-border acquiring")

    return {
        "profile": profile.model_dump(mode="json"),
        "admission": admission.model_dump(mode="json"),
    }


if __name__ == "__main__":
    result = run_demo(live="--live" in sys.argv)
    print(json.dumps(result, ensure_ascii=False, indent=2))
