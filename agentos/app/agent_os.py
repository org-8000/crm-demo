"""AgentOS 装配骨架（P0）。

AgentOS 本身是一个 FastAPI 应用，统一承载 agents/teams/workflows +
sessions/memory/knowledge/schedules(cron)/approvals(HITL)/traces。

P0：仅装配骨架（无业务模块，agents/teams/workflows 为空）。
P1+：从 modules/ 注入 ③⑤ 等 Team/Workflow。

依赖 agno/fastapi/sqlalchemy/psycopg（`pip install -e '.[serve]'`）。
未安装 serve 依赖时导入本模块会报错，属预期——核心 SDK 单测不导入本模块。
"""

from __future__ import annotations

import os


def _default_model():
    """按环境变量构造默认 LLM；未配置 key 时返回 None（仅装配骨架，运行时再配）。"""
    try:
        if os.getenv("OPENAI_API_KEY"):
            from agno.models.openai import OpenAIChat

            return OpenAIChat(id=os.getenv("MIP_MODEL", "gpt-4o-mini"))
        if os.getenv("ANTHROPIC_API_KEY"):
            from agno.models.anthropic import Claude

            return Claude(id=os.getenv("MIP_MODEL", "claude-3-5-sonnet-latest"))
    except Exception:  # noqa: BLE001 - 缺少模型 SDK 时不阻塞装配
        return None
    return None


def build_agent_os():
    """构建并返回 (agent_os, fastapi_app)。"""
    from agno.db.postgres import PostgresDb
    from agno.os import AgentOS

    db_url = os.environ.get(
        "DATABASE_URL", "postgresql+psycopg://mip:mip@localhost:5432/mip"
    )
    db = PostgresDb(db_url=db_url)

    # 注册 P1 模块：⑤ 合规准入（Workflow，无需 LLM，始终装配）
    #                ③ 客户研判（Team，需 LLM；未配置 key 时跳过，避免构建失败）
    from modules import m3_profile, m5_compliance

    agents: list = []
    workflows: list = [m5_compliance.build_workflow()]
    teams: list = []
    model = _default_model()
    if model is not None:
        teams.append(m3_profile.build_team(model=model))

    agent_os = AgentOS(
        name="market-intelligence-platform",
        description="市场智能情报与获客平台",
        db=db,
        agents=agents or None,
        teams=teams or None,
        workflows=workflows or None,
        # 生产自管 schema 时设为 False（业务表用 migrations/*.sql）
        auto_provision_dbs=os.getenv("AUTO_PROVISION_DBS", "true").lower() == "true",
    )
    app = agent_os.get_app()
    return agent_os, app


# uvicorn app.agent_os:app 需要模块级 app。延迟到导入时构建。
try:  # pragma: no cover - 仅在 serve 环境可用
    _agent_os, app = build_agent_os()
except Exception as _e:  # noqa: BLE001 - 缺少 serve 依赖或 DB 时不阻塞导入分析
    import logging

    logging.getLogger(__name__).warning("AgentOS 未在导入期构建（缺少 serve 依赖或 DB）：%s", _e)
    _agent_os = None
    app = None
