"""デスク2つ (南壁沿い。ドア側からデスク1・デスク2)。木目の天板 + 黒い角脚4本 (脚は2つで共通)。
写真 (reference/IMG_1099) に合わせて、天板の下に黒い細い枠 (幕板) と、奥 (壁側) の脚の間に細い棒の X の補強を付けた。

デスク1 = ナチュラルな明るい木目 (フローリングくらい) / デスク2 = ウォールナット。
位置・大きさは layout.py (desk1, desk2)。ローカル座標: 原点 = 足元の中心 / 正面 (座る側) = -Y / 幅は X
構成: Empty `desk1` / `desk2` の下に、天板 `desk1_top` と脚・枠 `desk1_legs`・X の補強 `desk1_brace` (desk2 も同じ)。
デスク2の上の小物 (写真) は Empty `desk2_items` (部屋の座標のまま) の下: 白い小物入れ・緑の瓶・ワイヤレスイヤホンのケース・スマートフォンと充電ケーブル・メモ帳
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


def _desk2_items(root):
    """デスク2の上の小物 (写真 reference/IMG_1099)。部屋の座標で置く (デスク2は X 2.30〜3.50 / Y 0.10〜0.60、天板 0.75)。
    キーボード (X 2.41〜2.85) とサブモニターの白い箱 (X 3.27 まで) をよけて、東の手前に並べる"""
    g = world_group("desk2_items", root)
    z = FURNITURE["desk2"]["h"]
    white = make_material("desk2_organizer", "#F1F0EC", roughness=0.45)
    # 白い小物入れ (仕切り2枚。ペンが3本)
    x0, x1, y0, y1, h = 3.30, 3.48, 0.44, 0.53, 0.10
    boxes_object("desk2_organizer", open_box(x0, x1, y0, y1, z, z + h, 0.004, white) + [
        (x0 + 0.06, x0 + 0.064, y0 + 0.004, y1 - 0.004, z, z + h - 0.02, white),
        (x0 + 0.12, x0 + 0.124, y0 + 0.004, y1 - 0.004, z, z + h - 0.02, white)], parent=g, bevel=0.0012)
    pens = [((x0 + 0.03 + dx, 0.485 + dy, z + 0.005), (x0 + 0.03 + dx + lx, 0.485 + dy + ly, z + 0.14))
            for dx, dy, lx, ly in ((-0.01, -0.01, -0.012, -0.008), (0.008, 0.012, 0.006, 0.01), (0.0, -0.002, 0.014, -0.006))]
    for (a, b), color in zip(pens, ("#1B1B1D", "#2E4C9A", "#F2F2F0")):
        tubes_object(f"desk2_pen_{color[1:]}", [[a, b]], 0.0045, make_material(f"desk2_pen_{color[1:]}", color, roughness=0.4), parent=g, sides=8)
    # 緑の瓶 (白いふた)
    lathe_object("desk2_jar", [(0, 0, 0), (0.033, 0, 0), (0.034, 0.055, 0), (0.035, 0.056, 1), (0.035, 0.075, 1), (0, 0.075, 1)],
                 [make_material("desk2_jar", "#2F7D5B", roughness=0.3), make_material("desk2_jar_lid", "#F2F2EF", roughness=0.35)],
                 parent=g, segments=20, location=(3.24, 0.50, z))
    # ワイヤレスイヤホンのケース (白、寝かせて置く)
    soft_boxes_object("desk2_earbuds", [(3.15, 3.204, 0.535, 0.58, z, z + 0.022, white, 0.01, (0.001, 0.001, 0.002))], parent=g, cuts=6)
    # スマートフォン (白。画面は消えている) と白い充電ケーブル (机の奥へ)
    m = place(3.06, 0.50, z, yaw=18)
    solids_object("desk2_phone", [rot_box(-0.035, 0.035, -0.07, 0.07, 0, 0.008, white, m, 0.003),
                                  rot_box(-0.032, 0.032, -0.065, 0.065, 0.008, 0.0085, make_material("desk2_phone_screen", "#101114", roughness=0.1), m, 0.0005)],
                  parent=g)
    tip = m @ Vector((0, -0.072, 0.004))   # 下の端の差し込み口から、サブモニターの白い箱の北をまわって机の奥へ
    cable = [tuple(tip), (3.11, 0.445, z + 0.003), (3.17, 0.475, z + 0.003), (3.24, 0.455, z + 0.003), (3.29, 0.41, z + 0.003),
             (3.33, 0.30, z + 0.003), (3.38, 0.16, z + 0.003), (3.40, 0.105, z + 0.002), (3.405, 0.096, z - 0.03), (3.41, 0.09, z - 0.30)]
    tubes_object("desk2_cable", [cable], 0.0018, make_material("desk2_cable", "#F4F4F2", roughness=0.4), parent=g, sides=6)
    # メモ帳 (白い紙の束)
    paper = make_material("desk2_notepad", "#F7F6F1", roughness=0.85)
    solids_object("desk2_notepad", [rot_box(-0.05, 0.05, -0.075, 0.075, 0, 0.008, paper, place(2.94, 0.51, z, yaw=4), 0.001)], parent=g)
    return g


def build_desks():
    leg = make_material("desk_leg", LEG_COLOR, roughness=0.5)
    d1, d2 = _desk("desk1", "oak", leg), _desk("desk2", "walnut", leg)
    _desk2_items(d2)
    return d1, d2
