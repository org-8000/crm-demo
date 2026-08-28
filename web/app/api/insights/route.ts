import { NextResponse } from "next/server";
import { agentosHeaders, agentosUrl } from "@/lib/api";
import { SAMPLE_INSIGHTS } from "@/lib/sample";

// BFF：代理 AgentOS 的洞察查询；后端不可用时回退到示例数据（P0 骨架）。
// 前端不直连 LLM/后端，统一经此路由并注入 OS_SECURITY_KEY。
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const module = searchParams.get("module");

  try {
    const qs = module ? `?module=${encodeURIComponent(module)}` : "";
    const res = await fetch(agentosUrl(`/insights${qs}`), {
      headers: agentosHeaders(),
      cache: "no-store",
    });
    if (res.ok) {
      return NextResponse.json(await res.json());
    }
  } catch {
    // 后端未就绪：回退示例数据
  }

  const data = module
    ? SAMPLE_INSIGHTS.filter((i) => i.module === module)
    : SAMPLE_INSIGHTS;
  return NextResponse.json(data);
}
