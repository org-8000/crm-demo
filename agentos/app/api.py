"""自定义业务 API（FastAPI Router），可独立于 Agno 用 TestClient 测试。

端点：
- GET  /insights            列出洞察（module/status 过滤）
- GET  /insights/{id}       取单条
- POST /m5/assess           运行⑤合规准入并持久化，返回带 steps 的结果
- POST /m3/research         运行③客户研判并持久化，返回带 steps 的结果
- GET  /review              接管队列（needs_human 且 new）
- POST /insights/{id}/review 处理接管（approve/reject/escalate + 反馈）

依赖注入：repo(InsightRepo) / knowledge / registry / enrich，便于测试替换。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.m3_profile import ProfileEngine, country_for_compliance
from modules.m5_compliance import ComplianceEngine


class AssessRequest(BaseModel):
    country: str
    business_mode: str = "cross-border acquiring"


class ResearchRequest(BaseModel):
    name: str
    homepage_url: str
    country: str | None = None
    business_mode: str | None = None


class ReviewRequest(BaseModel):
    action: str  # approve|reject|escalate
    note: str | None = None


_ACTION_STATUS = {
    "approve": "actioned",
    "reject": "dismissed",
    "escalate": "reviewed",
}


def build_api_router(repo, knowledge=None, registry=None, enrich=None, notify=None) -> APIRouter:
    router = APIRouter(tags=["mip"])
    compliance = ComplianceEngine(knowledge=knowledge) if knowledge is not None else None
    profile = (
        ProfileEngine(registry=registry, knowledge=knowledge, enrich=enrich)
        if registry is not None
        else None
    )

    @router.get("/insights")
    def list_insights(module: str | None = None, status: str | None = None, limit: int = 100):
        return repo.list(module=module, status=status, limit=limit)

    @router.get("/insights/{insight_id}")
    def get_insight(insight_id: int) -> dict[str, Any]:
        row = repo.get(insight_id)
        if not row:
            raise HTTPException(status_code=404, detail="insight 不存在")
        return row

    @router.post("/m5/assess")
    def m5_assess(req: AssessRequest):
        if compliance is None:
            raise HTTPException(status_code=503, detail="知识库未配置")
        steps = ["检索监管本体", "组装准入清单", "生成证据链"]
        ins = compliance.assess(req.country, req.business_mode)
        saved = repo.save(ins)
        if notify:
            notify(ins)
        return {"insight": saved, "steps": steps}

    @router.post("/m3/research")
    def m3_research(req: ResearchRequest):
        if profile is None:
            raise HTTPException(status_code=503, detail="采集注册表未配置")
        steps = ["抓取机构主页", "提取业务聚焦/切入点/风险", "生成画像"]
        ins = profile.research(
            req.name, req.homepage_url, country=req.country, business_mode=req.business_mode
        )
        saved = repo.save(ins)
        result: dict[str, Any] = {"insight": saved, "steps": steps}
        # 串联：带出可用于⑤的国家
        result["linked_country"] = country_for_compliance(ins)
        return result

    @router.get("/review")
    def review_queue(limit: int = 100):
        return repo.list(needs_human=True, status="new", limit=limit)

    @router.post("/insights/{insight_id}/review")
    def review_action(insight_id: int, req: ReviewRequest):
        status = _ACTION_STATUS.get(req.action)
        if not status:
            raise HTTPException(status_code=400, detail=f"未知 action：{req.action}")
        updated = repo.update_status(insight_id, status)
        if not updated:
            raise HTTPException(status_code=404, detail="insight 不存在")
        # 反馈写回（learnings 占位：生产写 agno_learnings）
        return {"insight": updated, "feedback_recorded": bool(req.note)}

    return router
