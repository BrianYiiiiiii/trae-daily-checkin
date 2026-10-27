# -*- coding: utf-8 -*-
"""探针 5：枚举渲染进程里的 IPC 桥 + 在已加载 JS 里搜签到相关端点/通道名。"""
import json
import sys

sys.path.insert(0, r"D:\workspace\10_PROJECTS\active\23-2026-10-25_trae-daily-checkin\src")
from trae_checkin import Cdp, solo_targets  # noqa: E402

JS = r"""
(async () => {
  const out = {};
  // 1) 全局对象里找桥
  out.bridges = Object.getOwnPropertyNames(window)
    .filter(k => /ipc|electron|bridge|trae|solo|invoke/i.test(k)).slice(0, 30);
  // 2) 在已加载的 JS 里搜端点/通道
  const jsUrls = [...new Set(performance.getEntriesByType("resource")
    .map(e => e.name).filter(u => u.endsWith(".js")))];
  const pathRe = /["'`]([\/\w.-]*(?:commercial|checkin|check_in|sign_in|billing|claim)[\/\w?&=.-]*)["'`]/gi;
  const chanRe = /["'`]([\w:.-]*(?:checkin|check-in|checkIn)[\w:.-]*)["'`]/g;
  const paths = new Set(), chans = new Set();
  for (const u of jsUrls.slice(0, 60)) {
    try {
      const t = await (await fetch(u)).text();
      let m;
      while ((m = pathRe.exec(t)) && paths.size < 60) paths.add(m[1]);
      while ((m = chanRe.exec(t)) && chans.size < 60) chans.add(m[1]);
    } catch (e) { /* 跨源或失败跳过 */ }
  }
  out.endpoints = [...paths].filter(s => s.length > 4 && s.length < 120);
  out.channels = [...chans].filter(s => s.length > 4 && s.length < 80);
  return JSON.stringify(out);
})()
"""

targets = solo_targets()
if not targets:
    print("NO_TARGET")
    sys.exit(1)
cdp = Cdp(targets[0]["webSocketDebuggerUrl"], timeout=60)
cdp.mid += 1
cdp.ws.send(json.dumps({"id": cdp.mid, "method": "Runtime.evaluate",
                        "params": {"expression": JS, "returnByValue": True, "awaitPromise": True}}))
cdp.ws.settimeout(120)
while True:
    msg = json.loads(cdp.ws.recv())
    if msg.get("id") == cdp.mid:
        val = msg["result"]["result"].get("value")
        print(json.dumps(json.loads(val or "{}"), ensure_ascii=False, indent=2))
        break
cdp.close()
