# -*- coding: utf-8 -*-
"""一次性探针：通过 CDP Network 域抓取账号面板相关请求。
用法: python work\\probe_checkin_api.py
仅本地分析用，token 在输出中打码。
"""
import json
import sys
import time

sys.path.insert(0, r"D:\workspace\10_PROJECTS\active\23-2026-10-25_trae-daily-checkin\src")
from trae_checkin import Cdp, solo_targets, ENSURE_PANEL_JS, CLOSE_PANEL_JS  # noqa: E402


def mask(v):
    if not isinstance(v, str) or len(v) < 12:
        return v
    return v[:6] + "..." + v[-4:]


def main():
    targets = solo_targets()
    if not targets:
        print("NO_TARGET")
        return
    cdp = Cdp(targets[0]["webSocketDebuggerUrl"], timeout=15)

    # 1) 开 Network 监听
    cdp.mid += 1
    cdp.ws.send(json.dumps({"id": cdp.mid, "method": "Network.enable", "params": {}}))

    # 2) 看一下 localStorage 里有哪些 key（找 token 存放位置，不打印值）
    keys = cdp.eval("JSON.stringify(Object.keys(localStorage))")
    print("localStorage keys:", keys)

    # 3) 打开账号面板（触发余额/签到状态请求）
    raw = cdp.eval(ENSURE_PANEL_JS)
    print("panel:", raw)
    time.sleep(2)

    # 4) 收集 8 秒内的网络事件
    cdp.ws.settimeout(8)
    seen = {}
    deadline = time.time() + 8
    while time.time() < deadline:
        try:
            msg = json.loads(cdp.ws.recv())
        except Exception:
            break
        m = msg.get("method")
        if m == "Network.requestWillBeSent":
            r = msg["params"]["request"]
            rid = msg["params"]["requestId"]
            seen[rid] = {"url": r["url"], "method": r["method"],
                         "headers": {k: mask(v) for k, v in r.get("headers", {}).items()},
                         "postData": (r.get("postData") or "")[:200]}
        elif m == "Network.responseReceived":
            rid = msg["params"]["requestId"]
            if rid in seen:
                seen[rid]["status"] = msg["params"]["response"]["status"]

    # 5) 过滤出非静态资源请求
    interesting = [v for v in seen.values()
                   if not any(x in v["url"] for x in (".js", ".css", ".png", ".svg", ".woff", "sourcemap"))]
    print(json.dumps(interesting, ensure_ascii=False, indent=2))

    # 6) 收起面板
    try:
        cdp.eval(CLOSE_PANEL_JS)
    except Exception:
        pass
    cdp.close()


if __name__ == "__main__":
    main()
