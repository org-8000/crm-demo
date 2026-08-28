import type { Insight } from "./types";

// BFF 基础地址：前端调用自身 /api/*，由 Next 服务端代理到 AgentOS（注入 OS_SECURITY_KEY）
const AGENTOS_BASE_URL =
  process.env.AGENTOS_BASE_URL || "http://localhost:8000";
const OS_SECURITY_KEY = process.env.OS_SECURITY_KEY || "";

export function agentosHeaders(): HeadersInit {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (OS_SECURITY_KEY) h["Authorization"] = `Bearer ${OS_SECURITY_KEY}`;
  return h;
}

export function agentosUrl(path: string): string {
  return `${AGENTOS_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

// 客户端从 BFF 拉取洞察
export async function fetchInsights(module?: string): Promise<Insight[]> {
  const qs = module ? `?module=${encodeURIComponent(module)}` : "";
  const res = await fetch(`/api/insights${qs}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`加载洞察失败：${res.status}`);
  return res.json();
}
