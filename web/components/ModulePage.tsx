import { InsightCard } from "@/components/InsightCard";
import type { ModuleId } from "@/lib/types";
import { MODULE_LABELS, HIGH_RISK_MODULES } from "@/lib/types";
import { SAMPLE_INSIGHTS } from "@/lib/sample";

// 模块页通用骨架：按 module 过滤展示 InsightCard；P1 起接入各模块输入面板与真实数据。
export function ModulePage({ module, hint }: { module: ModuleId; hint?: string }) {
  const items = SAMPLE_INSIGHTS.filter((i) => i.module === module);
  const highRisk = HIGH_RISK_MODULES.includes(module);
  return (
    <div>
      <h1>
        {MODULE_LABELS[module]}（{module}）{highRisk && <span title="高风险模块，默认合规子集"> 🔴</span>}
      </h1>
      {highRisk && (
        <p className="placeholder">
          ⚠ 高风险模块：默认仅运行合规子集（自动发送 / 群聊监控需管理员开启 feature flag 并经法务放行）。
        </p>
      )}
      {hint && <p className="placeholder">{hint}</p>}
      <div className="insight-grid">
        {items.length > 0 ? (
          items.map((ins) => <InsightCard key={ins.id} insight={ins} />)
        ) : (
          <p className="placeholder">暂无洞察（示例数据）。P1 起接入真实数据。</p>
        )}
      </div>
    </div>
  );
}
