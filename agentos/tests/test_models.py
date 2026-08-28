"""Insight / Evidence / verdict 模型单测。"""

import pytest
from pydantic import ValidationError

from core.models import Evidence, Insight, ModuleId, SourceType
from core.verdicts import AdmissionItem, AdmissionVerdict, EntryPoint, ProfileVerdict


def _ev(snippet="来源片段"):
    return Evidence(source_url="https://example.com", source_type=SourceType.WEB, snippet=snippet)


def test_insight_requires_evidence():
    with pytest.raises(ValidationError):
        Insight(module=ModuleId.M3_PROFILE, subject="Acme", evidence=[])


def test_evidence_snippet_not_empty():
    with pytest.raises(ValidationError):
        Evidence(source_url="https://x.com", snippet="  ")


def test_finalize_sets_needs_human_on_low_confidence():
    ins = Insight(module=ModuleId.M3_PROFILE, subject="Acme", confidence=0.4, evidence=[_ev()])
    ins.finalize()
    assert ins.needs_human is True


def test_finalize_high_confidence_no_human():
    ins = Insight(module=ModuleId.M5_COMPLIANCE, subject="SG", confidence=0.9, evidence=[_ev()])
    ins.finalize()
    assert ins.needs_human is False


def test_threshold_is_classvar_not_field():
    # LOW_CONFIDENCE_THRESHOLD 应为 ClassVar，不进入字段/序列化，且不可被构造覆盖
    ins = Insight(module=ModuleId.M3_PROFILE, subject="Acme", confidence=0.9, evidence=[_ev()])
    assert "LOW_CONFIDENCE_THRESHOLD" not in ins.model_dump()
    assert "LOW_CONFIDENCE_THRESHOLD" not in Insight.model_fields


def test_profile_verdict_to_insight():
    v = ProfileVerdict(
        subject="Acme Payments",
        confidence=0.82,
        profile="跨境收单机构",
        business_focus=["跨境收单", "钱包"],
        entry_points=[EntryPoint(title="申请 MPI 牌照", rationale="正在扩牌")],
        risks=["母公司制裁关联待核"],
        fit_score=0.82,
    )
    ins = v.to_insight(evidence=[_ev()])
    assert ins.module == ModuleId.M3_PROFILE
    assert ins.verdict["fit_score"] == 0.82
    assert "profile" in ins.verdict
    # 公共字段不应出现在 verdict payload 内
    assert "module" not in ins.verdict and "subject" not in ins.verdict


def test_admission_verdict_to_insight():
    v = AdmissionVerdict(
        subject="印尼 / 跨境收单",
        country="Indonesia",
        business_mode="cross-border acquiring",
        confidence=0.75,
        licenses=[AdmissionItem(title="PJP 牌照", detail="需 Bank Indonesia 批准", severity="block")],
        readiness_summary="中等，主要卡点=数据本地化",
    )
    ins = v.to_insight(evidence=[_ev()])
    assert ins.module == ModuleId.M5_COMPLIANCE
    assert ins.verdict["country"] == "Indonesia"
    assert ins.verdict["licenses"][0]["severity"] == "block"
