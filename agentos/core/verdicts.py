"""各模块的 verdict schema（结构化判断）。

每个模块产出不同的 verdict，但都通过 `to_insight()` 归一到统一 Insight。
P0 定义基类与 M3/M5（MVP 首选）的 schema；其余模块在对应期补充。
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from core.models import Evidence, Insight, ModuleId


class BaseVerdict(BaseModel):
    """verdict 基类：提供归一到 Insight 的能力。"""

    module: ModuleId
    subject: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    risk_flags: list[str] = Field(default_factory=list)

    def verdict_payload(self) -> dict:
        """返回除公共字段外的业务判断字段。"""
        return self.model_dump(exclude={"module", "subject", "confidence", "risk_flags"})

    def to_insight(self, evidence: list[Evidence], linked_org_id: int | None = None) -> Insight:
        return Insight(
            module=self.module,
            subject=self.subject,
            verdict=self.verdict_payload(),
            confidence=self.confidence,
            risk_flags=self.risk_flags,
            evidence=evidence,
            linked_org_id=linked_org_id,
        ).finalize()


# ---------------- M3 客户画像与商机研判 ----------------

class EntryPoint(BaseModel):
    title: str
    rationale: str


class ProfileVerdict(BaseVerdict):
    module: ModuleId = ModuleId.M3_PROFILE
    profile: str = Field(..., description="机构画像摘要")
    business_focus: list[str] = Field(default_factory=list)
    entry_points: list[EntryPoint] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    contacts: list[dict] = Field(default_factory=list, description="联系人(来自合规富化, 含 pii_ttl)")
    fit_score: float = Field(ge=0.0, le=1.0, default=0.0)


# ---------------- M5 合规准入筛查 ----------------

class AdmissionItem(BaseModel):
    """准入清单条目（每条都应有证据支撑）。"""

    title: str
    detail: str
    severity: str = Field(default="info", description="info|warn|block")


class AdmissionVerdict(BaseVerdict):
    module: ModuleId = ModuleId.M5_COMPLIANCE
    country: str
    business_mode: str
    licenses: list[AdmissionItem] = Field(default_factory=list)
    messaging_standards: list[AdmissionItem] = Field(default_factory=list)
    data_compliance: list[AdmissionItem] = Field(default_factory=list)
    business_restrictions: list[AdmissionItem] = Field(default_factory=list)
    readiness_summary: str = ""
