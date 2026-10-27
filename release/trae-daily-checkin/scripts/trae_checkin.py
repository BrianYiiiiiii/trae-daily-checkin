# -*- coding: utf-8 -*-
"""
Trae CN daily check-in via Chrome DevTools Protocol (CDP).

Requires Trae to be running with --remote-debugging-port (see work/Start-TraeWithDebug.ps1).
Prints a single-line JSON result on stdout and appends to logs/checkin.log.
"""
import json
import os
import subprocess
import sys
import time
from datetime import date, datetime, timedelta

import requests
import websocket
from windows_toasts import Toast, ToastAudio, WindowsToaster

PORT = int(os.environ.get("TRAE_CDP_PORT", "9222"))
TRAE_EXE = os.environ.get("TRAE_EXE", r"D:\Applications\Trae\Trae CN.exe")
# 计划任务用 pythonw（无控制台）运行；调用 tasklist 等控制台程序时必须加
# CREATE_NO_WINDOW，否则 Windows 会为其分配新控制台 → 屏幕闪黑框。
CREATE_NO_WINDOW = 0x08000000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
LOG_FILE = os.path.join(ROOT_DIR, "logs", "checkin.log")
DATA_DIR = os.path.join(ROOT_DIR, "data")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
REPORT_FILE = os.path.join(DATA_DIR, "签到日报.md")
WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
SCHEDULE_TEXT = "00:05 / 09:05 / 12:30 / 15:30 / 19:00"

# Dispatches a full pointer+mouse event sequence (plain .click() is ignored by the UI).
DISPATCH_FUNC = r"""
function __traeClick(el) {
  const r = el.getBoundingClientRect();
  const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
  const opts = {bubbles: true, cancelable: true, composed: true, clientX: cx, clientY: cy,
                button: 0, pointerId: 1, pointerType: "mouse", isPrimary: true, view: window};
  el.dispatchEvent(new PointerEvent("pointerover", opts));
  el.dispatchEvent(new MouseEvent("mouseover", opts));
  el.dispatchEvent(new PointerEvent("pointerdown", opts));
  el.dispatchEvent(new MouseEvent("mousedown", opts));
  el.dispatchEvent(new PointerEvent("pointerup", opts));
  el.dispatchEvent(new MouseEvent("mouseup", opts));
  el.dispatchEvent(new MouseEvent("click", opts));
}
"""

# Ensure the account popover is open; returns {open, label, usage}
ENSURE_PANEL_JS = DISPATCH_FUNC + r"""
(() => {
  const read = () => {
    const pop = document.querySelector('div[class*="popover-"][class*="visible"]');
    if (!pop) return null;
    const btn = pop.querySelector('button[class*="accountCheckinButton"]');
    const usage = pop.querySelector('button[class*="accountUsage"]');
    return {
      open: true,
      label: btn ? (btn.textContent || "").trim() : null,
      usage: usage ? (usage.textContent || "").trim() : null,
    };
  };
  const cur = read();
  if (cur) return JSON.stringify(cur);
  // 直接点按钮本身：外层 div.sc-* 的中心点可能落在按钮外（窗口尺寸变化后会失效）
  const target = document.querySelector('button[class*="accountTrigger"]')
              || document.querySelector('span[class*="accountTriggerName"]');
  if (!target) return JSON.stringify({open: false, why: "no_trigger"});
  __traeClick(target);
  return JSON.stringify({open: false, why: "trigger_clicked"});
})()
"""

CLICK_CHECKIN_JS = DISPATCH_FUNC + r"""
(() => {
  const pop = document.querySelector('div[class*="popover-"][class*="visible"]');
  if (!pop) return JSON.stringify({ok: false, why: "no_popover"});
  const btn = pop.querySelector('button[class*="accountCheckinButton"]');
  if (!btn) return JSON.stringify({ok: false, why: "no_button"});
  const label = (btn.textContent || "").trim();
  if (label === "已签到") return JSON.stringify({ok: true, did: "already"});
  __traeClick(btn);
  return JSON.stringify({ok: true, did: "clicked", before: label});
})()
"""

STATE_JS = r"""
(() => {
  const pop = document.querySelector('div[class*="popover-"][class*="visible"]');
  if (!pop) return JSON.stringify({open: false});
  const btn = pop.querySelector('button[class*="accountCheckinButton"]');
  const usage = pop.querySelector('button[class*="accountUsage"]');
  return JSON.stringify({open: true,
    label: btn ? (btn.textContent || "").trim() : null,
    usage: usage ? (usage.textContent || "").trim() : null});
})()
"""

CLOSE_PANEL_JS = DISPATCH_FUNC + r"""
(() => {
  const pop = document.querySelector('div[class*="popover-"][class*="visible"]');
  if (!pop) return JSON.stringify({closed: true, already: true});
  const btn = document.querySelector('button[class*="accountTrigger"]');
  if (btn) { __traeClick(btn); return JSON.stringify({closed: true}); }
  return JSON.stringify({closed: false, why: "no_trigger"});
})()
"""

# 在 Trae 界面内右下角弹一条提示：配色取 VS Code 主题变量，浅色/深色主题都贴合
NOTIFY_JS = r"""
(() => {
  const MSG = __MSG__;
  const ID = "__trae_checkin_toast";
  document.getElementById(ID)?.remove();
  const card = document.createElement("div");
  card.id = ID;
  card.style.cssText = [
    "position:fixed", "right:14px", "bottom:30px", "z-index:99999",
    "display:flex", "align-items:flex-start", "gap:9px",
    "max-width:340px", "padding:10px 14px",
    "background:var(--vscode-notifications-background,#252526)",
    "color:var(--vscode-notifications-foreground,#ccc)",
    "border:1px solid var(--vscode-editorWidget-border,#454545)",
    "border-radius:4px", "font-size:13px", "line-height:1.5", "white-space:pre-line",
    "font-family:system-ui,-apple-system,'Segoe UI',sans-serif",
    "box-shadow:0 4px 14px rgba(0,0,0,0.28)",
    "pointer-events:none", "opacity:0", "transition:opacity .25s ease"
  ].join(";");
  const icon = document.createElement("span");
  icon.textContent = "\u2713";
  icon.style.cssText = "color:#2ea043;font-weight:700;flex:0 0 auto;";
  const text = document.createElement("span");
  text.textContent = MSG;
  card.appendChild(icon);
  card.appendChild(text);
  document.body.appendChild(card);
  requestAnimationFrame(() => { card.style.opacity = "1"; });
  setTimeout(() => {
    card.style.opacity = "0";
    setTimeout(() => card.remove(), 400);
  }, 8000);
  return "shown";
})()
"""


def log(msg):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")


def cdp_available():
    try:
        return requests.get(f"http://localhost:{PORT}/json/version", timeout=2).status_code == 200
    except Exception:
        return False


def ensure_cdp(auto_start=True):
    if cdp_available():
        return True, "already_running"
    if not auto_start:
        return False, "cdp_unavailable"
    # Use tasklist (not powershell.exe) per workspace rule: never invoke PS 5.1.
    proc = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Trae CN.exe", "/NH"],
                          capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
    if "Trae CN.exe" in proc.stdout:
        return False, "running_without_cdp"
    subprocess.Popen([TRAE_EXE, f"--remote-debugging-port={PORT}"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + 90
    while time.time() < deadline:
        time.sleep(3)
        if cdp_available():
            return True, "started"
    return False, "start_timeout"


class Cdp:
    def __init__(self, ws_url, timeout=10):
        self.ws = websocket.create_connection(ws_url, timeout=timeout, suppress_origin=True)
        self.mid = 0

    def eval(self, expr):
        self.mid += 1
        self.ws.send(json.dumps({"id": self.mid, "method": "Runtime.evaluate",
                                 "params": {"expression": expr, "returnByValue": True}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.mid:
                return msg["result"]["result"].get("value")

    def close(self):
        self.ws.close()


def solo_targets():
    targets = requests.get(f"http://localhost:{PORT}/json/list", timeout=5).json()
    return [t for t in targets
            if t.get("type") in ("page", "webview")
            and "solo-lite" in (t.get("url") or "")
            and t.get("webSocketDebuggerUrl")]


def do_checkin(max_rounds=4, interval=5):
    last = {}
    for attempt in range(1, max_rounds + 1):
        for t in solo_targets():
            cdp = None
            opened_by_us = False
            result = None
            try:
                cdp = Cdp(t["webSocketDebuggerUrl"])
                raw = cdp.eval(ENSURE_PANEL_JS)
                st = json.loads(raw or "{}")
                if st.get("why") == "trigger_clicked":
                    opened_by_us = True
                    time.sleep(1.0)  # wait for popover animation/render
                    st = json.loads(cdp.eval(STATE_JS) or "{}")
                if not st.get("open"):
                    last = st
                    continue
                if st.get("label") == "已签到":
                    result = {"status": "already", "usage": st.get("usage")}
                else:
                    click = json.loads(cdp.eval(CLICK_CHECKIN_JS) or "{}")
                    if not click.get("ok"):
                        last = click
                        continue
                    if click.get("did") == "already":
                        result = {"status": "already", "usage": st.get("usage")}
                    else:
                        time.sleep(3)
                        after = json.loads(cdp.eval(STATE_JS) or "{}")
                        if after.get("label") == "已签到":
                            usage = after.get("usage") or ""
                            before_n = parse_num(st.get("usage"))
                            after_n = parse_num(usage)
                            gained = (after_n - before_n) if (before_n is not None
                                                              and after_n is not None) else None
                            result = {"status": "success", "usage": usage, "gained": gained}
                        else:
                            last = {"why": "clicked_unverified", "after": after}
            except Exception:
                continue
            finally:
                if cdp:
                    if opened_by_us:
                        try:
                            cdp.eval(CLOSE_PANEL_JS)  # 只关自己打开的面板
                        except Exception:
                            pass
                    cdp.close()
            if result:
                return result
        if attempt < max_rounds:
            time.sleep(interval)
    return {"status": "panel_not_found", "detail": last}


def parse_num(text):
    try:
        return int(str(text).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


# 通过 Trae 内部 RPC（__SOLO_LITE_PORT_REGISTRY__ 的 CheckinCreditsPort）直接领取，
# 不走任何 UI。claim() 幂等：当天重复调用无副作用，返回 undefined。
API_CLAIM_JS = r"""
(async () => {
  const reg = window.__SOLO_LITE_PORT_REGISTRY__;
  if (!reg || !reg.instances) return JSON.stringify({ok: false, why: "no_registry"});
  let inst = null;
  for (const [k, v] of reg.instances) {
    if (/checkin/i.test(String(k))) { inst = v; break; }
  }
  if (!inst || typeof inst.claim !== "function")
    return JSON.stringify({ok: false, why: "no_port"});
  try {
    await inst.claim();
    return JSON.stringify({ok: true});
  } catch (e) {
    return JSON.stringify({ok: false, why: "claim_throw", detail: String(e).slice(0, 200)});
  }
})()
"""


def api_claim():
    """零界面领取：调 CheckinCreditsPort.claim()。返回 True=已调用成功。"""
    for t in solo_targets():
        cdp = None
        try:
            cdp = Cdp(t["webSocketDebuggerUrl"])
            cdp.mid += 1
            cdp.ws.send(json.dumps({"id": cdp.mid, "method": "Runtime.evaluate",
                                    "params": {"expression": API_CLAIM_JS,
                                               "returnByValue": True, "awaitPromise": True}}))
            cdp.ws.settimeout(20)
            while True:
                msg = json.loads(cdp.ws.recv())
                if msg.get("id") == cdp.mid:
                    r = json.loads(msg["result"]["result"].get("value") or "{}")
                    return r.get("ok") is True
        except Exception:
            continue
        finally:
            if cdp:
                try:
                    cdp.close()
                except Exception:
                    pass
    return False


def today_checked():
    """今天的 history 记录已存在且 checked=true（当日首次 UI 流程已跑过）。"""
    today = date.today().isoformat()
    rec = next((e for e in load_history() if e.get("date") == today), None)
    return bool(rec and rec.get("checked"))


def load_history():
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def save_history(hist):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)


def streak_days(hist):
    checked = {e.get("date") for e in hist if e.get("checked")}
    n, d = 0, date.today()
    while d.isoformat() in checked:
        n += 1
        d -= timedelta(days=1)
    return n


def prepend_report(entry):
    """把当天报告插到日报最前面（最新的在最上面）。"""
    os.makedirs(DATA_DIR, exist_ok=True)
    header = "# Trae 每日签到日报\n\n"
    try:
        with open(REPORT_FILE, encoding="utf-8") as f:
            old = f.read()
    except FileNotFoundError:
        old = header
    if not old.startswith("# "):
        old = header + old
    title, _, body = old.partition("\n\n")
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(title + "\n\n" + entry + "\n\n" + body)


def record_and_report(result):
    """写入 history 与日报，每天只汇报一次。返回要弹在 Trae 里的文案（或 None）。"""
    status = result.get("status")
    if status not in ("success", "already"):
        return None
    today = date.today().isoformat()
    hist = load_history()
    rec = next((e for e in hist if e.get("date") == today), None)
    if rec is None:
        rec = {"date": today}
        hist.append(rec)
    usage = result.get("usage") or ""
    rec.update({"status": status, "usage": usage, "gained": result.get("gained"),
                "checked": True, "time": datetime.now().strftime("%H:%M")})
    streak = streak_days(hist)
    rec["streak"] = streak
    if rec.get("reported"):
        save_history(hist)
        return None
    rec["reported"] = True
    save_history(hist)

    now = datetime.now()
    head = f"## {WEEKDAYS[now.weekday()]} {now.month}月{now.day}日 {now.strftime('%H:%M')}"
    if status == "success":
        gained = result.get("gained")
        gain_txt = f"+{gained}" if gained else "+积分"
        line = f"Trae 签到成功：{gain_txt} 积分，连续第 {streak} 天，当前余额 {usage}。"
        tip = f"签到成功  {gain_txt}\n当前积分 {usage} · 连续 {streak} 天"
    else:
        line = f"今日已签到（无需重复领取），连续第 {streak} 天，当前余额 {usage}。"
        tip = f"今日已签到\n当前积分 {usage} · 连续 {streak} 天"
    prepend_report(f"{head}\n\n{line}\n\n下次自动尝试：{SCHEDULE_TEXT}")
    return tip


def emit(line):
    log(line)
    if sys.stdout:  # pythonw 下 sys.stdout 为 None
        print(line)


def trae_process_running():
    proc = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Trae CN.exe", "/NH"],
                          capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
    return "Trae CN.exe" in proc.stdout


def wait_for_trae(minutes):
    """有界等待：每 20 秒探一次，最多等 minutes 分钟。

    返回 (ok, how)。Trae 已在运行但无调试端口时立即返回，不再空等。
    """
    deadline = time.time() + minutes * 60
    while time.time() < deadline:
        if cdp_available():
            return True, "already_running"
        if trae_process_running():
            return False, "running_without_cdp"
        time.sleep(20)
    return False, "not_running"


def ping(text):
    """在 Trae 界面内弹一条提示（尽力而为，失败不影响主流程）。"""
    try:
        for t in solo_targets():
            cdp = Cdp(t["webSocketDebuggerUrl"])
            try:
                cdp.eval(NOTIFY_JS.replace("__MSG__", json.dumps(text, ensure_ascii=False)))
            finally:
                cdp.close()
            return True
    except Exception:
        return False
    return False


def notify_windows(text):
    """发一条静音的 Windows 系统通知气泡（尽力而为，失败不影响主流程）。"""
    try:
        lines = text.split("\n")
        title = lines[0] if lines else "Trae 签到"
        body = "\n".join(lines[1:]).strip()
        fields = [title] + ([body] if body else [])
        toast = Toast(text_fields=fields)
        toast.audio = ToastAudio(silent=True)
        WindowsToaster("Trae 签到").show_toast(toast)
        return True
    except Exception:
        return False


def main():
    auto_start = "--no-auto-start" not in sys.argv
    wait_min = 0
    if "--wait" in sys.argv:
        try:
            wait_min = int(sys.argv[sys.argv.index("--wait") + 1])
        except (IndexError, ValueError):
            wait_min = 0

    if wait_min > 0:
        ok, how = wait_for_trae(wait_min)
        if ok is False:
            emit(json.dumps({"status": how, "how": how}, ensure_ascii=False))
            return
    else:
        ok, how = ensure_cdp(auto_start=auto_start)
        if not ok:
            emit(json.dumps({"status": how, "how": how}, ensure_ascii=False))
            return

    if how == "started":
        time.sleep(15)  # 冷启动后等界面渲染

    # 混合模式：当天已有记录（首次 UI 流程已跑过）→ 走零界面 API 领取；
    # API 失败（Trae 改版等）自动退回 UI 流程。
    if today_checked():
        if api_claim():
            emit(json.dumps({"status": "already", "how": "api_claim"}, ensure_ascii=False))
            return
        log("api_claim failed, fallback to UI flow")

    result = do_checkin()
    result["how"] = how
    emit(json.dumps(result, ensure_ascii=False))
    tip = record_and_report(result)
    if tip:
        ping(tip)
        notify_windows(tip)
    elif result.get("status") not in ("success", "already"):
        ping("Trae 签到未完成，请手动看一眼（日志：checkin.log）")


if __name__ == "__main__":
    main()
