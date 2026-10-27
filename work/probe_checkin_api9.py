# -*- coding: utf-8 -*-
"""探针 9：调用 CheckinCreditsPort.claim()，今日已签到，预期返回幂等的"已领取"结果。"""
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
  try {
    const r = await inst.claim();
    let s;
    try { s = JSON.stringify(r); } catch (e) { s = String(r); }
    return JSON.stringify({ok: true, result: (s || "undefined").slice(0, 600)});
  } catch (e) {
    return JSON.stringify({ok: false, error: String(e).slice(0, 300)});
  }
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
        print(msg["result"]["result"].get("value"))
        break
cdp.close()
