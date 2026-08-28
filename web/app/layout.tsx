import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "市场智能情报与获客平台",
  description: "AI 驱动的市场情报与获客平台",
};

const NAV: { href: string; label: string; risk?: boolean }[] = [
  { href: "/", label: "🏠 今日概览" },
  { href: "/m1", label: "📡 行业情报" },
  { href: "/m2", label: "📑 招标监控", risk: true },
  { href: "/m3", label: "🏢 客户研判" },
  { href: "/m4", label: "🎤 峰会商机" },
  { href: "/m5", label: "🛡 合规准入" },
  { href: "/m6", label: "🔗 智能获客", risk: true },
  { href: "/review", label: "✅ 接管队列" },
  { href: "/settings", label: "⚙️ 设置" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="app">
          <aside className="sidebar">
            <div className="brand">市场情报 · 获客平台</div>
            <nav>
              {NAV.map((n) => (
                <Link key={n.href} href={n.href} className="nav-item">
                  {n.label}
                  {n.risk && <span className="risk-dot" title="高风险模块（默认合规子集）">🔴</span>}
                </Link>
              ))}
            </nav>
          </aside>
          <main className="content">{children}</main>
        </div>
      </body>
    </html>
  );
}
