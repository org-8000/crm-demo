// 与后端 core/models.py 对应的前端类型定义
export type ModuleId = "M1" | "M2" | "M3" | "M4" | "M5" | "M6";
export type ComplianceLevel = "green" | "yellow" | "red";
export type InsightStatus = "new" | "reviewed" | "actioned" | "dismissed";
export type SourceType =
  | "web"
  | "regulator"
  | "social"
  | "group"
  | "doc"
  | "linkedin"
  | "search";

export interface Evidence {
  source_url: string;
  source_type: SourceType;
  snippet: string;
  fetched_at: string;
}

export interface Insight {
  id?: number;
  module: ModuleId;
  subject: string;
  verdict: Record<string, unknown>;
  confidence: number;
  risk_flags: string[];
  evidence: Evidence[];
  needs_human: boolean;
  status: InsightStatus;
  linked_org_id?: number | null;
  created_at: string;
}

export const MODULE_LABELS: Record<ModuleId, string> = {
  M1: "行业情报",
  M2: "招标监控",
  M3: "客户研判",
  M4: "峰会商机",
  M5: "合规准入",
  M6: "智能获客",
};

// 高风险模块（默认合规子集）
export const HIGH_RISK_MODULES: ModuleId[] = ["M2", "M6"];
