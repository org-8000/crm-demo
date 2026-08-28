import { ReviewQueueLive } from "@/components/ReviewQueueLive";

export default function ReviewPage() {
  return (
    <div>
      <h1>✅ 接管队列</h1>
      <p className="placeholder">
        全平台 HITL 汇总（实时读取后端 /review；采纳/升级/忽略写回状态。后端未启动时显示示例回退）。
      </p>
      <ReviewQueueLive />
    </div>
  );
}
