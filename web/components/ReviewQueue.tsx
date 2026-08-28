import type { Insight } from "@/lib/types";
import { MODULE_LABELS } from "@/lib/types";

/**
 * 接管队列（Review Queue）：承载全平台 HITL。
 * 消费 needs_human 的 Insight（P0 骨架：展示 + 占位操作；P1 接 agno_approvals）。
 */
export function ReviewQueue({ items }: { items: Insight[] }) {
  const queue = items.filter((i) => i.needs_human && i.status === "new");

  if (queue.length === 0) {
    return <p className="empty">暂无待接管事项 🎉</p>;
  }

  return (
    <ul className="review-queue">
      {queue.map((ins, idx) => (
        <li key={ins.id ?? idx} className="review-item">
          <div className="review-item__meta">
            <span className="tag">{MODULE_LABELS[ins.module]}</span>
            <span>{ins.subject}</span>
            <span className="conf">置信 {ins.confidence.toFixed(2)}</span>
          </div>
          <div className="review-item__actions">
            {/* P1 接后端：批准/编辑/升级/拒绝 → agno_approvals */}
            <button type="button">采纳</button>
            <button type="button">修正</button>
            <button type="button">升级人工</button>
            <button type="button">忽略</button>
          </div>
        </li>
      ))}
    </ul>
  );
}
