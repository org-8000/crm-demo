"""评估基线：黄金样本 + 准确率 / 证据齐全率。

- ⑤ 合规准入：对每个(国家,模式)校验是否包含期望的关键牌照/要点关键词。
- 证据齐全率：所有产出 Insight 是否都带证据（应为 100%）。

运行：python -m modules.eval
"""

from __future__ import annotations

import json

from core.knowledge.kb import InMemoryKnowledgeBase
from modules.m5_compliance import ComplianceEngine
from modules.seeds import seed_payment_ontology

# 黄金样本：(country, business_mode, 期望在准入清单中出现的关键词列表)
GOLDEN_M5: list[tuple[str, str, list[str]]] = [
    ("Singapore", "cross-border acquiring", ["MPI", "ISO 20022", "PDPA"]),
    ("Indonesia", "wallet", ["PJP", "本地化", "GPN"]),
]


def _verdict_text(insight_dict: dict) -> str:
    return json.dumps(insight_dict["verdict"], ensure_ascii=False)


def evaluate_m5() -> dict:
    kb = InMemoryKnowledgeBase()
    seed_payment_ontology(kb)
    engine = ComplianceEngine(knowledge=kb)

    total_expected = 0
    hit_expected = 0
    cases: list[dict] = []
    evidence_complete = 0
    n = 0

    for country, mode, expected in GOLDEN_M5:
        ins = engine.assess(country, mode).model_dump(mode="json")
        n += 1
        if ins["evidence"]:
            evidence_complete += 1
        text = _verdict_text(ins)
        hits = [kw for kw in expected if kw.lower() in text.lower()]
        total_expected += len(expected)
        hit_expected += len(hits)
        cases.append(
            {
                "country": country,
                "mode": mode,
                "expected": expected,
                "hits": hits,
                "recall": round(len(hits) / len(expected), 2),
            }
        )

    return {
        "accuracy": round(hit_expected / total_expected, 4) if total_expected else 0.0,
        "evidence_completeness": round(evidence_complete / n, 4) if n else 0.0,
        "n_cases": n,
        "cases": cases,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate_m5(), ensure_ascii=False, indent=2))
