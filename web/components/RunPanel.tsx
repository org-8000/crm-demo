"use client";

import { useState } from "react";
import { assessCompliance, researchProfile, type RunResult } from "@/lib/client";
import { InsightCard } from "@/components/InsightCard";

// 步骤条：展示 Agent 运行过程（对应后端返回的 steps / Agno traces）
function Steps({ steps, done }: { steps: string[]; done: boolean }) {
  return (
    <ol className="steps">
      {steps.map((s, i) => (
        <li key={i} className={done ? "step done" : "step"}>
          {done ? "✓" : "▸"} {s}
        </li>
      ))}
    </ol>
  );
}

export function RunPanel({ mode }: { mode: "m3" | "m5" }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RunResult | null>(null);

  // M5 表单
  const [country, setCountry] = useState("Singapore");
  const [businessMode, setBusinessMode] = useState("cross-border acquiring");
  // M3 表单
  const [name, setName] = useState("Acme Payments");
  const [homepage, setHomepage] = useState("https://example.com");

  async function run() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res =
        mode === "m5"
          ? await assessCompliance(country, businessMode)
          : await researchProfile({ name, homepage_url: homepage, country, business_mode: businessMode });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="run-panel">
      <div className="run-form">
        {mode === "m3" && (
          <>
            <label>机构名称<input value={name} onChange={(e) => setName(e.target.value)} /></label>
            <label>主页 URL<input value={homepage} onChange={(e) => setHomepage(e.target.value)} /></label>
          </>
        )}
        <label>国家<input value={country} onChange={(e) => setCountry(e.target.value)} /></label>
        <label>业务模式<input value={businessMode} onChange={(e) => setBusinessMode(e.target.value)} /></label>
        <button type="button" onClick={run} disabled={loading}>
          {loading ? "运行中…" : mode === "m5" ? "生成准入清单" : "开始研判"}
        </button>
      </div>

      {error && <p className="error">⚠ {error}</p>}

      {result && (
        <>
          <Steps steps={result.steps} done={!loading} />
          {result.linked_country && (
            <p className="hint">串联提示：可对「{result.linked_country}」运行合规准入 ⑤</p>
          )}
          <InsightCard insight={result.insight} />
        </>
      )}
    </div>
  );
}
