"""核心领域模型（统一 Insight 对象、证据链、实体、各模块 verdict schema）。

设计要点：
- 纯 pydantic，不依赖 agno/DB/LLM，保证单测可离线运行。
- 所有模块共享同一个 Insight/Evidence 结构，前端一套 InsightCard 即可渲染。
- 每条 Insight 必须携带证据链（evidence），无证据不予展示（合规/反幻觉）。
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, ClassVar

from pydantic import BaseModel, Field, field_validator


def _now() -> datetime:
    return datetime.now(UTC)


class ModuleId(str, Enum):
    """六大业务模块标识。"""

    M1_INTEL = "M1"        # 行业情报采集
    M2_TENDER = "M2"       # 招标信息监控
    M3_PROFILE = "M3"      # 客户画像与商机研判
    M4_SUMMIT = "M4"       # 峰会商机挖掘
    M5_COMPLIANCE = "M5"   # 合规准入筛查
    M6_OUTREACH = "M6"     # LinkedIn 智能获客


class ComplianceLevel(str, Enum):
    """数据源/操作合规等级。"""

    GREEN = "green"    # 公开合规
    YELLOW = "yellow"  # 中风险（社媒 ToS 等）
    RED = "red"        # 高风险（群聊/认证态自动化等），默认关闭


class SourceType(str, Enum):
    WEB = "web"
    REGULATOR = "regulator"
    SOCIAL = "social"
    GROUP = "group"
    DOC = "doc"
    LINKEDIN = "linkedin"
    SEARCH = "search"


class InsightStatus(str, Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    ACTIONED = "actioned"
    DISMISSED = "dismissed"


class Evidence(BaseModel):
    """证据条目：支撑某条判断的原文出处，用于溯源。"""

    source_url: str
    source_type: SourceType = SourceType.WEB
    snippet: str = Field(..., description="原文片段，用于人工快速核验")
    fetched_at: datetime = Field(default_factory=_now)

    @field_validator("snippet")
    @classmethod
    def _snippet_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("evidence.snippet 不能为空")
        return v


class Entity(BaseModel):
    """提取层产出的规范化实体。"""

    type: str = Field(..., description="实体类型，如 org/person/license/amount/date/event")
    value: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    source_ref: dict[str, Any] | None = Field(
        default=None, description="回指原文位置（url/offset 等）"
    )


class Insight(BaseModel):
    """统一洞察对象（六模块共用）。

    verdict 为各模块专属的结构化判断（见 verdicts.py），此处以 dict 存储，
    便于统一落库与前端渲染；具体 schema 在生成侧用强类型校验后 dump。
    """

    module: ModuleId
    subject: str = Field(..., description="机构名/国家/线索标题")
    verdict: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    risk_flags: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    needs_human: bool = False
    status: InsightStatus = InsightStatus.NEW
    linked_org_id: int | None = None
    # 跨模块串联上下文（如国家/业务模式），不参与前端 verdict 渲染，避免泄漏到卡片
    chain_context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)

    # 低置信阈值：低于此值默认需要人工复核（ClassVar，非模型字段，不进入 model_dump）
    LOW_CONFIDENCE_THRESHOLD: ClassVar[float] = 0.6

    @field_validator("evidence")
    @classmethod
    def _require_evidence(cls, v: list[Evidence]) -> list[Evidence]:
        if not v:
            raise ValueError("Insight 必须携带至少一条证据（无证据不展示）")
        return v

    def finalize(self) -> Insight:
        """根据置信度自动置位 needs_human。生成流程末尾调用。"""
        if self.confidence < self.LOW_CONFIDENCE_THRESHOLD:
            self.needs_human = True
        return self
