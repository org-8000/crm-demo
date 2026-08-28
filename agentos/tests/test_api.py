"""持久化 + 自定义 API 端到端测试（FastAPI TestClient + SQLite）。

覆盖：⑤ assess→落库→列表→接管；③ research→落库→串联国家；证据齐全。
"""

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api import build_api_router  # noqa: E402
from app.db import SqlInsightRepo  # noqa: E402
from core.knowledge.kb import InMemoryKnowledgeBase  # noqa: E402
from core.models import SourceType  # noqa: E402
from core.tools.base import AdapterRegistry, RawDocument  # noqa: E402
from modules.seeds import seed_payment_ontology  # noqa: E402


class _StaticWeb:
    source_type = SourceType.WEB
    feature = None

    def fetch(self, target, **_):
        # 低信号站点（无支付关键词）→ 触发 needs_human
        if "nobody" in target or "n.example" in target:
            content = "A generic corporate homepage. About us. Contact."
        else:
            content = (
                "Acme is a cross-border acquiring and e-wallet provider applying for an MPI "
                "license, upgrading ISO 20022, compliance/AML."
            )
        return RawDocument(source_type=SourceType.WEB, url=target, content=content)


@pytest.fixture
def client():
    repo = SqlInsightRepo()  # SQLite 内存
    kb = InMemoryKnowledgeBase()
    seed_payment_ontology(kb)
    reg = AdapterRegistry()
    reg.register(_StaticWeb())
    app = FastAPI()
    app.include_router(build_api_router(repo=repo, knowledge=kb, registry=reg))
    return TestClient(app)


def test_m5_assess_persists_and_lists(client):
    r = client.post("/m5/assess", json={"country": "Singapore", "business_mode": "acquiring"})
    assert r.status_code == 200
    body = r.json()
    assert body["steps"] and body["insight"]["verdict"]["licenses"]
    assert body["insight"]["evidence"]  # 证据齐全
    iid = body["insight"]["id"]

    lst = client.get("/insights", params={"module": "M5"}).json()
    assert any(i["id"] == iid for i in lst)


def test_m3_research_persists_and_chains(client):
    r = client.post(
        "/m3/research",
        json={"name": "Acme", "homepage_url": "https://acme.example.com", "country": "Singapore"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["linked_country"] == "Singapore"
    assert body["insight"]["verdict"]["business_focus"]


def test_review_queue_and_action(client):
    # 造一条低置信③ → 进接管队列
    client.post("/m3/research", json={"name": "Nobody", "homepage_url": "https://n.example.com"})
    queue = client.get("/review").json()
    assert len(queue) >= 1
    iid = queue[0]["id"]
    # 处理接管
    r = client.post(f"/insights/{iid}/review", json={"action": "approve", "note": "ok"})
    assert r.status_code == 200
    assert r.json()["insight"]["status"] == "actioned"
    assert r.json()["note_received"] is True
    # 处理后不再在队列
    assert all(i["id"] != iid for i in client.get("/review").json())


def test_review_unknown_action_400(client):
    client.post("/m5/assess", json={"country": "Singapore", "business_mode": "x"})
    r = client.post("/insights/1/review", json={"action": "bogus"})
    assert r.status_code == 400


def test_m5_assess_bad_input_400(client):
    # 未知国家（知识库无数据）与空国家应为 400，而非 500
    assert client.post("/m5/assess", json={"country": "Atlantis", "business_mode": "x"}).status_code == 400
    assert client.post("/m5/assess", json={"country": "", "business_mode": "x"}).status_code == 400


def test_created_at_roundtrip_consistent(client):
    """写入与读回的 created_at 时区一致（SQLite naive → 统一补 UTC）。"""
    saved = client.post("/m5/assess", json={"country": "Singapore", "business_mode": "x"}).json()
    iid = saved["insight"]["id"]
    fetched = client.get(f"/insights/{iid}").json()
    # 两者都应带时区（以 +00:00 或 Z 结尾），不应一个带一个不带
    assert saved["insight"]["created_at"][-6:] in ("+00:00",) or saved["insight"]["created_at"].endswith("Z")
    assert fetched["created_at"][-6:] in ("+00:00",) or fetched["created_at"].endswith("Z")


def test_get_missing_insight_404(client):
    assert client.get("/insights/9999").status_code == 404
