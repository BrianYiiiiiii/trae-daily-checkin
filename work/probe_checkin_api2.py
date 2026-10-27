# -*- coding: utf-8 -*-
"""探针 2：读 localStorage 缓存的积分状态 + 用 performance 资源时序找 API 域名。"""
import json
import sys

sys.path.insert(0, r"D:\workspace\10_PROJECTS\active\23-2026-10-25_trae-daily-checkin\src")
from trae_checkin import Cdp, solo_targets  # noqa: E402

JS = r"""
(() => {
  const out = {};
  // 1) 积分缓存（value 可能含余额，截断展示）
  const bk = Object.keys(localStorage).find(k => k.startsWith("trae-cn-credits-billing-status"));
  out.billingKey = bk || null;
  out.billingValue = bk ? (localStorage.getItem(bk) || "").slice(0, 600) : null;
  // 2) 最近的资源请求里找 API 域名（排除静态资源和埋点）
  const skip = [".js", ".css", ".png", ".svg", ".woff", "mcs.zijieapi", "sourcemap", "lf1-cdn", "sf1-cdn"];
  const urls = performance.getEntriesByType("resource")
    .map(e => e.name)
    .filter(u => u.startsWith("http") && !skip.some(s => u.includes(s)));
  out.apiUrls = [...new Set(urls)].slice(0, 40);
  return JSON.stringify(out);
})()
"""

targets = solo_targets()
if not targets:
    print("NO_TARGET")
    sys.exit(1)
cdp = Cdp(targets[0]["webSocketDebuggerUrl"], timeout=10)
print(json.dumps(json.loads(cdp.eval(JS) or "{}"), ensure_ascii=False, indent=2))
cdp.close()
