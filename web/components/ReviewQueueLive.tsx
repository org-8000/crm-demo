"use client";

import { useEffect, useState } from "react";
import { getReview, postReview } from "@/lib/client";
import type { Insight } from "@/lib/types";
import { MODULE_LABELS } from "@/lib/types";

export function ReviewQueueLive() {
  const [items, setItems] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      setItems(await getReview());
    } catch (e) {
      setMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function act(id: number | undefined, action: string) {
    if (id == null) return;
    try {
      await postReview(id, action, `${action} via UI`);
      setMsg(`#${id} 已${action}`);
      setItems((prev) => prev.filter((i) => i.id !== id));
    } catch (e) {
      setMsg(e instanceof Error ? e.message : String(e));
    }
  }

  if (loading) return <p>加载中…</p>;

  return (
    <div>
      {msg && <p className="hint">{msg}</p>}
      {items.length === 0 ? (
        <p className="empty">暂无待接管事项 🎉</p>
      ) : (
        <ul className="review-queue">
          {items.map((ins) => (
            <li key={ins.id} className="review-item">
              <div className="review-item__meta">
                <span className="tag">{MODULE_LABELS[ins.module]}</span>
                <span>{ins.subject}</span>
                <span className="conf">置信 {ins.confidence.toFixed(2)}</span>
              </div>
              <div className="review-item__actions">
                <button type="button" onClick={() => act(ins.id, "approve")}>采纳</button>
                <button type="button" onClick={() => act(ins.id, "escalate")}>升级人工</button>
                <button type="button" onClick={() => act(ins.id, "reject")}>忽略</button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
