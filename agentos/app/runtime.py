"""Serve 环境的共享底座运行时（单例）。

集中构造采集适配器注册表与知识库，供各模块的 Agno Team/Workflow 复用。
仅在 serve 环境（含 agno）被 build_* 调用；核心单测不导入本模块。
"""

from __future__ import annotations

from functools import lru_cache

from core.compliance import ComplianceGateway
from core.knowledge.kb import InMemoryKnowledgeBase, KnowledgeBase
from core.tools.base import AdapterRegistry
from core.tools.web import RegulatorFetchAdapter, WebFetchAdapter


@lru_cache(maxsize=1)
def get_registry() -> AdapterRegistry:
    reg = AdapterRegistry(gateway=ComplianceGateway())
    reg.register(WebFetchAdapter())
    reg.register(RegulatorFetchAdapter())
    return reg


@lru_cache(maxsize=1)
def get_knowledge() -> KnowledgeBase:
    """知识库单例。

    P1 默认用内存版并注入支付本体种子；生产替换为 Agno Knowledge + PgVector。
    """
    from modules.seeds import seed_payment_ontology

    kb = InMemoryKnowledgeBase()
    seed_payment_ontology(kb)
    return kb
