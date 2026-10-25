"""テレビ (液晶、電源オフ。写真 reference/IMG_1100: 細い黒い枠の薄い画面、真ん中の台座、下の枠に赤い待機ランプ)。
テレビ台の L字棚2 の上に、西向き (ソファーの方) に置く。

大きさは仮に 32型 (画面の枠込みで 幅0.73 x 高さ0.43)。ユーザーの指定はまだ無い。
位置・大きさは layout.py (tv)。ローカル座標: 原点 = 足元の中心 / 正面 (画面) = -Y / 幅は X
構成: Empty `tv` の下に、本体 `tv_body` (薄い画面の板・背面のふくらみ・首・台座。黒)、画面 `tv_screen`、
下の枠の印 `tv_marks` (社名の代わりの銀の小さな帯と、待機中の赤いランプ。ランプは emission で光る)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from layout import FURNITURE

PANEL_H = 0.43      # 画面の板 (枠込み) の高さ
PANEL_T = 0.014     # 画面の板の厚み (縁の所)
BACK_T = 0.045      # 背面のふくらみ (電源・基板の入った所) の厚み
BEZEL = 0.008       # 画面のまわりの枠の幅 (下だけ太い)
BEZEL_BOTTOM = 0.02
BASE_T = 0.012      # 台座の厚み
BASE_W = 0.30       # 台座の幅
NECK_W = 0.07       # 台座と画面をつなぐ首の幅


def build_tv():
    e = FURNITURE["tv"]
    hx, hy, top = e["w"] / 2, e["d"] / 2, e["h"]
    root = add_empty("tv", (e["x"], e["y"], e["z0"]), FACING_DEG[e["facing"]])
    black = make_material("tv_body", "#18181A", roughness=0.5)
    bezel = make_material("tv_bezel", "#121214", roughness=0.25)    # 画面の板 (前の枠は少しツヤがある)
    screen = make_material("tv_screen", "#0B0C0F", roughness=0.12)

    z_panel = top - PANEL_H   # 画面の板の下端
    yf, yb = -PANEL_T / 2, PANEL_T / 2   # 画面の板の前面・背面
    boxes_object("tv_body", [
        (-hx, hx, yf, yb, z_panel, top, bezel, 0.003),                                                        # 画面の板
        (-hx + 0.10, hx - 0.10, yb - 0.002, yb + BACK_T, z_panel + 0.03, top - 0.13, black, 0.012),          # 背面のふくらみ
        (-NECK_W / 2, NECK_W / 2, yb, yb + 0.03, BASE_T - 0.002, z_panel + 0.06, black, 0.006),              # 首
        (-BASE_W / 2, BASE_W / 2, -hy, hy, 0, BASE_T, black, 0.005),                                          # 台座
    ], parent=root)
    boxes_object("tv_screen", [   # 枠の前に 1mm だけ出した黒い面 (枠と同じ面にすると、ちらつく)
        (-hx + BEZEL, hx - BEZEL, yf - 0.001, yf, z_panel + BEZEL_BOTTOM, top - BEZEL, screen),
    ], parent=root, bevel=0.0003)
    silver = make_material("tv_logo", "#9A9CA0", roughness=0.35, metallic=0.6)
    led = make_material("tv_led", "#FF2A1A", emission=2.5)
    zb = z_panel + BEZEL_BOTTOM / 2   # 下の枠の中ほど
    boxes_object("tv_marks", [
        (-0.022, 0.022, yf - 0.0006, yf, zb - 0.002, zb + 0.002, silver),          # 社名の代わりの帯
        (-0.075, -0.069, yf - 0.0008, yf, zb - 0.0015, zb + 0.0015, led),          # 待機中のランプ
    ], parent=root, bevel=0.0002)
    return root
