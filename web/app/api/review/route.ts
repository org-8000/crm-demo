import { NextResponse } from "next/server";
import { agentosHeaders, agentosUrl } from "@/lib/api";
import { SAMPLE_INSIGHTS } from "@/lib/sample";

// BFF：接管队列 → AgentOS GET /review（后端不可达时回退示例）
export async function GET() {
  try {
    const res = await fetch(agentosUrl("/review"), {
      headers: agentosHeaders(),
      cache: "no-store",
    });
    if (res.ok) return NextResponse.json(await res.json());
    return NextResponse.json({ error: `AgentOS ${res.status}` }, { status: res.status });
  } catch {
    const fallback = SAMPLE_INSIGHTS.filter((i) => i.needs_human && i.status === "new");
    return NextResponse.json(fallback, { headers: { "x-data-source": "sample-fallback" } });
  }
}
