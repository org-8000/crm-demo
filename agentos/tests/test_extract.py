"""提取 Pipeline 与知识库单测。"""

from core.extract.pipeline import ExtractionPipeline, RegexEntityExtractor
from core.knowledge.kb import KB_PAYMENT_ONTOLOGY, InMemoryKnowledgeBase, KBChunk
from core.models import SourceType
from core.tools.base import RawDocument


def _doc(text: str) -> RawDocument:
    return RawDocument(source_type=SourceType.REGULATOR, url="https://mas.gov.sg", content=text)


def test_regex_extractor_amount_and_date():
    ex = RegexEntityExtractor()
    ents = ex.extract("招标金额 USD 2,000,000，截止 2026-09-15", ["amount", "date"])
    types = {e.type for e in ents}
    assert "amount" in types and "date" in types


def test_regex_extractor_license_standard():
    ex = RegexEntityExtractor()
    ents = ex.extract("需申请 MPI 牌照并支持 ISO 20022 报文标准", ["license", "standard"])
    vals = {e.value.upper().replace(" ", "") for e in ents}
    assert any("MPI" in v or "牌照" in v for v in {e.value for e in ents})
    assert any("ISO20022" in v for v in vals)


def test_pipeline_entities():
    p = ExtractionPipeline()
    ents = p.entities(_doc("截止 2026-09-15 提交，牌照 MPI"), ["date", "license"])
    assert len(ents) >= 2


def test_inmemory_kb_search():
    kb = InMemoryKnowledgeBase()
    kb.add(KBChunk(kb_name=KB_PAYMENT_ONTOLOGY, content="新加坡 MAS 要求 MPI 牌照用于跨境支付"))
    kb.add(KBChunk(kb_name=KB_PAYMENT_ONTOLOGY, content="印尼数据本地化 PP71 规定"))
    hits = kb.search(KB_PAYMENT_ONTOLOGY, "MPI 牌照 跨境", top_k=1)
    assert hits and "MPI" in hits[0].content
