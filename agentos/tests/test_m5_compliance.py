"""模块⑤ 合规准入引擎单测。"""

import pytest

from core.knowledge.kb import InMemoryKnowledgeBase
from core.models import ModuleId, SourceType
from modules.m5_compliance import ComplianceEngine
from modules.seeds import seed_payment_ontology


@pytest.fixture
def kb():
    k = InMemoryKnowledgeBase()
    seed_payment_ontology(k)
    return k


def test_assess_singapore(kb):
    eng = ComplianceEngine(knowledge=kb)
    ins = eng.assess("Singapore", "cross-border acquiring")
    assert ins.module == ModuleId.M5_COMPLIANCE
    v = ins.verdict
    # 四类都应有内容（种子覆盖）
    assert v["licenses"] and v["messaging_standards"]
    assert v["data_compliance"] and v["business_restrictions"]
    # 证据均来自监管源
    assert all(e.source_type == SourceType.REGULATOR for e in ins.evidence)
    assert len(ins.evidence) >= 4


def test_assess_indonesia_has_blockers(kb):
    eng = ComplianceEngine(knowledge=kb)
    ins = eng.assess("Indonesia", "wallet")
    # 印尼 PJP 牌照 + 数据本地化为 block
    blockers = [f for f in ins.risk_flags if f.startswith("blocker")]
    assert len(blockers) >= 2
    assert "卡点" in ins.verdict["readiness_summary"]


def test_confidence_is_category_coverage(kb):
    eng = ComplianceEngine(knowledge=kb)
    ins = eng.assess("Singapore", "acquiring")
    assert ins.confidence == 1.0  # 四类全覆盖


def test_country_filter_exact(kb):
    # 只应返回该国条目，不混入他国
    eng = ComplianceEngine(knowledge=kb)
    ins = eng.assess("Indonesia", "acquiring")
    for e in ins.evidence:
        assert "Indonesia" in e.snippet or "印尼" in e.snippet or "bi.go.id" in e.source_url or "kominfo" in e.source_url


def test_unknown_country_raises(kb):
    eng = ComplianceEngine(knowledge=kb)
    with pytest.raises(ValueError):
        eng.assess("Atlantis", "acquiring")
