import type { ComplianceLevel, Insight } from "@/lib/types";
import { MODULE_LABELS } from "@/lib/types";

// 置信度点阵（●○），5 格
function ConfidenceDots({ value }: { value: number }) {
  const filled = Math.round(value * 5);
  return (
    <span title={`置信度 ${value.toFixed(2)}`} aria-label={`置信度 ${value.toFixed(2)}`}>
      {"●".repeat(filled)}
      {"○".repeat(5 - filled)} {value.toFixed(2)}
    </span>
  );
}

const COMPLIANCE_BADGE: Record<ComplianceLevel, { icon: string; label: string }> = {
  green: { icon: "🟢", label: "合规" },
  yellow: { icon: "🟡", label: "中风险" },
  red: { icon: "🔴", label: "高风险" },
};

// 从 risk_flags 粗略推断展示用合规角标（默认绿色）
function complianceOf(ins: Insight): ComplianceLevel {
  if (ins.risk_flags.some((f) => /red|group|linkedin|高风险/i.test(f))) return "red";
  if (ins.risk_flags.some((f) => /yellow|social|中风险/i.test(f))) return "yellow";
  return "green";
}

/**
 * 统一洞察卡片：六模块通用。
 * 靠 module + verdict 渲染差异，与后端统一 Insight 模型一一对应。
 */
export function InsightCard({ insight }: { insight: Insight }) {
  const level = complianceOf(insight);
  const badge = COMPLIANCE_BADGE[level];
  const lowConf = insight.confidence < 0.6;

  return (
    <article
      className="insight-card"
      style={{ borderColor: lowConf ? "#e0a800" : "#ddd" }}
    >
      <header className="insight-card__head">
        <span className="tag">{MODULE_LABELS[insight.module]}（{insight.module}）</span>
        <span title={badge.label}>{badge.icon} {badge.label}</span>
        <span className="conf"><ConfidenceDots value={insight.confidence} /></span>
      </header>

      <h3 className="insight-card__subject">{insight.subject}</h3>

      <section className="insight-card__verdict">
        {Object.entries(insight.verdict).map(([k, v]) => (
          <div key={k} className="verdict-row">
            <span className="verdict-key">{k}</span>
            <span className="verdict-val">{renderValue(v)}</span>
          </div>
        ))}
      </section>

      {insight.risk_flags.length > 0 && (
        <p className="insight-card__risk">⚠ {insight.risk_flags.join("、")}</p>
      )}

      <section className="insight-card__evidence">
        <strong>证据链：</strong>
        {insight.evidence.map((e, i) => (
          <details key={i} className="evidence">
            <summary>[{e.source_type}]</summary>
            <div className="evidence__body">
              <a href={e.source_url} target="_blank" rel="noreferrer">{e.source_url}</a>
              <p>{e.snippet}</p>
            </div>
          </details>
        ))}
      </section>

      <footer className="insight-card__actions">
        {insight.needs_human && <span className="needs-human">需人工复核</span>}
        <span className="status">状态：{insight.status}</span>
      </footer>
    </article>
  );
}

function renderValue(v: unknown): string {
  if (v == null) return "-";
  if (Array.isArray(v)) return v.map((x) => renderValue(x)).join("；");
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}
