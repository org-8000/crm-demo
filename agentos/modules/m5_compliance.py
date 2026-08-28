"""模块⑤ 合规准入筛查。

输入：目标国家 + 业务模式 → 输出准入清单（牌照/报文标准/数据合规/业务限制），每条附监管原文证据。

分两层：
- `ComplianceEngine`：纯 Python 引擎，基于知识库(kb_payment_ontology)检索 + 监管抓取证据组装
  AdmissionVerdict，确定性、可离线测试。
- `build_workflow(model)`：将引擎包成 Agno Workflow（guarded import），供 AgentOS 装配与 cron 调度。
"""

from __future__ import annotations

from core.knowledge.kb import KB_PAYMENT_ONTOLOGY, KBChunk, KnowledgeBase
from core.models import Evidence, Insight, SourceType
from core.verdicts import AdmissionItem, AdmissionVerdict

# 类别 → verdict 字段
_CATEGORY_FIELD = {
    "license": "licenses",
    "messaging": "messaging_standards",
    "data": "data_compliance",
    "restriction": "business_restrictions",
}


class ComplianceEngine:
    """合规准入引擎。"""

    def __init__(self, knowledge: KnowledgeBase):
        self.knowledge = knowledge

    def assess(self, country: str, business_mode: str) -> Insight:
        if not country or not str(country).strip():
            raise ValueError("country 不能为空")
        # 检索该国相关本体（宽召回后按 country 精确过滤）
        hits = self.knowledge.search(
            KB_PAYMENT_ONTOLOGY, f"{country} {business_mode}", top_k=50
        )
        rows = [
            h.source_ref
            for h in hits
            if h.source_ref and h.source_ref.get("country", "").lower() == country.lower()
        ]

        buckets: dict[str, list[AdmissionItem]] = {v: [] for v in _CATEGORY_FIELD.values()}
        evidence: list[Evidence] = []
        for r in rows:
            field = _CATEGORY_FIELD.get(r.get("category", ""))
            if not field:
                continue
            buckets[field].append(
                AdmissionItem(
                    title=r["title"], detail=r["detail"], severity=r.get("severity", "info")
                )
            )
            evidence.append(
                Evidence(
                    source_url=r["source_url"],
                    source_type=SourceType.REGULATOR,
                    snippet=f"{r['title']}：{r['detail']}",
                )
            )

        # 无证据不出 Insight（合规/反幻觉）：前置于构造 verdict
        if not evidence:
            raise ValueError(f"知识库中无 {country} 的合规准入数据，请先补充监管本体")

        filled = sum(1 for items in buckets.values() if items)
        # 注意：confidence 语义 = 四类(牌照/报文/数据/限制)覆盖度，衡量"清单完整性"，
        # 非"结论确定性"。四类齐全国家恒为 1.0（不会触发 needs_human）。
        confidence = round(filled / len(_CATEGORY_FIELD), 2)
        blockers = [
            it.title
            for items in buckets.values()
            for it in items
            if it.severity == "block"
        ]
        summary = _readiness_summary(country, business_mode, blockers)

        verdict = AdmissionVerdict(
            subject=f"{country} / {business_mode}",
            country=country,
            business_mode=business_mode,
            confidence=confidence,
            risk_flags=[f"blocker: {b}" for b in blockers],
            licenses=buckets["licenses"],
            messaging_standards=buckets["messaging_standards"],
            data_compliance=buckets["data_compliance"],
            business_restrictions=buckets["business_restrictions"],
            readiness_summary=summary,
        )

        return verdict.to_insight(evidence=evidence)


def _readiness_summary(country: str, mode: str, blockers: list[str]) -> str:
    if not blockers:
        return f"{country}（{mode}）：未发现硬性阻断项，可推进前期准备。"
    return f"{country}（{mode}）：就绪度中等，主要卡点 = {'、'.join(blockers)}。"


def ingest_regulator_page(
    registry,
    knowledge: KnowledgeBase,
    country: str,
    url: str,
    category: str,
    title: str,
    severity: str = "warn",
    parser=None,
) -> KBChunk:
    """从监管活页抽取本体并入库（⑤ 监管拓展路径 / Docling 解析）。

    registry: AdapterRegistry（用 REGULATOR 适配器抓取）
    parser: DocumentParser（默认基础 HTML 解析）
    返回写入知识库的 KBChunk。
    """
    from core.extract.documents import get_parser

    parser = parser or get_parser()
    doc = registry.fetch(SourceType.REGULATOR, url, legal_basis="public regulator")
    text = parser.to_text(doc.content, doc.raw_meta.get("content_type", "text/html"))
    detail = text[:400] if text else title
    chunk = KBChunk(
        kb_name=KB_PAYMENT_ONTOLOGY,
        content=f"{country} | {category} | {title} | {detail}",
        source_ref={
            "country": country,
            "category": category,
            "title": title,
            "detail": detail,
            "severity": severity,
            "source_url": url,
        },
    )
    knowledge.add(chunk)
    return chunk


def run_subscriptions(
    knowledge: KnowledgeBase,
    countries: list[str],
    business_mode: str = "cross-border acquiring",
    repo=None,
    notify=None,
) -> list[Insight]:
    """⑤ 监管变更订阅：对订阅国家批量出准入清单，落库并通知。

    设计为可被 AgentOS scheduler / 外部 cron 定时调用（7×24）。
    """
    engine = ComplianceEngine(knowledge=knowledge)
    out: list[Insight] = []
    for country in countries:
        try:
            ins = engine.assess(country, business_mode)
        except ValueError:
            continue
        if repo is not None:
            repo.save(ins)
        if notify is not None:
            notify(ins)
        out.append(ins)
    return out


# ---------------- Agno Workflow 装配（serve 环境）----------------
def build_workflow(model=None):  # pragma: no cover - 需 serve 依赖
    """将合规准入包成 Agno Workflow。model 为 LLM（用于润色摘要，可选）。"""
    from agno.workflow import Step, Workflow

    from app.runtime import get_knowledge

    engine = ComplianceEngine(knowledge=get_knowledge())

    def _run(country: str, business_mode: str, **_):
        return engine.assess(country, business_mode).model_dump(mode="json")

    return Workflow(
        name="m5-compliance-admission",
        description="合规准入筛查：国家+业务模式 → 准入清单（附监管证据）",
        steps=[Step(name="assess", executor=_run)],
    )
