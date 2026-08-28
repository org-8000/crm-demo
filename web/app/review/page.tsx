import { ReviewQueue } from "@/components/ReviewQueue";
import { SAMPLE_INSIGHTS } from "@/lib/sample";

export default function ReviewPage() {
  return (
    <div>
      <h1>✅ 接管队列</h1>
      <p className="placeholder">全平台 HITL 汇总（P1 接 agno_approvals：批准/编辑/升级/反馈写回 learnings）。</p>
      <ReviewQueue items={SAMPLE_INSIGHTS} />
    </div>
  );
}
