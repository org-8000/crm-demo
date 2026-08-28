-- 市场智能情报与获客平台 — 业务表 DDL v1
-- Agno 系统表（agno_sessions/agno_approvals/agno_schedules/...）由 AgentOS 首次启动自动建。
-- 本文件只建业务表；与 agno_* 同库（PostgreSQL + pgvector）。

CREATE EXTENSION IF NOT EXISTS vector;

-- 机构/客户（③④⑥ 共用）
CREATE TABLE IF NOT EXISTS org (
  id             BIGSERIAL PRIMARY KEY,
  name           TEXT NOT NULL,
  country        TEXT,
  domain         TEXT,
  business_lines TEXT[],
  created_at     TIMESTAMPTZ DEFAULT now(),
  UNIQUE (name, country)
);

-- 联系人（③④⑥，PII，受合规约束）
CREATE TABLE IF NOT EXISTS person (
  id           BIGSERIAL PRIMARY KEY,
  org_id       BIGINT REFERENCES org(id) ON DELETE CASCADE,
  full_name    TEXT,
  title        TEXT,
  linkedin_url TEXT,
  pii_ttl      TIMESTAMPTZ,          -- 到期自动清理
  legal_basis  TEXT,                 -- 合规依据
  created_at   TIMESTAMPTZ DEFAULT now()
);

-- 被监控源（①② 共用：大V账号/媒体/群聊）
CREATE TABLE IF NOT EXISTS watch_source (
  id               BIGSERIAL PRIMARY KEY,
  module           TEXT,             -- M1|M2
  source_type      TEXT,             -- twitter|linkedin|rss|group|regulator
  handle_or_url    TEXT,
  enabled          BOOLEAN DEFAULT true,
  compliance_level TEXT,             -- green|yellow|red
  created_at       TIMESTAMPTZ DEFAULT now()
);

-- 统一洞察产出（六模块共用，前端统一渲染）
CREATE TABLE IF NOT EXISTS insight (
  id          BIGSERIAL PRIMARY KEY,
  module      TEXT NOT NULL,         -- M1..M6
  subject     TEXT,
  verdict     JSONB,                 -- 各模块结构化判断
  confidence  REAL,
  risk_flags  TEXT[],
  evidence    JSONB,                 -- Evidence[]
  needs_human BOOLEAN DEFAULT false,
  status      TEXT DEFAULT 'new',    -- new|reviewed|actioned|dismissed
  linked_org_id BIGINT REFERENCES org(id) ON DELETE SET NULL,
  created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_insight_module_status ON insight (module, status, created_at DESC);

-- 采集审计（合规）
CREATE TABLE IF NOT EXISTS ingestion_log (
  id          BIGSERIAL PRIMARY KEY,
  source_url  TEXT,
  source_type TEXT,
  legal_basis TEXT,
  fetched_at  TIMESTAMPTZ DEFAULT now()
);

-- 知识库向量块（pgvector；Agno Knowledge 亦可托管其元数据）
CREATE TABLE IF NOT EXISTS kb_chunk (
  id         BIGSERIAL PRIMARY KEY,
  kb_name    TEXT,                   -- kb_payment_ontology|kb_org_profiles|kb_sources
  content    TEXT,
  embedding  VECTOR(1536),
  source_ref JSONB
);
CREATE INDEX IF NOT EXISTS idx_kb_chunk_embedding ON kb_chunk USING hnsw (embedding vector_cosine_ops);
