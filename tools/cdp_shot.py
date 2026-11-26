"""ヘッドレス Edge を DevTools Protocol で操作して、ビューアのスクショを撮る (tools/shot_viewer.sh から呼ぶ)。

**Windows 側の Python** で動かす (WSL からは Windows の 127.0.0.1 の DevTools に届かないため)。標準ライブラリだけで書いてある。
    python cdp_shot.py <port> <url> <out.png> <幅> <高さ>
ページの読み込みが終わる (body[data-ready]、または "load failed" が出る) まで実時間で待ってから撮り、最後に Edge を閉じる。
ビューア以外のページ (モニターの画面に映すウェブページ) は document の読み込み完了だけを待つ。
(Edge の --screenshot + --virtual-time-budget は、glb に埋め込んだテクスチャの読み込みを待たずに撮ってしまう)
"""
import base64
import json
import os
import socket
import struct
import sys
import time
import urllib.request

LOAD_TIMEOUT = 60   # 秒
SETTLE = 1.5        # 読み込み後、視線のなめらかな追従と仕上げ処理が落ち着くまで待つ秒数


class WS:
    """最小限の WebSocket クライアント (テキストフレームの送受信だけ)"""

    def __init__(self, url):
        hostport, path = url[len("ws://"):].split("/", 1)
        host, port = hostport.split(":")
        self.s = socket.create_connection((host, int(port)))
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET /{path} HTTP/1.1\r\nHost: {hostport}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        self.rest = buf.split(b"\r\n\r\n", 1)[1]

    def _read(self, n):
        while len(self.rest) < n:
            chunk = self.s.recv(1 << 20)
            if not chunk:
                raise EOFError
            self.rest += chunk
        out, self.rest = self.rest[:n], self.rest[n:]
        return out

    def send(self, text):
        data = text.encode()
        hdr = bytearray([0x81])
        n = len(data)
        if n < 126:
            hdr.append(0x80 | n)
        elif n < 65536:
            hdr.append(0x80 | 126); hdr += struct.pack(">H", n)
        else:
            hdr.append(0x80 | 127); hdr += struct.pack(">Q", n)
        mask = os.urandom(4)
        self.s.sendall(bytes(hdr) + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self):
        msg = b""
        while True:
            b0, b1 = self._read(2)
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            payload = self._read(n)
            if b0 & 0x0F in (0x0, 0x1, 0x2):   # ping/pong/close は無視
                msg += payload
                if b0 & 0x80:
                    return msg.decode("utf-8", "replace")


class CDP:
    def __init__(self, ws_url):
        self.ws = WS(ws_url)
        self.i = 0

    def call(self, method, **params):
        self.i += 1
        self.ws.send(json.dumps({"id": self.i, "method": method, "params": params}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get("id") == self.i:
                if "error" in m:
                    raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result", {})

    def eval(self, js):
        return self.call("Runtime.evaluate", expression=js, returnByValue=True).get("result", {}).get("value")


def get_json(port, path, timeout=30):
    """Edge が起動して DevTools が応答するまで待つ"""
    end = time.time() + timeout
    while True:
        try:
            return json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=2))
        except OSError:
            if time.time() > end:
                raise
            time.sleep(0.3)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Windows の既定 (cp932) だと日本語の表示で落ちることがある
    port, url, out, w, h = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
    browser = CDP(get_json(port, "/json/version")["webSocketDebuggerUrl"])
    try:
        page = CDP([t for t in get_json(port, "/json") if t["type"] == "page"][0]["webSocketDebuggerUrl"])
        page.call("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=False)
        page.call("Page.navigate", url=url)
        end = time.time() + LOAD_TIMEOUT
        state = None
        viewer = "/viewer/" in url
        while time.time() < end:
            time.sleep(0.5)
            if not viewer:
                state = page.eval("document.readyState === 'complete' && 'ready'")
            else:
                state = page.eval("document.readyState === 'complete' && (document.body.dataset.ready ? 'ready'"
                                  " : /load failed/.test(document.getElementById('status')?.textContent) ? 'failed' : false)")
            if state:
                break
        if state != "ready":
            print(f"WARNING: page not ready ({state or 'timeout'})")
        time.sleep(SETTLE)
        status = page.eval("document.getElementById('status')?.textContent || ''")
        if status:
            print(status.rstrip())
        data = page.call("Page.captureScreenshot", format="png")["data"]
        with open(out, "wb") as f:
            f.write(base64.b64decode(data))
    finally:
        browser.ws.send(json.dumps({"id": 0, "method": "Browser.close"}))


main()
