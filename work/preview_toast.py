"""一次性预览签到卡片样式：复用 src/trae_checkin.py 的 NOTIFY_JS，仅把停留时长改成 10 秒。

不触发签到、不写 history.json、不写 checkin.log、不改 reported 标记。
用法：D:\\Python311\\python.exe work\\preview_toast.py
"""
import json
import os
import sys

import requests
import websocket

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.insert(0, SRC)
from trae_checkin import NOTIFY_JS, notify_windows  # noqa: E402

TEXT = "签到成功  +100\n当前积分 3,787 · 连续 2 天"
PREVIEW_JS = (
    NOTIFY_JS
    .replace("__MSG__", json.dumps(TEXT, ensure_ascii=False))
    .replace("}, 8000);", "}, 10000);")
)

# 同时发一路 Windows 系统气泡（与真实签到后行为一致）
notify_windows(TEXT)

targets = requests.get("http://localhost:9222/json/list", timeout=5).json()
solo = [t for t in targets
        if t.get("type") in ("page", "webview") and "solo-lite" in (t.get("url") or "")]
print(f"solo-lite targets: {len(solo)}")
for t in solo:
    ws = websocket.create_connection(t["webSocketDebuggerUrl"], timeout=10, suppress_origin=True)
    try:
        ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                            "params": {"expression": PREVIEW_JS, "returnByValue": True}}))
        while True:
            m = json.loads(ws.recv())
            if m.get("id") == 1:
                print("->", m["result"]["result"].get("value"), "@", (t.get("url") or "")[:80])
                break
    finally:
        ws.close()
