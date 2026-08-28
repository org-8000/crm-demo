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
uv venv .venv --python 3.13 && uv pip install -e '.[serve,dev]'
.venv/bin/python -m pytest -q          # 全量单测（含持久化/API/富化/通知/评估）
.venv/bin/python -m ruff check core modules app scripts tests
.venv/bin/python -m modules.demo       # ③→⑤ 端到端离线演示
.venv/bin/python -m modules.eval       # 评估基线（准确率/证据齐全率）
```

不装 Agno/PG 也能起后端联调（SQLite + 内存知识库种子）：
```bash
cd agentos
.venv/bin/python -m uvicorn scripts.serve_api:app --port 8000
# POST /m5/assess {country,business_mode} · POST /m3/research · GET /insights · GET /review
```

前端（连后端跑通端到端）：
```bash
cd web
npm install
npm run typecheck && npm run build
AGENTOS_BASE_URL=http://localhost:8000 npm run dev   # http://localhost:3000
# M5 输入国家→真实准入清单；M3 输入机构→真实画像；接管队列可采纳/升级/忽略
```

## 已接通的端到端能力（P0/P1 收口）

- **持久化**：`app/db.py` 用 SQLAlchemy JSON 列，SQLite（测试）/PostgreSQL（生产）通用；Insight 落 `insight` 表。
- **业务 API**：`app/api.py` 提供 `/insights`、`/m5/assess`、`/m3/research`、`/review`、`/insights/{id}/review`，挂到 AgentOS，也可用 TestClient 独测。
- **前端接通**：M3/M5 输入页 → BFF(`/api/*`) → 后端 → 落库 → InsightCard（含证据弹层、步骤条）；接管队列实时读写。
- **联系人富化**：Proxycurl 适配器（🟢 付费合规，key-gated），PII 落 `pii_ttl` + `legal_basis`。
- **监管拓展**：`ingest_regulator_page` 从活页解析入知识库；`run_subscriptions` 订阅国家批量出清单+通知（可 cron）。
- **通知**：`core/notify.py` 飞书/Slack webhook 抽象 + Insight 格式化。
- **评估基线**：`modules/eval.py` 黄金样本，准确率 / 证据齐全率。

## 合规基线

- 高风险能力默认关闭，由 feature flag 控制：`ENABLE_M2_GROUP_MONITOR`、`ENABLE_M6_AUTOSEND`、`ENABLE_SOCIAL_DEEP_SCRAPE`。
- 数据源分级（🟢 web/regulator/doc；🟡 social；🔴 group/linkedin）由 `core/compliance.py` 的 `ComplianceGateway` 前置校验。
- 联系人 PII 落 `person.pii_ttl`，最小化留存、可删除。

## 实施进度

- **P0 工程底座**：3 组件打通、共享底座 SDK、AgentOS 骨架、PG DDL、前端骨架、CI ✅
- **P1（MVP）**：③客户研判 + ⑤合规准入（进行中）
- 详见 `docs/实施分期计划` 与 `docs/Sprint分解_P0-P1`。
