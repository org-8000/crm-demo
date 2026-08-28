"""知识库种子数据。

- payment_ontology_seed()：支付牌照/报文标准/数据合规/业务限制的本体条目（⑤③ 复用）。
  每条含 source_ref（监管出处），供生成 Insight 时构建证据链。

生产环境应从监管官网抓取 + 人工校订后写入 pgvector；此处提供可运行的最小真实内容，
覆盖新加坡/印尼两个目标国，用于 MVP 演示与离线测试。
"""

from __future__ import annotations

from core.knowledge.kb import KB_PAYMENT_ONTOLOGY, KBChunk, KnowledgeBase

# (country, category, title, detail, severity, source_url)
_ONTOLOGY: list[tuple[str, str, str, str, str, str]] = [
    # --- Singapore ---
    ("Singapore", "license", "Major Payment Institution (MPI) 牌照",
     "在新加坡提供超过阈值的支付服务需向 MAS 申请 MPI 牌照（Payment Services Act 2019）。",
     "block", "https://www.mas.gov.sg/regulation/payments/entities-that-are-licensed-under-psa"),
    ("Singapore", "messaging", "ISO 20022 报文标准",
     "新加坡快速支付系统 FAST / PayNow 采用 ISO 20022 报文；跨境需兼容。",
     "warn", "https://www.mas.gov.sg/"),
    ("Singapore", "data", "个人数据保护法 (PDPA)",
     "处理个人数据须遵守 PDPA，明确同意、用途限制与保护义务。",
     "warn", "https://www.pdpc.gov.sg/"),
    ("Singapore", "restriction", "反洗钱/反恐融资 (AML/CFT)",
     "须建立符合 MAS Notice PSN01 的 AML/CFT 制度与客户尽调。",
     "warn", "https://www.mas.gov.sg/regulation/notices"),
    # --- Indonesia ---
    ("Indonesia", "license", "Bank Indonesia PJP 牌照",
     "支付服务提供商 (PJP) 须取得 Bank Indonesia 许可（PBI 22/23）。",
     "block", "https://www.bi.go.id/en/publikasi/peraturan/"),
    ("Indonesia", "messaging", "国家支付网关 (GPN/NPG)",
     "境内借记/信用交易须经由国家支付网关处理；报文遵循本地标准。",
     "warn", "https://www.bi.go.id/"),
    ("Indonesia", "data", "数据本地化 (PP 71/2019)",
     "电子系统提供者的部分数据须在印尼境内存储与处理。",
     "block", "https://www.kominfo.go.id/"),
    ("Indonesia", "restriction", "外资持股上限",
     "支付领域外资持股比例受限，须满足本地股权要求。",
     "warn", "https://www.bi.go.id/"),
]


def payment_ontology_chunks() -> list[KBChunk]:
    chunks: list[KBChunk] = []
    for country, category, title, detail, severity, url in _ONTOLOGY:
        chunks.append(
            KBChunk(
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
        )
    return chunks


def seed_payment_ontology(kb: KnowledgeBase) -> int:
    """把支付本体写入知识库，返回写入条数。"""
    chunks = payment_ontology_chunks()
    for c in chunks:
        kb.add(c)
    return len(chunks)
