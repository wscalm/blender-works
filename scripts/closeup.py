"""家具の近くから見た確認画像を撮る (renders/closeup_<名前>.png)。

    ./run_blender.sh scripts/closeup.py

標準の視点 (views.py) では形が細かく見えないときに使う。下の VIEWS を確認したい場所に書き換えて実行し、
画像を Read で見たら `rm renders/closeup_*.png` で消す。.blend / .glb は書き換えない。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from build_all import build_scene

# (名前, カメラの位置 (x, y, z), 見る先 (x, y, z), 焦点距離 mm)  座標は部屋の座標 (m)。壁は消さないので、部屋の中に置くこと
VIEWS = [
    ("desk", (2.63, 0.92, 1.15), (2.75, 0.3, 0.9), 22),          # 椅子の目線: メインの画面・デスク2の小物・PC の上
    ("lshelf", (2.9, 1.9, 1.1), (3.9, 3.4, 0.5), 24),            # L字棚の中 (かご・炊飯器・薬)
    ("lshelf2", (3.5, 2.6, 0.9), (4.5, 3.0, 0.55), 26),          # L字棚2 (西向きの箱の中)
    ("table_sofa", (2.0, 1.4, 1.3), (3.0, 2.6, 0.35), 24),       # ローテーブルの小物・ソファーのクッション
    ("curtain_clock", (2.4, 1.0, 1.4), (4.7, 1.7, 1.5), 22),     # 半分開けたカーテン・時計・窓
    ("rail", (1.9, 1.2, 1.45), (1.9, 0.0, 1.5), 28),             # フックのレール
]

build_scene()
for name, location, target, lens in VIEWS:
    render_view(f"closeup_{name}.png", location, target, lens=lens, width=1000, height=700)
