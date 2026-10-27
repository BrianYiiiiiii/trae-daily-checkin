# -*- coding: utf-8 -*-
"""探针 7：深入 registry 结构，找 CheckinCreditsPort 实例与方法。只读。"""
import json
import sys

sys.path.insert(0, r"D:\workspace\10_PROJECTS\active\23-2026-10-25_trae-daily-checkin\src")
from trae_checkin import Cdp, solo_targets  # noqa: E402

JS = r"""
(() => {
  const reg = window.__SOLO_LITE_PORT_REGISTRY__;
  const out = {};
  const dump = (o, depth) => {
    if (o == null) return String(o);
    if (o instanceof Map) return {__map: [...o.keys()].slice(0, 50)};
    if (o instanceof Set) return {__set: [...o].slice(0, 50)};
    if (Array.isArray(o)) return {__arr: o.length};
    if (typeof o === "object") {
      if (depth <= 0) return "{...}";
      const r = {};
      for (const k of Object.keys(o).slice(0, 50)) r[k] = dump(o[k], depth - 1);
      return r;
    }
    return typeof o === "string" ? o.slice(0, 60) : typeof o;
  };
  out.ports = dump(reg.ports, 1);
  out.implementations = dump(reg.implementations, 1);
  out.instances = dump(reg.instances, 1);
  // instances 里若有 checkin 相关的，列出方法名
  const find = (o) => {
    if (o instanceof Map) {
      for (const [k, v] of o) if (/checkin/i.test(String(k))) return [k, v];
    } else if (o && typeof o === "object") {
      for (const k of Object.keys(o)) if (/checkin/i.test(k)) return [k, o[k]];
    }
    return null;
  };
  for (const [name, cont] of [["ports", reg.ports], ["implementations", reg.implementations], ["instances", reg.instances]]) {
    const hit = find(cont);
    if (hit) {
      const [k, inst] = hit;
      const proto = Object.getPrototypeOf(inst) || {};
      out["found_in_" + name] = {
        key: String(k),
        methods: [...new Set([...Object.getOwnPropertyNames(inst), ...Object.getOwnPropertyNames(proto)])]
          .filter(n => typeof inst[n] === "function" && n !== "constructor"),
      };
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
print(json.dumps(json.loads(cdp.eval(JS) or "{}"), ensure_ascii=False, indent=2))
cdp.close()
