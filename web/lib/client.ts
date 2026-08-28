// 浏览器端 API：调用同源 /api/*（由 BFF 代理到 AgentOS）
import type { Insight } from "./types";

export interface RunResult {
  insight: Insight & { id?: number };
  steps: string[];
  linked_country?: string | null;
  error?: string;
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.error || `请求失败：${res.status}`);
  return data as T;
}

export function assessCompliance(country: string, business_mode: string) {
  return postJson<RunResult>("/api/compliance", { country, business_mode });
}

export function researchProfile(input: {
  name: string;
  homepage_url: string;
  country?: string;
  business_mode?: string;
}) {
  return postJson<RunResult>("/api/profile", input);
}

export async function getReview(): Promise<Insight[]> {
  const res = await fetch("/api/review", { cache: "no-store" });
  if (!res.ok) throw new Error(`加载接管队列失败：${res.status}`);
  return res.json();
}

export function postReview(id: number, action: string, note?: string) {
  return postJson<{ insight: Insight; feedback_recorded: boolean }>(
    `/api/review/${id}`,
    { action, note },
  );
}

export async function getInsights(module?: string): Promise<Insight[]> {
  const qs = module ? `?module=${encodeURIComponent(module)}` : "";
  const res = await fetch(`/api/insights${qs}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`加载洞察失败：${res.status}`);
  return res.json();
}
