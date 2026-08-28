import { RunPanel } from "@/components/RunPanel";

export default function Page() {
  return (
    <div>
      <h1>🏢 客户研判（M3）</h1>
      <p className="placeholder">输入机构名与主页 → 画像 / 切入点 / 风险 / fit_score（低置信自动进接管队列）。</p>
      <RunPanel mode="m3" />
    </div>
  );
}
