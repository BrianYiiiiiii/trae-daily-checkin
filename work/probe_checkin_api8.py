# -*- coding: utf-8 -*-
"""探针 8：探测 CheckinCreditsPort 实例（疑似 Proxy）可访问的方法名，并只读调用 status。不调用 claim。"""
import json
import sys

sys.path.insert(0, r"D:\workspace\10_PROJECTS\active\23-2026-10-25_trae-daily-checkin\src")
from trae_checkin import Cdp, solo_targets  # noqa: E402

JS = r"""
(async () => {
  const reg = window.__SOLO_LITE_PORT_REGISTRY__;
  let inst = null;
  for (const [k, v] of reg.instances) {
    if (/checkin/i.test(String(k))) { inst = v; break; }
  }
  if (!inst) return JSON.stringify({err: "no instance"});
  const out = {};
  const names = ["status", "getStatus", "checkStatus", "getCheckinStatus",
                 "claim", "doClaim", "checkin", "doCheckin", "sign"];
  out.props = {};
  for (const n of names) {
    try { out.props[n] = typeof inst[n]; } catch (e) { out.props[n] = "throw"; }
  }
  // 只读调用 status 类方法
  for (const n of ["status", "getStatus", "checkStatus", "getCheckinStatus"]) {
    if (typeof inst[n] === "function") {
      try {
        const r = await inst[n]();
        out.statusResult = {method: n, value: JSON.stringify(r).slice(0, 500)};
        break;
      } catch (e) { out.statusResult = {method: n, error: String(e).slice(0, 200)}; }
    }
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
