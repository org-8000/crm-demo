import type { Insight } from "./types";

// P0 骨架用示例数据（离线可渲染）。P1 起由 AgentOS 经 BFF 提供真实数据。
export const SAMPLE_INSIGHTS: Insight[] = [
  {
    id: 1,
    module: "M3",
    subject: "Acme Payments（新加坡）",
    verdict: {
      profile: "跨境收单 + 钱包服务商",
      business_focus: ["跨境收单", "电子钱包"],
      entry_points: ["正申请 MPI 牌照", "缺 ISO20022 报文能力"],
      risks: ["母公司涉某制裁关联（待核）"],
      fit_score: 0.82,
    },
    confidence: 0.82,
    risk_flags: [],
    evidence: [
      { source_url: "https://example.com/acme", source_type: "web", snippet: "官网业务介绍", fetched_at: "2026-08-28T00:00:00Z" },
      { source_url: "https://mas.gov.sg/notice", source_type: "regulator", snippet: "MAS 公告", fetched_at: "2026-08-28T00:00:00Z" },
    ],
    needs_human: false,
    status: "new",
    created_at: "2026-08-28T08:00:00Z",
  },
  {
    id: 2,
    module: "M5",
    subject: "印尼 / 跨境收单",
    verdict: {
      licenses: ["Bank Indonesia PJP 牌照"],
      messaging_standards: ["ISO 20022", "本地 NPG"],
      data_compliance: ["数据本地化（PP71）"],
      business_restrictions: ["外资持股上限"],
      readiness_summary: "中等，主要卡点=数据本地化",
    },
    confidence: 0.76,
    risk_flags: [],
    evidence: [
      { source_url: "https://bi.go.id/reg", source_type: "regulator", snippet: "BI 监管条款", fetched_at: "2026-08-28T00:00:00Z" },
    ],
    needs_human: false,
    status: "new",
    created_at: "2026-08-28T08:05:00Z",
  },
  {
    id: 3,
    module: "M2",
    subject: "某银行拟启动跨境支付系统招标",
    verdict: { tender_org: "某银行", scope: "跨境支付系统", deadline: "2026-09-15", amount: "USD 2,000,000" },
    confidence: 0.55,
    risk_flags: ["yellow: social 公开信号"],
    evidence: [
      { source_url: "https://twitter.com/x/status/1", source_type: "social", snippet: "公开动态提及招标", fetched_at: "2026-08-28T00:00:00Z" },
    ],
    needs_human: true,
    status: "new",
    created_at: "2026-08-28T09:00:00Z",
  },
];
