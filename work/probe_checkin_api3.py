# -*- coding: utf-8 -*-
"""探针 3：开面板时抓 commercial/credit/checkin 相关请求及响应体。"""
import json
import sys
import time

sys.path.insert(0, r"D:\workspace\10_PROJECTS\active\23-2026-10-25_trae-daily-checkin\src")
from trae_checkin import Cdp, solo_targets, ENSURE_PANEL_JS, CLOSE_PANEL_JS  # noqa: E402

KEYWORDS = ("commercial", "credit", "checkin", "check_in", "sign", "billing")
SKIP = (".js", ".css", ".png", ".svg", ".woff", "mcs.zijieapi", "starling",
        "abtestvm", "sourcemap", "cdn")


def mask_headers(h):
    return {k: (v[:6] + "..." + v[-4:] if isinstance(v, str) and len(v) > 16 else v)
            for k, v in h.items()}


def main():
    targets = solo_targets()
    if not targets:
        print("NO_TARGET")
        return
    cdp = Cdp(targets[0]["webSocketDebuggerUrl"], timeout=15)
    cdp.mid += 1
    cdp.ws.send(json.dumps({"id": cdp.mid, "method": "Network.enable", "params": {}}))

    # 确保面板从关闭状态开始，再打开
    print("close:", cdp.eval(CLOSE_PANEL_JS))
    time.sleep(1)
    print("open1:", cdp.eval(ENSURE_PANEL_JS))
    time.sleep(1.5)
    print("open2:", cdp.eval(ENSURE_PANEL_JS))

    cdp.ws.settimeout(10)
    hits = {}
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            msg = json.loads(cdp.ws.recv())
        except Exception:
            break
        m = msg.get("method")
        p = msg.get("params", {})
        if m == "Network.requestWillBeSent":
            r = p["request"]
            u = r["url"].lower()
            if u.startswith("http") and not any(s in u for s in SKIP):
                hits[p["requestId"]] = {
                    "url": r["url"], "method": r["method"],
                    "headers": mask_headers(r.get("headers", {})),
                    "postData": (r.get("postData") or "")[:300],
                }
        elif m == "Network.responseReceived":
            rid = p["requestId"]
            if rid in hits:
                hits[rid]["status"] = p["response"]["status"]

    # 取响应体
    cdp.ws.settimeout(5)
    for rid, info in hits.items():
        cdp.mid += 1
        cdp.ws.send(json.dumps({"id": cdp.mid, "method": "Network.getResponseBody",
                                "params": {"requestId": rid}}))
        try:
            while True:
                msg = json.loads(cdp.ws.recv())
                if msg.get("id") == cdp.mid:
                    body = msg.get("result", {}).get("body", "")
                    info["body"] = body[:400]
                    break
        except Exception:
            info["body"] = "<timeout>"

    print(json.dumps(list(hits.values()), ensure_ascii=False, indent=2))
    try:
        cdp.eval(CLOSE_PANEL_JS)
    except Exception:
        pass
    cdp.close()


if __name__ == "__main__":
    main()
