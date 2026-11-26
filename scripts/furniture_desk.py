"""デスク2つ (南壁沿い。ドア側からデスク1・デスク2)。木目の天板 + 黒い角脚4本 (脚は2つで共通)。
写真 (reference/IMG_1099) に合わせて、天板の下に黒い細い枠 (幕板) と、奥 (壁側) の脚の間に細い棒の X の補強を付けた。

デスク1 = ナチュラルな明るい木目 (フローリングくらい) / デスク2 = ウォールナット。
位置・大きさは layout.py (desk1, desk2)。ローカル座標: 原点 = 足元の中心 / 正面 (座る側) = -Y / 幅は X
構成: Empty `desk1` / `desk2` の下に、天板 `desk1_top` と脚・枠 `desk1_legs`・X の補強 `desk1_brace` (desk2 も同じ)。
デスク2の上の小物 (文庫本・コースター・ペン立て・Echo Show 5) は furniture_desk_items.py (Empty `desk2_items` の下)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props import *
from layout import FURNITURE

TOP_T = 0.03          # 天板の厚み
LEG = 0.04            # 脚の太さ (正方形の角パイプ)
LEG_INSET = 0.04      # 天板の縁から脚の外面までの引っ込み
LEG_COLOR = "#1C1C1E"  # 黒
APRON = 0.04          # 幕板 (天板の下の枠) の高さ


def _desk(name, wood, leg_mat):
    e = FURNITURE[name]
    hx, hy, top = e["w"] / 2, e["d"] / 2, e["h"]
    root = add_empty(name, (e["x"], e["y"], e["z0"]), FACING_DEG[e["facing"]])

    boxes_object(f"{name}_top", [(-hx, hx, -hy, hy, top - TOP_T, top, wood_material(f"{name}_top", wood))], parent=root)
    lx, ly = hx - LEG_INSET, hy - LEG_INSET
    legs = [(sx * lx, sx * (lx - LEG), sy * ly, sy * (ly - LEG), 0, top - TOP_T, leg_mat)
            for sx in (-1, 1) for sy in (-1, 1)]
    zu = top - TOP_T                       # 天板の下面
    for sy in (-1, 1):                     # 幕板: 脚の外面に揃えた細い枠 (高さ 4cm・厚み 2cm)
        legs.append((-lx + LEG, lx - LEG, sy * ly, sy * (ly - 0.02), zu - APRON, zu, leg_mat))
    for sx in (-1, 1):
        legs.append((sx * lx, sx * (lx - 0.02), -ly + LEG, ly - LEG, zu - APRON, zu, leg_mat))
    boxes_object(f"{name}_legs", legs, parent=root)
    # X の補強: 奥 (壁側 +Y) の脚の間に、幕板の下から床の近くまで斜めの細い棒を2本
    yb = ly - LEG / 2
    xa, za, zb = lx - LEG, zu - APRON - 0.01, 0.10
    tubes_object(f"{name}_brace", [[(-xa, yb, za), (xa, yb, zb)], [(xa, yb + 0.006, za), (-xa, yb + 0.006, zb)]],
                 0.004, leg_mat, parent=root, sides=6)
    return root


def build_desks():
    leg = make_material("desk_leg", LEG_COLOR, roughness=0.5)
    return _desk("desk1", "oak", leg), _desk("desk2", "walnut", leg)
