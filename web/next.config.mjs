/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 注意：不要在此 inline AGENTOS_BASE_URL / OS_SECURITY_KEY。
  // 它们是"服务端运行时"变量，由 BFF 路由处理器在运行时读取 process.env，
  // 放进 next.config 的 env 会在 build 期固化，导致运行时改环境变量无效。
};

export default nextConfig;
