"""富化 / 文档解析 / 通知 / 评估 单测。"""

import json

from core.extract.documents import BasicHtmlParser
from core.models import Evidence, Insight, ModuleId, SourceType
from core.notify import NullSink, WebhookSink, format_insight, notify_insight
from core.tools.enrich import ProxycurlEnrichAdapter, parse_contacts


# ---- 富化 ----
def test_enrich_disabled_without_key(monkeypatch):
    monkeypatch.delenv("PROXYCURL_API_KEY", raising=False)
    a = ProxycurlEnrichAdapter()
    doc = a.fetch("https://linkedin.com/in/x")
    assert a.source_type is SourceType.ENRICH
    assert parse_contacts(doc) == []  # 未启用返回空


def test_enrich_with_injected_fetch():
    def fake(_target):
        return {"people": [{"full_name": "Jane", "occupation": "CTO",
                            "linkedin_profile_url": "https://li/x"}]}

    a = ProxycurlEnrichAdapter(fetch_json=fake)
    contacts = parse_contacts(a.fetch("acme.com"))
    assert contacts and contacts[0]["full_name"] == "Jane" and contacts[0]["title"] == "CTO"


def test_enrich_source_is_green():
    from core.compliance import ComplianceLevel, level_for

    assert level_for(SourceType.ENRICH) is ComplianceLevel.GREEN


# ---- 文档解析 ----
def test_basic_html_parser_strips_tags_and_scripts():
    html = "<html><head><style>x{}</style></head><body><h1>Title</h1>" \
           "<script>evil()</script><p>正文内容 A</p></body></html>"
    text = BasicHtmlParser().to_text(html)
    assert "Title" in text and "正文内容 A" in text
    assert "evil" not in text and "{}" not in text


def test_basic_parser_plaintext():
    assert BasicHtmlParser().to_text("hello   world", content_type="text/plain") == "hello world"


# ---- 通知 ----
def _insight():
    return Insight(
        module=ModuleId.M2_TENDER,
        subject="某行招标",
        confidence=0.55,
        risk_flags=["yellow: social"],
        evidence=[Evidence(source_url="https://x", source_type=SourceType.SOCIAL, snippet="s")],
        needs_human=True,
    )


def test_format_insight_contains_key_fields():
    text = format_insight(_insight())
    assert "招标监控" in text and "某行招标" in text
    assert "需人工接管" in text and "证据 1 条" in text


def test_null_sink_returns_false():
    assert notify_insight(_insight(), sink=NullSink()) is False


def test_webhook_payload_shapes():
    lark = WebhookSink("http://x", provider="lark")._payload("hi")
    slack = WebhookSink("http://x", provider="slack")._payload("hi")
    assert lark["msg_type"] == "text" and lark["content"]["text"] == "hi"
    assert slack == {"text": "hi"}


# ---- 评估 ----
def test_eval_m5_thresholds():
    from modules.eval import evaluate_m5

    report = evaluate_m5()
    assert report["evidence_completeness"] == 1.0        # 证据齐全率 100%
    assert report["accuracy"] >= 0.8                     # 关键要点召回 ≥ 80%
    assert report["n_cases"] >= 2


# ---- 监管入库 + 订阅 ----
def test_ingest_regulator_and_subscription():
    from core.knowledge.kb import InMemoryKnowledgeBase
    from core.tools.base import AdapterRegistry, RawDocument
    from modules.m5_compliance import ingest_regulator_page, run_subscriptions

    class _Reg:
        source_type = SourceType.REGULATOR
        feature = None

        def fetch(self, target, **_):
            return RawDocument(
                source_type=SourceType.REGULATOR,
                url=target,
                content="<html><body>Testland requires a TPX license for payments.</body></html>",
            )

    kb = InMemoryKnowledgeBase()
    reg = AdapterRegistry()
    reg.register(_Reg())
    chunk = ingest_regulator_page(
        reg, kb, country="Testland", url="https://reg.testland.gov",
        category="license", title="TPX license", severity="block",
    )
    assert chunk.source_ref["country"] == "Testland"
    # 订阅跑该国 → 应能出准入清单
    sent = []
    results = run_subscriptions(kb, ["Testland"], notify=lambda ins: sent.append(ins))
    assert results and results[0].verdict["licenses"]
    assert len(sent) == 1


def test_dummy_json_roundtrip():
    # 确保富化 doc content 为合法 JSON
    a = ProxycurlEnrichAdapter()
    doc = a.fetch("x")
    json.loads(doc.content)
