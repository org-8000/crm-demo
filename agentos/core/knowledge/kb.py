"""知识库配置（pgvector）。

定义共享知识库的名称与嵌入维度；真实向量读写在 serve 环境用 Agno Knowledge + PgVector。
此处提供纯配置 + 一个内存版 `InMemoryKnowledgeBase`（余弦相似）用于离线测试与冒烟。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

# 共享知识库名（与技术文档 §4.3 对应）
KB_PAYMENT_ONTOLOGY = "kb_payment_ontology"  # 支付牌照/报文标准/辖区本体（⑤③ 护城河）
KB_ORG_PROFILES = "kb_org_profiles"          # 机构历史资料（③）
KB_SOURCES = "kb_sources"                    # 可信来源库（①⑤）

DEFAULT_EMBEDDING_DIM = 1536


@dataclass
class KBChunk:
    kb_name: str
    content: str
    source_ref: dict = field(default_factory=dict)
    embedding: list[float] | None = None


class KnowledgeBase(Protocol):
    def add(self, chunk: KBChunk) -> None: ...
    def search(self, kb_name: str, query: str, top_k: int = 5) -> list[KBChunk]: ...


class InMemoryKnowledgeBase:
    """离线测试用知识库：基于词重叠的朴素检索（非向量，仅用于冒烟）。

    生产环境用 Agno Knowledge + PgVector（混合检索 / 余弦相似），接口保持一致。
    """

    def __init__(self) -> None:
        self._store: list[KBChunk] = []

    def add(self, chunk: KBChunk) -> None:
        self._store.append(chunk)

    def search(self, kb_name: str, query: str, top_k: int = 5) -> list[KBChunk]:
        q_terms = set(_tokenize(query))
        scored: list[tuple[float, KBChunk]] = []
        for c in self._store:
            if c.kb_name != kb_name:
                continue
            c_terms = set(_tokenize(c.content))
            if not c_terms:
                continue
            overlap = len(q_terms & c_terms) / (len(q_terms) or 1)
            if overlap > 0:
                scored.append((overlap, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]


def _tokenize(text: str) -> list[str]:
    import re

    return [t for t in re.split(r"[^\w]+", text.lower()) if t]
