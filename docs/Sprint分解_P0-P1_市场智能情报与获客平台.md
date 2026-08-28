# P0 / P1 — Sprint 级任务分解

> 配套《实施分期计划》。栈：Python + Agno(AgentOS) + Next.js + PostgreSQL(pgvector)。
> 采用 **1 周 Sprint**；团队 ~4 人：**BE1 / BE2**(后端)、**FE**(前端)、**FS/ML**(全栈+算法/知识)。
> 估算单位：**pt（人天）**。任务 ID 便于导入 Jira/Linear。DoD=Definition of Done。
> 版本：v1.0 ｜ 2026-08

---

## 角色与容量假设
| 角色 | 职责 | 周容量 |
|---|---|---|
| BE1 | AgentOS/Agno 编排、调度、审批 | 5 pt |
| BE2 | 采集 Tools、数据模型、迁移 | 5 pt |
| FS/ML | 提取 Pipeline、知识库/RAG、评估 | 5 pt |
| FE | Next.js、组件、BFF、接管队列 | 5 pt |

> 每周约 20 pt 团队容量；下方每 Sprint 控制在 ~18–20 pt 留缓冲。

---

# P0 · 工程底座（3 个 Sprint）

**P0 出口目标**：一条"假 Insight"从 API→PG→前端 InsightCard 渲染+证据链可点开；调度/审批冒烟通过；CI 全绿。

---

## Sprint 0.1 — 骨架与打通（"Hello Insight"）

**Sprint 目标**：三组件 `docker compose up` 起来，前后端跑通一条链路。

| ID | 任务 | 角色 | pt | 依赖 | 验收(AC) |
|---|---|---|---|---|---|
| P0-101 | 技术验证 spike：Agno 2.0 版本/AgentOS/schedules/approvals API 核对 | BE1 | 1 | — | 输出 1 页可行性结论 + 锁定版本 |
| P0-102 | Monorepo + docker-compose(web/agentos/postgres+pgvector) + .env 模板 | BE2 | 2 | — | `docker compose up` 三容器健康 |
| P0-103 | AgentOS 装配 `get_app()` + PG 连接 + `auto_provision_dbs` | BE1 | 2 | 102 | 启动自动建 `agno_*` 表；/health 200 |
| P0-104 | 业务 DDL v1（org/person/watch_source/insight/ingestion_log/kb_chunk）+ 迁移工具 | BE2 | 2 | 102 | 迁移可 up/down；ER 图产出 |
| P0-105 | `Insight`/`Evidence`/`Entity` Pydantic 模型 + 一条 seed 假数据 API | FS/ML | 1 | 104 | GET /insights 返回 seed |
| P0-106 | Next.js 骨架：布局+左侧导航(6模块+接管+设置) | FE | 2 | — | 导航可点，路由占位页 |
| P0-107 | 统一 `InsightCard` 组件 + Storybook + 假数据渲染 | FE | 3 | 105 | 卡片渲染判断/置信度/合规角标/证据入口 |
| P0-108 | BFF：Next API Route 代理 AgentOS + `OS_SECURITY_KEY` 注入 | FE | 2 | 103,105 | 前端经 BFF 拉到 seed Insight |
| P0-109 | CI 骨架(lint/test/build：ruff+eslint+pytest) | BE2 | 2 | 102 | PR 触发 CI 全绿 |

**Sprint DoD**：前端 InsightCard 显示后端 seed 数据；CI 通过；README 可复现。合计 ~17 pt。

---

## Sprint 0.2 — 共享底座能力层

**Sprint 目标**：采集/提取/知识/合规四大底座能力可用（接口 + 最小实现）。

| ID | 任务 | 角色 | pt | 依赖 | 验收(AC) |
|---|---|---|---|---|---|
| P0-201 | 采集 Tools 接口 + `web_fetch`(Firecrawl/Crawl4AI) + `search_web` | BE2 | 3 | P0-103 | 给 URL 返回统一 `RawDocument`；写 `ingestion_log` |
| P0-202 | Tool 适配器框架(可插拔+超时/重试/限速) | BE2 | 2 | 201 | 换适配器不改上层；单测覆盖 |
| P0-203 | 提取 Pipeline：GLiNER2 集成(实体/schema 抽取) | FS/ML | 3 | P0-105 | 文本→`NormalizedEntity[]`，带 source_ref |
| P0-204 | 提取 LLM 兜底：Pydantic-schema 约束输出(模型无关) | FS/ML | 2 | 203 | 复杂文本→结构化 JSON，schema 校验通过 |
| P0-205 | Knowledge/pgvector：Agno Knowledge + PgVector 混合检索 | FS/ML | 3 | P0-104 | 写入/检索 kb_chunk；hnsw 索引生效 |
| P0-206 | 合规网关：来源分级校验 + PII TTL 字段 + feature flags 读取 | BE1 | 2 | P0-104 | 采集前校验；flag 关闭时 Tool 拒绝执行 |
| P0-207 | 通知适配器(飞书/Slack Webhook) 抽象 | BE1 | 1 | — | 发送一条测试通知成功 |
| P0-208 | 前端：ReviewQueue 空壳页 + 概览指标卡骨架 | FE | 3 | P0-107 | 队列/概览可渲染假数据 |

**Sprint DoD**：能"取一个真实网页→抽取实体→写/检索知识库"，全程写审计；flag 生效。合计 ~19 pt。

---

## Sprint 0.3 — 编排/调度/审批 + 工程化收口

**Sprint 目标**：Agno schedules(cron) 与 approvals(HITL) 打通到前端；P0 出口达成。

| ID | 任务 | 角色 | pt | 依赖 | 验收(AC) |
|---|---|---|---|---|---|
| P0-301 | Agno `schedules` 冒烟：注册 cron→写 `agno_schedules`→触发一次 | BE1 | 2 | Sprint0.2 | 定时任务产出一条 Insight |
| P0-302 | Agno `approvals`(HITL)：`requires_confirmation` 工具→写 `agno_approvals` | BE1 | 3 | P0-206 | 触发一条待审批并可查询 |
| P0-303 | 接管队列后端 API：列出/批准/拒绝/升级 + 状态流转 | BE2 | 3 | 302 | new→reviewed→actioned/dismissed 正确 |
| P0-304 | 反馈写回 `agno_learnings`(误报/修正) 接口 | FS/ML | 2 | 303 | 反馈落库，可读取 |
| P0-305 | 前端接管队列(可用)：消费 approvals + 批准/编辑/升级/反馈 | FE | 3 | 303 | 端到端处理一条审批 |
| P0-306 | 前端：证据链弹层(点回原文快照) | FE | 2 | P0-201 | 从卡片打开证据看到 URL/片段/时间 |
| P0-307 | OpenTelemetry traces 接入 + 实时步骤条数据源 | BE1 | 2 | P0-103 | 前端可显示一次运行的步骤 |
| P0-308 | 部署手册 + 密钥管理 + `.env.example` 收口 + 冒烟脚本 | BE2 | 2 | 全部 | 新人按手册 30 分钟起环境 |

**Sprint DoD（=P0 Exit Gate）**：
- cron 自动产出 Insight → 前端可见；审批链路端到端可用；证据链可溯源。
- CI 全绿、无明文密钥、冒烟脚本通过。合计 ~19 pt。

**P0 交付产物汇总**：可运行全栈环境、PG 迁移+ER 图、底座 SDK(tools/extract/knowledge/models/compliance)、InsightCard+ReviewQueue、CI+部署手册、合规基线文档、feature flag 清单。

---

# P1 · MVP：客户研判③ + 合规准入⑤（4 个 Sprint）

**P1 出口目标**：真实机构名→60s 出带证据链的画像/切入点/风险；⑤ 出四类准入清单可溯源；③↔⑤ 串联；低置信进接管；核心样本人工评估通过率 ≥80%，证据齐全率 100%。

---

## Sprint 1.1 — 模块⑤ 合规准入（先做，数据源最干净）

**Sprint 目标**：输入国家+业务模式→生成准入清单(附监管原文)。

| ID | 任务 | 角色 | pt | 依赖 | 验收(AC) |
|---|---|---|---|---|---|
| P1-101 | `regulator_fetch(country)` 适配器(2–3 个目标国监管站) | BE2 | 3 | P0-201 | 返回监管页 RawDocument + 审计 |
| P1-102 | `kb_payment_ontology` 建库：牌照/ISO20022/8583/辖区本体 + 导入脚本 | FS/ML | 3 | P0-205 | 检索命中相关条目 top-k |
| P1-103 | Docling 文档解析(监管 PDF→结构) 接入 | FS/ML | 2 | P0-203 | PDF→分块+source_ref |
| P1-104 | ⑤ Workflow + `AdmissionVerdict` schema(licenses/messaging/data/restrictions/summary) | BE1 | 3 | 101,102 | 输出四类清单，每条带 evidence |
| P1-105 | ⑤ ResearchAgent 提示词 + RAG 融合 + 置信度评分 | BE1 | 2 | 104 | 结论引用检索证据；给 confidence |
| P1-106 | 前端 M5 准入页：输入→流式步骤→清单卡+证据 | FE | 3 | P0-306,307 | 端到端展示一国清单 |
| P1-107 | ⑤ 评估集(≥10 国家×模式黄金样本)+准确率/证据齐全率脚本 | FS/ML | 2 | 104 | 产出基线报告 |
| P1-108 | 导出 PDF + "订阅该国监管变更(cron)" 入口 | FE | 2 | 106,P0-301 | 导出成功；可建订阅 |

**Sprint DoD**：真实"目标国+模式"→四类准入清单，每条可点回监管原文；评估基线出炉。合计 ~20 pt。

---

## Sprint 1.2 — 模块③ 客户研判（核心）

**Sprint 目标**：输入机构名→画像+切入点+风险 InsightCard。

| ID | 任务 | 角色 | pt | 依赖 | 验收(AC) |
|---|---|---|---|---|---|
| P1-201 | `people_enrich`(Proxycurl) 适配器 + PII TTL 落库 | BE2 | 3 | P0-206 | 返回合规联系人；写 person.pii_ttl |
| P1-202 | `kb_org_profiles` 建库 + 机构资料写入/复用 | FS/ML | 2 | P0-205 | 二次研判命中历史资料 |
| P1-203 | ③ Team(采集Agent+研判Agent+风险Agent) 编排 | BE1 | 3 | P0-302 | 三 Agent 协作产出统一 Insight |
| P1-204 | `ProfileVerdict` schema(profile/business_focus/entry_points/risks/fit_score) | BE1 | 1 | 203 | schema 校验通过 |
| P1-205 | 风险 Agent：制裁/母公司/负面舆情初筛(公开源) | FS/ML | 2 | 203 | 输出 risk_flags + 证据 |
| P1-206 | 置信度<0.6→进接管队列(needs_human) 规则 | BE2 | 1 | P0-303 | 低置信项自动进队列 |
| P1-207 | 前端 M3 研判页：输入→步骤条→画像卡(画像/切入点/风险/联系人) | FE | 3 | P0-107 | 端到端展示一机构研判 |
| P1-208 | ③ 评估集(≥10 机构)+人工评估打分表 | FS/ML | 2 | 204 | 通过率基线报告 |
| P1-209 | 概览页接入真实指标(待接管/今日洞察/监控源) | FE | 2 | P0-208 | 指标来自真实数据 |

**Sprint DoD**：真实机构名→带证据链画像/切入点/风险；低置信正确进接管。合计 ~19 pt。

---

## Sprint 1.3 — 串联 ③↔⑤ + 接管闭环 + 联系人

**Sprint 目标**：③→⑤ 一键串联；接管队列反馈闭环生效。

| ID | 任务 | 角色 | pt | 依赖 | 验收(AC) |
|---|---|---|---|---|---|
| P1-301 | ③卡片"查合规准入⑤"：按 org.country/模式触发⑤并回填 | BE1 | 3 | P1-104,203 | 一键从研判跳出该国准入清单 |
| P1-302 | ⑤结果关联到③机构(`insight.linked_org`) + 双向展示 | BE2 | 2 | 301 | 机构页同时见研判与准入 |
| P1-303 | 接管队列：③低置信复核→采纳/修正/补证→写回 learnings | FS/ML | 2 | P0-304 | 修正后结论更新，反馈落库 |
| P1-304 | 联系人在③卡片展示(🟢来源角标 + PII 到期提示) | FE | 2 | P1-201 | 联系人可见且标注合规 |
| P1-305 | 机构详情页(org)：聚合研判/准入/联系人/证据 | FE | 3 | 302 | 单页看全一个机构 |
| P1-306 | 串联链路 e2e 测试(机构→研判→准入) | BE2 | 2 | 301 | 自动化用例通过 |
| P1-307 | 演示数据集 + Demo 脚本(场景 A 的③⑤片段) | FS/ML | 2 | 全部 | 一键跑通演示 |
| P1-308 | 错误态/空态/长任务流式反馈打磨 | FE | 2 | P1-207 | 无白屏；步骤可见 |

**Sprint DoD**：③→⑤ 串联无缝；接管修正写回并生效；机构详情页聚合完整。合计 ~18 pt。

---

## Sprint 1.4 — MVP 硬化与对外演示（Exit）

**Sprint 目标**：达到 P1 出口标准，可对外演示。

| ID | 任务 | 角色 | pt | 依赖 | 验收(AC) |
|---|---|---|---|---|---|
| P1-401 | 性能：研判/准入 ≤60s(缓存 + 并发抓取 + 检索调优) | BE1/BE2 | 3 | P1.2,1.1 | p50 达标；超时降级提示 |
| P1-402 | 证据齐全率强校验(无证据不展示/标警告) | FS/ML | 2 | P1-204 | 100% 有证据方展示 |
| P1-403 | 评估回归：③⑤ 通过率≥约定阈值(如80%) | FS/ML | 3 | P1-107,208 | 回归报告达标 |
| P1-404 | 鉴权/权限收口 + 高风险动作二次确认 | FE/BE1 | 2 | P0-108 | 登录态 + 基本 RBAC |
| P1-405 | 可观测：traces 采样 + 基础告警 + 成本埋点 | BE1 | 2 | P0-307 | 一次研判可看完整 trace |
| P1-406 | 通知：⑤监管变更订阅触发→飞书/邮件 | BE2 | 2 | P1-108,P0-207 | 变更→收到通知 |
| P1-407 | Demo 演练 + 演示脚本/话术 + 录屏 | 全员 | 2 | P1-307 | 现场可复现 |
| P1-408 | Bug 修复缓冲 + 文档(用户指南片段) | 全员 | 3 | — | P0 遗留+P1 缺陷清零 |

**Sprint DoD（=P1 Exit Gate / MVP 达标）**：
- 真实数据：机构名→≤60s 画像+切入点+风险(带证据)；国家+模式→四类准入清单(可溯源)。
- ③↔⑤ 串联；低置信进接管且反馈生效；证据齐全率 100%；评估通过率达阈值。
- 满足 Issue MVP："≥2 模块端到端 + 真实数据"，并含"Agent 自动运转(cron 订阅)"。合计 ~19 pt。

---

## 关键依赖 / 排期风险

| 项 | 影响 Sprint | 缓解 |
|---|---|---|
| Agno 2.0 API 确认 | P0-101(先做) | Sprint0.1 首日 spike 定版 |
| Firecrawl/Proxycurl 账号与额度 | P0-201/P1-201 | P0 期间开通并压测配额 |
| 目标国监管站可访问/结构差异 | P1-101 | 先选 2–3 个结构清晰国家；适配器化 |
| GLiNER2 抽取质量 | P0-203/P1 | LLM 兜底 + 评估集校准 |
| 评估阈值达成 | P1-403 | 提示词/RAG 迭代预留 P1-408 缓冲 |

## 跨 Sprint 约定（Definition of Done 通用项）
- 每任务：单测/集成测覆盖关键路径；PR 过 CI；更新对应文档。
- 每 Sprint 末：可运行 Demo + 增量回归 + 评估快照 + 风险复盘。
- 合规：新增数据源必须过合规网关 + 分级标注 + 审计；PII 落 TTL。
