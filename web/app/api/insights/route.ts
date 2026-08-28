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
    // 上游返回错误（如 401/500）：透传状态，不用示例数据掩盖问题
    return NextResponse.json(
      { error: `AgentOS 返回 ${res.status}` },
      { status: res.status },
    );
  } catch {
    // 后端不可达（网络错误）：P0 骨架回退到示例数据以便前端可渲染
    const data = module
      ? SAMPLE_INSIGHTS.filter((i) => i.module === module)
      : SAMPLE_INSIGHTS;
    return NextResponse.json(data, { headers: { "x-data-source": "sample-fallback" } });
  }
}
