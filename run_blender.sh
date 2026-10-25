#!/usr/bin/env bash
# WSLからWindows版Blenderをバックグラウンドで実行し、Pythonスクリプトを流すヘルパー
# 使い方: ./run_blender.sh scripts/xxx.py [スクリプトへ渡す引数...]
set -euo pipefail

BLENDER_EXE="${BLENDER_EXE:-/mnt/c/Users/kouta/AppData/Local/Programs/Blender Foundation/Blender 5.2/blender.exe}"   # 2.92 も "/mnt/c/Program Files/Blender Foundation/Blender 2.92/blender.exe" に残してある
ROOT="$(cd "$(dirname "$0")" && pwd)"

script="${1:?usage: $0 script.py [args...]}"
shift || true

# Windows側プロセスにはWindowsパスを渡す
win_script="$(wslpath -w "$(realpath "$script")")"
export WORKSPACE_WIN="$(wslpath -w "$ROOT")"
export WSLENV="${WSLENV:+$WSLENV:}WORKSPACE_WIN"  # Windows側プロセスへ環境変数を渡す

"$BLENDER_EXE" --background --factory-startup --python "$win_script" -- "$@"
