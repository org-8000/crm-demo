import { NextResponse } from "next/server";
import { agentosHeaders, agentosUrl } from "@/lib/api";

// BFF：接管处理 → AgentOS POST /insights/{id}/review
export async function POST(
  request: Request,
  { params }: { params: { id: string } },
) {
  const body = await request.json();
  try {
    const res = await fetch(agentosUrl(`/insights/${params.id}/review`), {
      method: "POST",
      headers: agentosHeaders(),
      body: JSON.stringify(body),
      cache: "no-store",
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json(
      { error: "AgentOS 不可达，请确认后端(:8000)已启动" },
      { status: 502 },
    );
  }
}
