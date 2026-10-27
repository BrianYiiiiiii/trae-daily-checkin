# -*- coding: utf-8 -*-
"""探针 11：看 CheckinCredits/Commercial 相关 implementation（非 Proxy 实现类）的方法名，找余额只读接口。"""
import json
import sys

sys.path.insert(0, r"D:\workspace\10_PROJECTS\active\23-2026-10-25_trae-daily-checkin\src")
from trae_checkin import Cdp, solo_targets  # noqa: E402

JS = r"""
(() => {
  const reg = window.__SOLO_LITE_PORT_REGISTRY__;
  const out = {};
  for (const [k, impl] of reg.implementations) {
    const s = String(k).replace(/^Symbol\(|\)$/g, "");
    if (!/checkin|commercial|credit|usage|account/i.test(s)) continue;
    const info = {implType: typeof impl};
    if (impl && typeof impl === "object") {
      // implementation 可能是类（构造函数）或工厂
      const proto = impl.prototype || Object.getPrototypeOf(impl) || {};
      info.implMethods = [...new Set([
        ...Object.getOwnPropertyNames(impl),
        ...Object.getOwnPropertyNames(proto),
      ])].filter(n => n !== "constructor" && !n.startsWith("_")).slice(0, 40);
      if (typeof impl === "function") info.isClass = true;
    }
    out[s] = info;
  }
  // window 上找 store
  out.stores = Object.getOwnPropertyNames(window).filter(k => /store|commercial/i.test(k)).slice(0, 20);
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
