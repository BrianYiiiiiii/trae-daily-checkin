# -*- coding: utf-8 -*-
"""探针 6：检查 __SOLO_LITE_PORT_REGISTRY__ 与 CheckinCreditsPort 的方法。只读，不调用。"""
import json
import sys

sys.path.insert(0, r"D:\workspace\10_PROJECTS\active\23-2026-10-25_trae-daily-checkin\src")
from trae_checkin import Cdp, solo_targets  # noqa: E402

JS = r"""
(() => {
  const out = {};
  const reg = window.__SOLO_LITE_PORT_REGISTRY__;
  out.registryType = typeof reg;
  if (reg) {
    out.registryKeys = Object.getOwnPropertyNames(reg).slice(0, 20);
    // 常见形态：Map / 对象 / 带 get 方法
    if (typeof reg.get === "function") {
      try {
        const port = reg.get("CheckinCreditsPort") || reg.get("checkinCredits");
        out.portType = typeof port;
        if (port) {
          const proto = Object.getPrototypeOf(port) || {};
          out.portMethods = [...new Set([
            ...Object.getOwnPropertyNames(port),
            ...Object.getOwnPropertyNames(proto)
          ])].filter(k => typeof port[k] === "function" && k !== "constructor");
        }
      } catch (e) { out.err = String(e); }
    } else {
      // 对象形态：列出 key
      out.shape = Object.keys(reg).slice(0, 40);
      const p = reg.CheckinCreditsPort || reg.checkinCredits;
      if (p) {
        const proto = Object.getPrototypeOf(p) || {};
        out.portMethods = [...new Set([
          ...Object.getOwnPropertyNames(p),
          ...Object.getOwnPropertyNames(proto)
        ])].filter(k => typeof p[k] === "function" && k !== "constructor");
      }
    }
  }
  return JSON.stringify(out);
})()
"""

targets = solo_targets()
if not targets:
    print("NO_TARGET")
    sys.exit(1)
cdp = Cdp(targets[0]["webSocketDebuggerUrl"], timeout=10)
print(cdp.eval(JS))
cdp.close()
