"""提取 Pipeline 底座：RawDocument → NormalizedEntity[]。

分两层：
1. 确定性抽取（生产用 GLiNER2；此处提供可插拔 `EntityExtractor` 协议，
   并内置一个基于规则的 `RegexEntityExtractor` 兜底实现，保证离线可测）。
2. LLM schema 约束抽取（可插拔 `SchemaExtractor` 协议，用于复杂语义/观点提炼）。

上层只依赖协议，生产环境注入 GLiNER2 / LLM 实现即可。
"""

from __future__ import annotations

import re
from typing import Protocol

from core.models import Entity
from core.tools.base import RawDocument


class EntityExtractor(Protocol):
    """确定性实体抽取协议（生产：GLiNER2）。"""

    def extract(self, text: str, entity_types: list[str]) -> list[Entity]: ...


class RegexEntityExtractor:
    """规则兜底抽取器：无需模型即可抽取常见实体（金额/日期/牌照关键词等）。

    仅用于底座冒烟与离线测试；生产用 GLiNER2 替换。
    """

    _PATTERNS: dict[str, re.Pattern] = {
        "amount": re.compile(r"(?:USD|US\$|\$|EUR|€|RMB|¥)\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:million|亿|万))?", re.I),
        "date": re.compile(r"\b\d{4}[-/年]\d{1,2}[-/月]\d{1,2}\b"),
        "license": re.compile(r"\b(?:MPI|MAS|PJP|EMI|PI|PSP|MSB|license|licence|牌照)\b", re.I),
        "standard": re.compile(r"\bISO\s?\d{3,5}\b", re.I),
    }

    def extract(self, text: str, entity_types: list[str]) -> list[Entity]:
        out: list[Entity] = []
        for etype in entity_types:
            pat = self._PATTERNS.get(etype)
            if not pat:
                continue
            for m in pat.finditer(text):
                out.append(
                    Entity(
                        type=etype,
                        value=m.group(0),
                        confidence=0.7,
                        source_ref={"offset": m.start()},
                    )
                )
        return out


class SchemaExtractor(Protocol):
    """LLM schema 约束抽取协议（生产：模型无关 LLM，输出受 Pydantic schema 约束）。"""

    def extract_schema(self, text: str, schema: type) -> dict: ...


class ExtractionPipeline:
    """把确定性抽取与（可选）LLM schema 抽取组合起来。"""

    def __init__(
        self,
        entity_extractor: EntityExtractor | None = None,
        schema_extractor: SchemaExtractor | None = None,
    ):
        self.entity_extractor = entity_extractor or RegexEntityExtractor()
        self.schema_extractor = schema_extractor

    def entities(self, doc: RawDocument, entity_types: list[str]) -> list[Entity]:
        return self.entity_extractor.extract(doc.content, entity_types)

    def structured(self, doc: RawDocument, schema: type) -> dict:
        if not self.schema_extractor:
            raise RuntimeError("未配置 SchemaExtractor（LLM）；请注入生产实现")
        return self.schema_extractor.extract_schema(doc.content, schema)
