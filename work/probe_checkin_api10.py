# -*- coding: utf-8 -*-
"""探针 10：枚举全部 port 实例名 + 找余额查询方法。只读。"""
import json
import sys

sys.path.insert(0, r"D:\workspace\10_PROJECTS\active\23-2026-10-25_trae-daily-checkin\src")
from trae_checkin import Cdp, solo_targets  # noqa: E402

JS = r"""
(async () => {
  const reg = window.__SOLO_LITE_PORT_REGISTRY__;
  const names = [];
  const targets = [];
  for (const [k, v] of reg.instances) {
    const s = String(k);  // Symbol(xxx) -> "Symbol(xxx)"
    names.push(s.replace(/^Symbol\(|\)$/g, ""));
    if (/commercial|usage|credit|account|user/i.test(s)) targets.push([s, v]);
  }
  const out = {all: names, probes: {}};
  const candidates = ["status", "getStatus", "usage", "getUsage", "getSessionUsage",
                      "fetchUsage", "refresh", "query", "info", "getInfo", "balance",
                      "getBalance", "claim", "history", "getHistory"];
  for (const [s, inst] of targets) {
    const found = {};
    for (const n of candidates) {
      try { if (typeof inst[n] === "function") found[n] = 1; } catch (e) {}
    }
    out.probes[s.replace(/^Symbol\(|\)$/g, "")] = Object.keys(found);
  }
  return JSON.stringify(out);
})()
"""

targets = solo_targets()
if not targets:
    print("NO_TARGET")
    sys.exit(1)
cdp = Cdp(targets[0]["webSocketDebuggerUrl"], timeout=20)
cdp.mid += 1
cdp.ws.send(json.dumps({"id": cdp.mid, "method": "Runtime.evaluate",
                        "params": {"expression": JS, "returnByValue": True, "awaitPromise": True}}))
cdp.ws.settimeout(30)
while True:
    msg = json.loads(cdp.ws.recv())
    if msg.get("id") == cdp.mid:
        print(json.dumps(json.loads(msg["result"]["result"].get("value") or "{}"),
                         ensure_ascii=False, indent=2))
        break
cdp.close()
