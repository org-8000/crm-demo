"""模块③ 客户画像与商机研判。

输入：机构名称(+国家/业务模式/主页) → 画像 + 合作切入点 + 风险提示。

- `ProfileEngine`：纯 Python 引擎，复用采集 Tools(AdapterRegistry) + 提取 Pipeline + 知识库，
  规则化产出 ProfileVerdict，确定性、可离线测试（注入 fake 适配器）。
- 与⑤串联：`country_for_compliance()` 抽出国家，供合规准入引擎联动。
- `build_team(model)`：包成 Agno Team（guarded import）。
"""

from __future__ import annotations

import re

from core.extract.pipeline import ExtractionPipeline
from core.knowledge.kb import KB_ORG_PROFILES, KnowledgeBase
from core.models import Evidence, Insight, SourceType
from core.tools.base import AdapterRegistry
from core.verdicts import EntryPoint, ProfileVerdict

# 支付业务关键词词典（命中即视为业务聚焦信号）
_FOCUS_LEXICON = {
    "跨境收单": ["cross-border", "acquiring", "跨境", "收单"],
    "电子钱包": ["wallet", "e-wallet", "钱包"],
    "汇款": ["remittance", "汇款", "money transfer"],
    "发卡": ["issuing", "card issuing", "发卡"],
    "清算": ["clearing", "settlement", "清算"],
}
# 风险关键词
_RISK_TERMS = ["sanction", "制裁", "penalty", "fine", "处罚", "breach", "违规", "lawsuit", "诉讼"]
# 切入点线索
_ENTRY_HINTS = {
    "牌照扩张": ["license", "licence", "牌照", "apply", "申请"],
    "报文标准升级": ["iso 20022", "iso20022", "报文"],
    "合规需求": ["compliance", "aml", "kyc", "合规"],
}


class ProfileEngine:
    def __init__(
        self,
        registry: AdapterRegistry,
        knowledge: KnowledgeBase | None = None,
        pipeline: ExtractionPipeline | None = None,
    ):
        self.registry = registry
        self.knowledge = knowledge
        self.pipeline = pipeline or ExtractionPipeline()

    def research(
        self,
        name: str,
        homepage_url: str,
        country: str | None = None,
        business_mode: str | None = None,
    ) -> Insight:
        doc = self.registry.fetch(SourceType.WEB, homepage_url, legal_basis="public website")
        text = doc.content
        low = text.lower()

        business_focus = [
            focus for focus, kws in _FOCUS_LEXICON.items() if any(k in low for k in kws)
        ]
        entry_points = [
            EntryPoint(title=title, rationale=f"页面提及相关信号：{title}")
            for title, kws in _ENTRY_HINTS.items()
            if any(k in low for k in kws)
        ]
        risks = [t for t in _RISK_TERMS if t in low]

        # 复用知识库历史资料（若命中，增强画像）
        kb_hits = (
            self.knowledge.search(KB_ORG_PROFILES, name, top_k=1) if self.knowledge else []
        )
        profile_extra = f"；历史资料：{kb_hits[0].content}" if kb_hits else ""

        # fit_score：业务聚焦命中数 + 切入点 归一
        signal = len(business_focus) + len(entry_points)
        fit_score = round(min(signal / 5.0, 1.0), 2)
        # 置信度：有内容且有信号则高，否则低（触发人工复核）
        confidence = round(min(0.4 + 0.15 * signal, 0.95), 2) if signal else 0.3

        profile = (
            f"{name}"
            + (f"（{country}）" if country else "")
            + f"：识别到 {len(business_focus)} 类支付业务聚焦{profile_extra}"
        )

        verdict = ProfileVerdict(
            subject=name + (f"（{country}）" if country else ""),
            confidence=confidence,
            risk_flags=[f"risk-term: {r}" for r in risks],
            profile=profile,
            business_focus=business_focus,
            entry_points=entry_points,
            risks=[f"页面出现风险关键词：{r}" for r in risks],
            fit_score=fit_score,
        )

        evidence = [
            Evidence(
                source_url=doc.url,
                source_type=SourceType.WEB,
                snippet=_snippet(text),
            )
        ]
        insight = verdict.to_insight(evidence=evidence)
        # 记录国家于 verdict，供串联⑤
        insight.verdict["_country"] = country
        insight.verdict["_business_mode"] = business_mode
        return insight


def country_for_compliance(profile_insight: Insight) -> str | None:
    """从③研判 Insight 抽取国家，用于串联⑤合规准入。"""
    return profile_insight.verdict.get("_country")


def _snippet(text: str, n: int = 160) -> str:
    s = re.sub(r"\s+", " ", text).strip()
    return s[:n] or "（无正文）"


# ---------------- Agno Team 装配（serve 环境）----------------

def build_team(model=None):  # pragma: no cover - 需 serve 依赖
    """包成 Agno Team：研判 Agent（生产可扩展为采集/研判/风险多 Agent 协作）。"""
    from agno.agent import Agent
    from agno.team import Team

    from app.runtime import get_registry

    engine = ProfileEngine(registry=get_registry())

    def research_org(name: str, homepage_url: str, country: str | None = None) -> dict:
        """研判某机构：抓取主页→提取业务聚焦/切入点/风险→输出结构化画像。"""
        return engine.research(name, homepage_url, country=country).model_dump(mode="json")

    researcher = Agent(name="profile-researcher", model=model, tools=[research_org])
    return Team(name="m3-profile", members=[researcher])
