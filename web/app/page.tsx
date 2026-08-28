import { InsightCard } from "@/components/InsightCard";
import { ReviewQueue } from "@/components/ReviewQueue";
import { SAMPLE_INSIGHTS } from "@/lib/sample";

// 今日概览（P0 骨架：用示例数据渲染 InsightCard + ReviewQueue）
export default function DashboardPage() {
  const insights = SAMPLE_INSIGHTS;
  const pending = insights.filter((i) => i.needs_human && i.status === "new").length;
  const todayTop = insights.filter((i) => i.module === "M1").length;
  const highIntent = insights.filter((i) => i.module === "M6").length;

  return (
    <div>
      <h1>今日概览</h1>

      <section className="metrics">
        <div className="metric"><b>{pending}</b><span>待接管</span></div>
        <div className="metric"><b>{insights.length}</b><span>今日新洞察</span></div>
        <div className="metric"><b>{highIntent}</b><span>高意向线索</span></div>
        <div className="metric"><b>{todayTop}</b><span>行业 Top3</span></div>
      </section>

      <h2>🔥 需要你接管</h2>
      <ReviewQueue items={insights} />

      <h2>最近洞察流</h2>
      <div className="insight-grid">
        {insights.map((ins) => (
          <InsightCard key={ins.id} insight={ins} />
        ))}
      </div>
    </div>
  );
}
