#!/usr/bin/env bash
# ビューア用のローカルサーバー。ブラウザで http://localhost:8000/viewer/ を開く。
cd "$(dirname "$0")/.."
exec python3 -m http.server 8000 --bind 127.0.0.1
