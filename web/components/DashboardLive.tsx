"use client";

import { useEffect, useState } from "react";
import { getInsights } from "@/lib/client";
import type { Insight } from "@/lib/types";
import { InsightCard } from "@/components/InsightCard";
import { SAMPLE_INSIGHTS } from "@/lib/sample";

export function DashboardLive() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [source, setSource] = useState<"live" | "sample">("sample");

  useEffect(() => {
    getInsights()
      .then((data) => {
        // 后端有数据用真实数据，否则回退示例便于观感
        if (Array.isArray(data) && data.length > 0) {
          setInsights(data);
          setSource("live");
        } else {
          setInsights(SAMPLE_INSIGHTS);
        }
      })
      .catch(() => setInsights(SAMPLE_INSIGHTS));
  }, []);

  const pending = insights.filter((i) => i.needs_human && i.status === "new").length;
  const highIntent = insights.filter((i) => i.module === "M6").length;
  const top = insights.filter((i) => i.module === "M1").length;

  return (
    <div>
      <p className="hint">数据源：{source === "live" ? "后端实时" : "示例回退（后端无数据/未启动）"}</p>
      <section className="metrics">
        <div className="metric"><b>{pending}</b><span>待接管</span></div>
        <div className="metric"><b>{insights.length}</b><span>洞察总数</span></div>
        <div className="metric"><b>{highIntent}</b><span>高意向线索</span></div>
        <div className="metric"><b>{top}</b><span>行业情报</span></div>
      </section>

      <h2>最近洞察流</h2>
      <div className="insight-grid">
        {insights.map((ins, i) => (
          <InsightCard key={ins.id ?? i} insight={ins} />
        ))}
      </div>
    </div>
  );
}
