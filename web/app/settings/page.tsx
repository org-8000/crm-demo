export default function SettingsPage() {
  return (
    <div>
      <h1>⚙️ 设置</h1>
      <p className="placeholder">
        源管理（watch_source）/ ICP 规则 / 合规开关（feature flags）/ 团队与权限。P1+ 逐步接入。
      </p>
      <ul>
        <li>ENABLE_M2_GROUP_MONITOR：②群聊/私域招标监控（默认关闭 🔴）</li>
        <li>ENABLE_M6_AUTOSEND：⑥LinkedIn 自动发送（默认关闭 🔴）</li>
        <li>ENABLE_SOCIAL_DEEP_SCRAPE：①②深度社媒抓取（默认关闭 🟡）</li>
      </ul>
    </div>
  );
}
