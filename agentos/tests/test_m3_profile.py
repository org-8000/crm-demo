"""模块③ 客户研判引擎 + ③→⑤ 串联单测。"""


from core.knowledge.kb import KB_ORG_PROFILES, InMemoryKnowledgeBase, KBChunk
from core.models import ModuleId, SourceType
from core.tools.base import AdapterRegistry, RawDocument
from modules.m3_profile import ProfileEngine, country_for_compliance
from modules.m5_compliance import ComplianceEngine
from modules.seeds import seed_payment_ontology


class _StaticWeb:
    source_type = SourceType.WEB
    feature = None

    def __init__(self, text: str):
        self._text = text

    def fetch(self, target: str, **_):
        return RawDocument(source_type=SourceType.WEB, url=target, content=self._text)


_TEXT = (
    "Acme Payments is a cross-border acquiring and e-wallet provider applying for an MPI "
    "license and upgrading to ISO 20022. Compliance/AML program expanding."
)


def _registry(text: str) -> AdapterRegistry:
    r = AdapterRegistry()
    r.register(_StaticWeb(text))
    return r


def test_profile_extracts_focus_and_entry_points():
    eng = ProfileEngine(registry=_registry(_TEXT))
    ins = eng.research("Acme Payments", "https://acme.example.com", country="Singapore")
    assert ins.module == ModuleId.M3_PROFILE
    v = ins.verdict
    assert "跨境收单" in v["business_focus"] and "电子钱包" in v["business_focus"]
    titles = {e["title"] for e in v["entry_points"]}
    assert "牌照扩张" in titles and "报文标准升级" in titles
    assert 0 < v["fit_score"] <= 1.0
    assert ins.evidence[0].source_type == SourceType.WEB


def test_profile_low_signal_needs_human():
    eng = ProfileEngine(registry=_registry("A generic company homepage with no payment terms."))
    ins = eng.research("Nobody Inc", "https://nobody.example.com")
    assert ins.confidence <= 0.6
    assert ins.needs_human is True


def test_profile_risk_flags():
    eng = ProfileEngine(registry=_registry(_TEXT + " Under sanction review with a fine."))
    ins = eng.research("Acme", "https://acme.example.com")
    assert any("risk-term" in f for f in ins.risk_flags)


def test_profile_uses_org_kb():
    kb = InMemoryKnowledgeBase()
    kb.add(KBChunk(kb_name=KB_ORG_PROFILES, content="Acme Payments 历史：2024 曾申请 EMI"))
    eng = ProfileEngine(registry=_registry(_TEXT), knowledge=kb)
    ins = eng.research("Acme Payments", "https://acme.example.com")
    assert "历史资料" in ins.verdict["profile"]


def test_chain_profile_to_compliance():
    """③→⑤ 串联：研判抽出国家 → 驱动合规准入。"""
    kb = InMemoryKnowledgeBase()
    seed_payment_ontology(kb)
    p_eng = ProfileEngine(registry=_registry(_TEXT), knowledge=kb)
    profile = p_eng.research("Acme", "https://acme.example.com", country="Singapore")

    country = country_for_compliance(profile)
    assert country == "Singapore"

    c_eng = ComplianceEngine(knowledge=kb)
    admission = c_eng.assess(country, "cross-border acquiring")
    assert admission.verdict["country"] == "Singapore"
    assert admission.verdict["licenses"]


def test_chain_context_not_leaked_into_verdict():
    """串联上下文应在 chain_context，不得泄漏进 verdict（前端只渲染 verdict）。"""
    eng = ProfileEngine(registry=_registry(_TEXT))
    ins = eng.research("Acme", "https://acme.example.com", country="Singapore",
                       business_mode="cross-border acquiring")
    assert "_country" not in ins.verdict and "_business_mode" not in ins.verdict
    assert ins.chain_context["country"] == "Singapore"
    assert ins.chain_context["business_mode"] == "cross-border acquiring"
