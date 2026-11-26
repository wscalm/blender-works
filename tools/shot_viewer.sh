#!/usr/bin/env bash
# ヘッドレス Edge (Windows) でビューアのスクリーンショットを撮る。tools/serve.sh を起動しておくこと。
# 使い方: tools/shot_viewer.sh "look=west&pos=3.8,1.8" renders/viewer_west.png
#   SIZE=1600,900 のように画面サイズを変えられる (既定 1280,800)。既定は GPU 描画、GPU=0 でソフトウェア描画 (swiftshader)
#   (swiftshader は斜めから見た大きな面を真っ黒に描くことがある。ユーザーのブラウザと同じ GPU 描画で確かめる)
#   クエリ: look=north|east|south|west  pos=X,Y[,高さ] (部屋の座標 m)  at=X,Y,Z (その点を向く)  pitch=度  hfov=度  mode=orbit  probe=ノード名  debug
#   ?debug を付けたときは、画面左上の表示 (probe の結果など) も端末に出す
#   "https://..." を渡すと、そのページを撮る (モニターの画面に映すウェブページ。読み込み完了だけ待つ)
# Edge を DevTools Protocol (tools/cdp_shot.py を Windows 側の Python で実行) で操作し、glb の読み込みが終わるまで待ってから撮る。
# URL の最後に &_=時刻 を付ける (同じクエリだと、書き換える前の index.html をキャッシュから出すことがあった)。
set -euo pipefail
query="${1:-}"; out="${2:?usage: $0 \"query\" out.png}"
EDGE="${EDGE:-/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe}"
WIN_PYTHON="${WIN_PYTHON:-/mnt/c/Users/kouta/AppData/Local/Programs/Python/Python311/python.exe}"
PORT="${PORT:-9223}"
IFS=, read -r w h <<< "${SIZE:-1280,800}"
if [ "${GPU:-1}" = 1 ]; then render=(--use-angle=d3d11 --enable-gpu); else render=(--use-angle=swiftshader --enable-unsafe-swiftshader); fi

win_temp="$(cd /mnt/c && cmd.exe /c 'echo %TEMP%' 2>/dev/null | tr -d '\r')"
work="$(wslpath "$win_temp")/claude-edge-shot"; mkdir -p "$work"
cp "$(dirname "$0")/cdp_shot.py" "$work/cdp_shot.py"
(cd /mnt/c && timeout 120 "$EDGE" --headless=new --user-data-dir="$win_temp\\claude-edge-shot\\profile" \
  "${render[@]}" --ignore-gpu-blocklist --hide-scrollbars --window-size="$w,$h" \
  --remote-debugging-port="$PORT" about:blank >/dev/null 2>&1) &
edge=$!
case "$query" in http*) url="$query" ;; *) url="http://localhost:8000/viewer/?$query&_=$(date +%s%N)" ;; esac
(cd /mnt/c && timeout 100 "$WIN_PYTHON" "$win_temp\\claude-edge-shot\\cdp_shot.py" "$PORT" \
  "$url" "$win_temp\\claude-edge-shot\\shot.png" "$w" "$h") | tr -d '\r'
wait "$edge" || true
cp "$work/shot.png" "$out"
echo "WROTE: $out"
