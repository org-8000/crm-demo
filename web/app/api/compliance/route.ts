import { NextResponse } from "next/server";
import { agentosHeaders, agentosUrl } from "@/lib/api";

// BFF：⑤ 合规准入 → AgentOS POST /m5/assess
export async function POST(request: Request) {
  const body = await request.json();
  try {
    const res = await fetch(agentosUrl("/m5/assess"), {
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
