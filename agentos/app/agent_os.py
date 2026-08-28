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


def build_agent_os():
    """构建并返回 (agent_os, fastapi_app)。"""
    from agno.db.postgres import PostgresDb
    from agno.os import AgentOS

    db_url = os.environ.get(
        "DATABASE_URL", "postgresql+psycopg://mip:mip@localhost:5432/mip"
    )
    db = PostgresDb(db_url=db_url)

    # P1+ 在此注入模块化 Team/Workflow：
    #   from modules import m5_compliance, m3_profile
    #   teams=[m3_profile.build_team(...)]; workflows=[m5_compliance.build_workflow(...)]
    agents: list = []
    teams: list = []
    workflows: list = []

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
except Exception:  # noqa: BLE001 - 缺少 serve 依赖或 DB 时不阻塞导入分析
    _agent_os = None
    app = None
