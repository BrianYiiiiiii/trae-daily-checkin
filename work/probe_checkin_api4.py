# -*- coding: utf-8 -*-
"""探针 4：从页面上下文直接 fetch 余额接口，看渲染进程能否直连 API。"""
import json
import sys

sys.path.insert(0, r"D:\workspace\10_PROJECTS\active\23-2026-10-25_trae-daily-checkin\src")
from trae_checkin import Cdp, solo_targets  # noqa: E402

JS = r"""
(async () => {
  const url = "https://trae-api-cn.mchost.guru/api/v1/commercial/get_session_usage";
  try {
    const r = await fetch(url, {credentials: "include"});
    const text = await r.text();
    return JSON.stringify({status: r.status, body: text.slice(0, 400)});
  } catch (e) {
    return JSON.stringify({error: String(e)});
  }
})()
"""

targets = solo_targets()
if not targets:
    print("NO_TARGET")
    sys.exit(1)
cdp = Cdp(targets[0]["webSocketDebuggerUrl"], timeout=10)
# awaitPromise 需要直接用 Runtime.evaluate 的 awaitPromise 参数
cdp.mid += 1
cdp.ws.send(json.dumps({"id": cdp.mid, "method": "Runtime.evaluate",
                        "params": {"expression": JS, "returnByValue": True, "awaitPromise": True}}))
while True:
    msg = json.loads(cdp.ws.recv())
    if msg.get("id") == cdp.mid:
        print(msg["result"]["result"].get("value"))
        break
cdp.close()
