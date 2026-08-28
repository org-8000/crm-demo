// 仅在服务端（BFF 路由处理器）使用：读取后端地址与密钥，代理到 AgentOS。
// 不要在客户端组件里导入本模块（含服务端环境变量）。
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
