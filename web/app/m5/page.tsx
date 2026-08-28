import { RunPanel } from "@/components/RunPanel";

export default function Page() {
  return (
    <div>
      <h1>🛡 合规准入（M5）</h1>
      <p className="placeholder">输入目标国家 + 业务模式 → 准入清单（牌照/报文/数据/限制，附监管原文证据）。种子含 Singapore / Indonesia。</p>
      <RunPanel mode="m5" />
    </div>
  );
}
