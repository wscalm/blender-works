"""テレビ台。正方形の箱を組み合わせた L 字の棚2つでできている (ユーザー指定)。

どちらも背板が無く、箱はトンネルのように奥の壁が見える。扉なし。色はデスク1の天板と同じオーク。
L字棚1 = 箱4つ。北東の隅に、背面を北壁・右側面を東壁にくっつけ、箱の口を部屋側 (南) に向ける。正面から見て
    □           下に3つ並べ、西端 (ソファー側) の上に1つ積む
    □□□
L字棚2 = 箱3つの L 字を上下逆さにしたもの。エアコンの下の東壁に、箱の口を西に向けて置く。正面 (西) から見て
    □□          上の段の北の箱は L字棚1 の東端の箱の上に乗る。下の段の南の箱は床に立つ
     □          上の段の箱2つ分の幅にテレビ (furniture_tv.py) を載せる
位置・大きさは layout.py (tv_shelf1, tv_shelf2)。ローカル座標: 原点 = 足元の中心 / 正面 = -Y / 正面から見て右 = +X
構成: Empty `tv_stand` (クリック判定用。部屋の原点に置く) の下に Empty `tv_shelf1` `tv_shelf2`、その下に板 `tv_shelf1_body` `tv_shelf2_body`

棚の中の物 (写真 reference/IMG_1100・IMG_7064): Empty `tv_stand_items` (部屋の座標のまま) の下に
  L字棚1 の下の段: 西の箱に白い布のランドリーバスケット `tv_basket_white`、真ん中の箱にコバルトブルーの布のバスケット `tv_basket_blue` (ユーザー指定)
  L字棚1 の西の上の箱: 炊飯器 `tv_rice_cooker` (緑の布をかぶせた) + 奥に一升瓶より小さい酒瓶2本 `tv_bottles` (ユーザー指定「白いバスケットの上には炊飯器」)
  L字棚1 の西の箱の天板: 白いかごに入れた薬の箱 `tv_medicine_*` と、手前の小箱・瓶 (ユーザー指定「その上部には薬などが入ったケース」)
  L字棚1 の真ん中の箱の上: 紺のかごと封筒 `tv_navy_basket`
  L字棚2: 北の上の箱に白いかごと白い箱、南の上の箱に白いかご + 灰色の編みかご、南の下の箱に白い箱・白黒の市松のかご・薄緑の箱
写真で判別できない物 (ルーター・ケーブル・袋など) は作らない
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import random

from props import *
from layout import FURNITURE, TV_BOARD as T

L_SHELF1 = {(0, 0), (1, 0), (2, 0), (0, 1)}   # 箱の位置 (列: 正面から見て左から, 段: 下から)
L_SHELF2 = {(0, 1), (1, 1), (1, 0)}           # 左 (北) の上の箱は L字棚1 に乗るので、その下は空き


def cube_shelf(name, cells, mat, parent):
    """正方形の箱を並べた棚 (背板なし) を1つのメッシュにする。隣り合う箱は板を共有する。
    箱の大きさは layout の幅を列の数で割って決める (高さも同じ間隔で積む)。
    z0 > 0 で浮かせた棚は、最下段の板を床まで伸ばす (他の棚に乗せた分だけ浮いた棚が、床にも着くように)。"""
    e = FURNITURE[name]
    ncols = max(c for c, _ in cells) + 1
    p = (e["w"] - T) / ncols                 # 箱の間隔 (板1枚 + 内法)
    x0, y0, y1 = -e["w"] / 2, -e["d"] / 2, e["d"] / 2

    def X(i):   # i 本目の縦の板の左面
        return x0 + i * p

    def Z(j):   # j 段目の横の板の下面。最下段の板は床から
        return j * p if j > 0 else -e["z0"]

    boxes = []
    for i in range(ncols + 1):   # 縦の板: 左右どちらかに箱がある段を、上下に続く範囲ごとに1枚にまとめる
        runs = []
        for r in sorted({r for c, r in cells if c in (i - 1, i)}):
            if runs and runs[-1][1] == r - 1:
                runs[-1][1] = r
            else:
                runs.append([r, r])
        for ra, rb in runs:
            boxes.append((X(i), X(i) + T, y0, y1, Z(ra), Z(rb + 1) + T, mat))
    for c, j in sorted({(c, r + k) for c, r in cells for k in (0, 1)}):   # 横の板: 箱の上下。縦の板の間に入れる
        boxes.append((X(c) + T, X(c + 1), y0, y1, Z(j), j * p + T, mat))

    root = add_empty(name, (e["x"], e["y"], e["z0"]), FACING_DEG[e["facing"]])
    root.parent = parent
    boxes_object(f"{name}_body", boxes, parent=root)
    return root


def build_tv_stand():
    stand = add_empty("tv_stand")   # クリック判定用の親 (部屋の原点)
    wood = wood_material("tv_stand_oak", "oak_soft")   # 木目は薄く (ユーザー指定)
    cube_shelf("tv_shelf1", L_SHELF1, wood, stand)
    cube_shelf("tv_shelf2", L_SHELF2, wood, stand)
    _items(stand)
    return stand


# ---------------------------------------------------------------- 棚の中の物
def _fabric_basket(name, x0, x1, y0, y1, z0, z1, mat, seed, parent, wall=0.008, cuff=0.035):
    """布のバスケット: 底 + 4枚の壁 + 口の折り返し (厚い帯)。壁はひだで少し波打つ (角では動かさない)"""
    w = wall
    items = [(x0, x1, y0, y1, z0, z0 + w, mat, 0.004, (0, 0, 0))]
    for a0, a1, b0, b1 in ((x0, x1, y0, y0 + w), (x0, x1, y1 - w, y1), (x0, x0 + w, y0 + w, y1 - w), (x1 - w, x1, y0 + w, y1 - w)):
        items.append((a0, a1, b0, b1, z0, z1 - cuff, mat, 0.003, (0, 0, 0)))
    c = 2.2 * w   # 折り返しは外へ厚く
    for a0, a1, b0, b1 in ((x0 - w, x1 + w, y0 - w, y0 - w + c), (x0 - w, x1 + w, y1 + w - c, y1 + w),
                           (x0 - w, x0 - w + c, y0 - w + c, y1 + w - c), (x1 + w - c, x1 + w, y0 - w + c, y1 + w - c)):
        items.append((a0, a1, b0, b1, z1 - cuff, z1, mat, 0.008, (0.003, 0.003, 0.0)))
    obj = soft_boxes_object(name, items, parent=parent, cuts=6)
    f = folds(seed, 0.006, k=(25.0, 50.0), tilt=0.5)

    def shape(p):
        x, y, z = p
        if z < z0 + w + 1e-4:
            return p
        d = [x - x0 + w, x1 + w - x, y - y0 + w, y1 + w - y]   # 4枚の壁 (外面) までの距離
        i = d.index(min(d))
        u, (lo, hi) = (y, (y0, y1)) if i < 2 else (x, (x0, x1))
        fade = smoothstep(min(u - lo, hi - u) / 0.05) * smoothstep((z - z0) / 0.1)
        n = ((-1, 0), (1, 0), (0, -1), (0, 1))[i]
        dz = f(u, z) * fade
        return (x + n[0] * dz, y + n[1] * dz, z)
    deform(obj, shape)
    return obj


def _lumps(name, center, size, mat, seed, parent, n=3):
    """かごの口から見える、くしゃっと詰めた布 (タオル・服)"""
    rng = random.Random(seed)
    cx, cy, top = center
    sx, sy = size
    items = []
    for _ in range(n):
        x, y = cx + rng.uniform(-0.2, 0.2) * sx, cy + rng.uniform(-0.2, 0.2) * sy
        w, d, h = rng.uniform(0.3, 0.45) * sx, rng.uniform(0.3, 0.45) * sy, rng.uniform(0.05, 0.08)
        items.append((x - w / 2, x + w / 2, y - d / 2, y + d / 2, top - h, top - h + h * rng.uniform(0.9, 1.3), mat, 0.025, (0.01, 0.01, 0.015)))
    return soft_boxes_object(name, items, parent=parent, cuts=8, wrinkle=0.006, wrinkle_size=0.07, seed=seed)


def _box_basket(name, x0, x1, y0, y1, z0, z1, mat, parent, wall=0.004):
    """樹脂や編んだかご (上の開いた薄い板の箱)"""
    return boxes_object(name, open_box(x0, x1, y0, y1, z0, z1, wall, mat), parent=parent, bevel=0.0012)


def _items(stand):
    """棚の中の物。部屋の座標で置く。箱の内法 (写真で見えている物だけ):
    L字棚1 (口は南、Y 3.20〜3.60): 西の箱 X 3.418〜3.827 (下段 Z 0.018〜0.427 / 上段 Z 0.445〜0.855、天板 0.873)、真ん中 X 3.845〜4.255 (上面 0.445)
    L字棚2 (口は西、X 4.30〜4.70): 北の上の箱 Y 3.173〜3.582 / 南の箱 Y 2.745〜3.155、上段 Z 0.463〜0.873、下段 Z 0.036〜0.445"""
    g = world_group("tv_stand_items", stand)
    # ---- L字棚1 の下の段: 布のランドリーバスケット (白・コバルトブルー)。中に布が少し見える
    canvas = fabric_material("tv_basket_white", "canvas", (230, 226, 216))
    blue = fabric_material("tv_basket_blue", "canvas", (86, 113, 154))
    _fabric_basket("tv_basket_white", 3.44, 3.805, 3.225, 3.58, 0.018, 0.355, canvas, 51, g)
    _fabric_basket("tv_basket_blue", 3.868, 4.232, 3.225, 3.58, 0.018, 0.37, blue, 52, g)
    _lumps("tv_basket_white_cloth", (3.62, 3.40, 0.345), (0.33, 0.32), make_material("tv_cloth_gray", "#8D8F93", roughness=1.0), 53, g)
    _lumps("tv_basket_blue_cloth", (4.05, 3.40, 0.36), (0.33, 0.32), make_material("tv_cloth_navy", "#2C3346", roughness=1.0), 54, g)

    # ---- L字棚1 の西の上の箱: 炊飯器 (白) に緑の布をかぶせ、奥に酒瓶2本
    z = 0.4453
    white = make_material("tv_rice_cooker", "#ECEAE4", roughness=0.35)
    panel = make_material("tv_rice_cooker_panel", "#4A4C50", roughness=0.25)
    soft_boxes_object("tv_rice_cooker", [
        (3.47, 3.73, 3.21, 3.50, z, z + 0.20, white, 0.045, (0.004, 0.004, 0.0)),
        (3.485, 3.715, 3.225, 3.485, z + 0.19, z + 0.225, white, 0.04, (0.0, 0.0, 0.008)),   # ふた
    ], parent=g, cuts=8)
    boxes_object("tv_rice_cooker_panel", [(3.555, 3.645, 3.206, 3.211, z + 0.12, z + 0.165, panel, 0.001)], parent=g)
    cloth = fabric_material("tv_rice_cooker_cloth", "cotton", (107, 110, 78))
    top = z + 0.233
    c = soft_boxes_object("tv_rice_cooker_cloth", [(3.45, 3.71, 3.18, 3.47, top - 0.004, top + 0.006, cloth, 0.004, (0, 0, 0.003))],
                          parent=g, cuts=14, wrinkle=0.006, wrinkle_size=0.06, seed=55)
    deform(c, lambda p: (p[0], p[1], p[2] - 2.6 * max(0.0, 3.22 - p[1]) - 2.0 * max(0.0, 3.475 - p[0])))   # 手前と西の端が垂れる
    glass = make_material("tv_bottle_glass", "#2B1D12", roughness=0.12, specular=0.7)
    label = make_material("tv_bottle_label", "#E3DCC8", roughness=0.7)
    cap = make_material("tv_bottle_cap", "#8A6E3A", roughness=0.35, metallic=0.6)
    prof = [(0, 0, 0), (0.037, 0, 0), (0.04, 0.006, 0), (0.04, 0.06, 1), (0.0405, 0.06, 1), (0.0405, 0.15, 0), (0.04, 0.15, 0),
            (0.04, 0.19, 0), (0.03, 0.22, 0), (0.016, 0.245, 0), (0.016, 0.262, 2), (0.0175, 0.262, 2), (0.0175, 0.297, 2), (0, 0.297, 0)]
    for i, (bx, by) in enumerate(((3.50, 3.552), (3.59, 3.554))):
        lathe_object(f"tv_bottle_{i}", prof, [glass, label, cap], parent=g, segments=20, location=(bx, by, z))

    # ---- L字棚1 の西の箱の天板 (Z 0.873): 白いかごに薬の箱。手前に小箱と瓶
    z = 0.8727
    mesh_white = make_material("tv_basket_mesh_white", "#FFFFFF", roughness=0.4, texture="basket_mesh.jpg", texture_size=0.128)
    _box_basket("tv_medicine_basket", 3.52, 3.80, 3.30, 3.52, z, z + 0.105, mesh_white, g)
    rng = random.Random(56)
    colors = ["#F2F0EA", "#E8EEF4", "#F4E6E8", "#EAF2E6", "#F6F1DE", "#DCE6F2"]
    boxes, x = [], 3.528
    while x + 0.045 < 3.792:
        w = rng.uniform(0.022, 0.045)
        d = rng.uniform(0.06, 0.10)
        y0 = rng.uniform(3.31, 3.51 - d)
        boxes.append((x, x + w - 0.002, y0, y0 + d, z + 0.004, z + rng.uniform(0.11, 0.15),
                      make_material(f"tv_medicine_{len(boxes)}", rng.choice(colors), roughness=0.6)))
        x += w
    boxes += [(3.42, 3.452, 3.215, 3.275, z, z + 0.105, make_material("tv_medicine_pink", "#F3D7DC", roughness=0.6)),
              (3.455, 3.497, 3.215, 3.265, z, z + 0.095, make_material("tv_medicine_blue", "#D5E3F5", roughness=0.6))]
    boxes_object("tv_medicine_boxes", boxes, parent=g, bevel=0.0015)
    lathe_object("tv_medicine_bottle_white", [(0, 0, 0), (0.021, 0, 0), (0.022, 0.065, 0), (0.016, 0.07, 1), (0.016, 0.085, 1), (0, 0.085, 1)],
                 [make_material("tv_pill_bottle", "#F4F4F0", roughness=0.4), make_material("tv_pill_cap", "#E9E9E6", roughness=0.3)],
                 parent=g, segments=16, location=(3.52, 3.245, z))
    lathe_object("tv_medicine_bottle_brown", [(0, 0, 0), (0.018, 0, 0), (0.019, 0.07, 0), (0.011, 0.08, 1), (0.011, 0.095, 1), (0, 0.095, 1)],
                 [make_material("tv_brown_bottle", "#5A3418", roughness=0.15, specular=0.7), make_material("tv_brown_cap", "#F0F0EC", roughness=0.4)],
                 parent=g, segments=16, location=(3.565, 3.24, z))

    # ---- L字棚1 の真ん中の箱の上 (Z 0.445): 紺のかご + 立てた封筒
    z = 0.4453
    navy = make_material("tv_basket_navy", tint((240, 240, 237), (31, 43, 77)), roughness=0.45, texture="basket_mesh.jpg", texture_size=0.128)
    _box_basket("tv_navy_basket", 3.88, 4.14, 3.24, 3.44, z, z + 0.135, navy, g)
    paper = make_material("tv_envelope", "#E9EEF2", roughness=0.8)
    solids_object("tv_envelope", [rot_box(-0.09, 0.09, -0.002, 0.002, 0, 0.235, paper, place(4.01, 3.33, z + 0.006, pitch=-9, roll=4))],
                  parent=g, bevel=0.0008)

    # ---- L字棚2 (口は西)
    z = 0.4633
    mesh_white2 = make_material("tv_basket_mesh_white2", "#F6F6F3", roughness=0.4, texture="basket_mesh.jpg", texture_size=0.128)
    _box_basket("tv_basket_north", 4.33, 4.58, 3.22, 3.40, z, z + 0.11, mesh_white2, g)                  # 北の上の箱: 白いかご
    boxes_object("tv_box_north", [(4.35, 4.49, 3.43, 3.55, z, z + 0.075, make_material("tv_white_box", "#EFEFEC", roughness=0.5))],
                 parent=g)
    _box_basket("tv_basket_south", 4.33, 4.63, 2.78, 3.08, z, z + 0.12, mesh_white2, g)                  # 南の上の箱: 白いかご
    woven = make_material("tv_basket_woven", "#FFFFFF", roughness=0.8, texture="basket_woven.jpg", texture_size=0.20)
    _box_basket("tv_basket_woven", 4.315, 4.665, 2.765, 3.14, z + 0.12, z + 0.28, woven, g, wall=0.008)   # その上に灰色の編みかご
    blue_pack = make_material("tv_blue_pack", "#3F72B8", roughness=0.5)
    solids_object("tv_blue_packs", [rot_box(-0.07, 0.07, -0.004, 0.004, 0, 0.20, blue_pack, place(4.42 + 0.07 * i, 2.90 + 0.05 * i, z + 0.128, pitch=8 - 14 * i, yaw=90))
                                    for i in range(2)], parent=g, bevel=0.0015)
    z = 0.036                                                                                            # 南の下の箱
    boxes_object("tv_box_south", [(4.32, 4.62, 2.76, 3.00, z, z + 0.10, make_material("tv_white_box2", "#F2F2EF", roughness=0.5)),
                                  (4.33, 4.45, 2.78, 3.00, z + 0.10, z + 0.19, make_material("tv_green_box", "#BFE3C9", roughness=0.55))],
                 parent=g)
    check = make_material("tv_basket_check", "#FFFFFF", roughness=0.6, texture="basket_check.jpg", texture_size=0.12)
    _box_basket("tv_basket_check", 4.32, 4.62, 3.005, 3.145, z, z + 0.11, check, g, wall=0.006)
    _box_basket("tv_basket_check_small", 4.46, 4.62, 2.79, 2.98, z + 0.10, z + 0.18, check, g, wall=0.006)
    return g
