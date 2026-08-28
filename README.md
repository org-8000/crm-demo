# 市场智能情报与获客平台（Market Intelligence & Outreach Platform）

面向支付/金融行业、基于公开互联网信息的 AI 驱动市场情报与获客平台。
详见 [`docs/`](./docs)：调研报告、技术设计、UI/UX 与用户故事、实施分期计划、Sprint 分解。

## 架构（少而精，3 个常驻组件）

```
web (Next.js/React)  ─BFF→  agentos (FastAPI/Agno)  ─SQL/pgvector→  PostgreSQL(+pgvector)
```

- **agentos/**：Agno AgentOS 后端。核心 SDK（`core/`：models/tools/extract/knowledge/compliance）不依赖 Agno/DB，可离线单测；`app/agent_os.py` 装配 AgentOS；`modules/` 放各业务模块（P1+）。
- **web/**：Next.js 前端。统一 `InsightCard` + `ReviewQueue` + 六模块导航；BFF 代理 AgentOS。
- **PostgreSQL + pgvector**：业务表（`agentos/migrations/001_init.sql`）+ Agno 系统表同库。

## 快速开始

```bash
cp .env.example .env            # 按需填入 LLM / Firecrawl / Proxycurl 等 key
docker compose up --build       # 启动 postgres + agentos + web
# web:      http://localhost:3000
# agentos:  http://localhost:8000
```

## 本地开发 / 测试

后端核心 SDK（无需 Agno/DB）：
```bash
cd agentos
uv venv .venv --python 3.13 && uv pip install pydantic pytest ruff
.venv/bin/python -m pytest -q          # 单测
.venv/bin/python -m ruff check core modules app tests
# 运行完整服务需额外依赖：uv pip install '.[serve]'
```

前端：
```bash
cd web
npm install
npm run typecheck && npm run build     # 类型检查 + 构建
npm run dev                            # 本地开发
```

## 合规基线

- 高风险能力默认关闭，由 feature flag 控制：`ENABLE_M2_GROUP_MONITOR`、`ENABLE_M6_AUTOSEND`、`ENABLE_SOCIAL_DEEP_SCRAPE`。
- 数据源分级（🟢 web/regulator/doc；🟡 social；🔴 group/linkedin）由 `core/compliance.py` 的 `ComplianceGateway` 前置校验。
- 联系人 PII 落 `person.pii_ttl`，最小化留存、可删除。

## 实施进度

- **P0 工程底座**：3 组件打通、共享底座 SDK、AgentOS 骨架、PG DDL、前端骨架、CI ✅
- **P1（MVP）**：③客户研判 + ⑤合规准入（进行中）
- 详见 `docs/实施分期计划` 与 `docs/Sprint分解_P0-P1`。
