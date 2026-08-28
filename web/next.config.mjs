/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // AgentOS 后端地址（BFF 通过此变量代理，前端不直连 LLM）
  env: {
    AGENTOS_BASE_URL: process.env.AGENTOS_BASE_URL || "http://localhost:8000",
  },
};

export default nextConfig;
