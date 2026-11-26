"""本棚 (ウォールナット)。2列 x 4段の正方形の箱を積んだ形で、扉が4枚 (reference/61ui-F6+2nL._AC_SL1000_.jpg)。

1マスの内法は幅から決めた正方形。高さの余り (幅 1.0 / 高さ 2.0 なら 1.8cm) は底板を厚くして吸収する。

扉は上の段から 左・右・左・右 (正面から見て) の互い違い。写真 (reference/IMG_1099) のとおり、扉の下には雑誌を立てる受けがあり、
最上段の扉に青紫の絵と本の箱、2段目の扉に賞状と小さな箱を飾っている。
扉の無い4マスは、どれも中に棚板が1枚あって上下2段。写真を見て、本・かご・小物を入れた:
  最上段 (右)  上: 濃い色の上製本 + 白いかご / 下: 技術書
  2段目 (左)   上: 漫画・単行本 / 下: 文庫
  3段目 (右)   上: 白いかご (中に布) + 籐のかご / 下: えんじ色のケース・黒い袋・平積みの本
  最下段 (左)  上: 本 / 下: 灰色と白の収納ケース
天板の上に書類の束、最下段の扉 (右) の受けに、月夜の絵の額 (横長) を立てる (2026-10-27 ユーザー指定「きちんとラック部分に乗せて」)。
位置・大きさは layout.py。ローカル座標: 原点 = 足元の中心 / 正面 = -Y / 正面から見て右 = +X
構成: Empty `bookshelf` の下に、枠 `bookshelf_body` (側板・天板・底板・仕切り・棚板・背板)、扉 `bookshelf_doors` (受け付き)、
Empty `bookshelf_items` (本・かご・飾り・書類・受けに立てた絵)
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props import *
from layout import FURNITURE

T = 0.018        # 板の厚み
BACK_T = 0.006   # 背板の厚み
GAP = 0.003      # 扉のまわりのすき間
ROWS = 4
DOORS = {(0, "left"), (1, "right"), (2, "left"), (3, "right")}   # 扉の付くマス (段: 0 = 最上段, 列: 正面から見て)
LIP_D, LIP_H = 0.05, 0.055   # 扉の下の受けの奥行と高さ (写真)
MOON_W, MOON_H = 0.58, 0.50  # 最下段 (右) の扉の受けに立てた月夜の絵の額の外寸 (写真)
# 扉の無いマスの中の棚板: マスの内法の下端から棚板の上面までの高さ
INNER = {(0, "right"): 0.27, (1, "left"): 0.205, (2, "right"): 0.25, (3, "left"): 0.23}


def build_bookshelf():
    e = FURNITURE["bookshelf"]
    hx, hy, h = e["w"] / 2, e["d"] / 2, e["h"]
    root = add_empty("bookshelf", (e["x"], e["y"], e["z0"]), FACING_DEG[e["facing"]])
    wood = wood_material("bookshelf_walnut", "walnut_soft")   # 木目は薄く (ユーザー指定)

    cell = (e["w"] - 3 * T) / 2            # 1マスの内法 (正方形の一辺)
    base = h - ROWS * cell - (ROWS + 1) * T   # 高さの余り。底板を厚くして埋める
    assert base >= 0, "本棚の高さが足りない (マスを正方形にできない)"
    yb = hy - BACK_T                       # 背板の前面
    cols = {"left": (-hx + T, -T / 2), "right": (T / 2, hx - T)}   # 各列の内法 (X)
    body = [
        (-hx, -hx + T, -hy, yb, 0, h, wood),          # 側板 (左右)
        (hx - T, hx, -hy, yb, 0, h, wood),
        (-hx + T, hx - T, -hy, yb, 0, base + T, wood),   # 底板 (高さの余りの分だけ厚い)
        (-hx + T, hx - T, -hy, yb, h - T, h, wood),   # 天板
        (-T / 2, T / 2, -hy, yb, base + T, h - T, wood),   # 中央の仕切り (全段を通す)
        (-hx, hx, yb, hy, 0, h, wood),                # 背板
    ]

    def cell_top(row):   # その段の内法の上端 (段: 0 = 最上段)
        return h - T - row * (cell + T)

    for row in range(ROWS - 1):   # 段の境目の棚板 (仕切りの左右に1枚ずつ)
        z1 = cell_top(row) - cell
        for xa, xb in cols.values():
            body.append((xa, xb, -hy, yb, z1 - T, z1, wood))
    for (row, col), up in INNER.items():   # 扉の無いマスの中の棚板 (1cm 引っ込める)
        xa, xb = cols[col]
        z1 = cell_top(row) - cell + up
        body.append((xa, xb, -hy + 0.01, yb, z1 - T, z1, wood))
    boxes_object("bookshelf_body", body, parent=root)

    doors = []
    for row in range(ROWS):
        z1 = cell_top(row)
        for col, (xa, xb) in cols.items():
            if (row, col) in DOORS:
                z0 = z1 - cell + GAP
                doors += [
                    (xa + GAP, xb - GAP, -hy, -hy + T, z0, z1 - GAP, wood),                       # 扉
                    (xa + GAP, xb - GAP, -hy - LIP_D, -hy, z0, z0 + 0.012, wood),                 # 受けの底
                    (xa + GAP, xb - GAP, -hy - LIP_D, -hy - LIP_D + 0.012, z0, z0 + LIP_H, wood),  # 受けの前板
                ]
    boxes_object("bookshelf_doors", doors, parent=root)

    items = add_empty("bookshelf_items")
    items.parent = root
    _fill(items, cols, cell_top, cell, hy, yb)
    return root


def _fill(items, cols, cell_top, cell, hy, yb):
    rng = random.Random(3)
    front = -hy + 0.012            # 本の背を揃える位置 (棚の前の縁から少し奥)

    def level(row, col, upper):    # マスの中の段の (x0, x1, 床の高さ, 天井の高さ)
        xa, xb = cols[col]
        bottom = cell_top(row) - cell
        mid = bottom + INNER[(row, col)]
        return (xa, xb, mid, cell_top(row)) if upper else (xa, xb, bottom, mid - T)

    books = []
    # 最上段 (右): 上 = 濃い色の上製本 (左寄り) / 下 = 技術書
    xa, xb, z, top = level(0, "right", True)
    books += book_row(rng, xa, xa + 0.22, z, ["dark"], (0.15, 0.185), thick=(0.018, 0.03), depth=(0.13, 0.16),
                      y_front=front, max_h=top - z - 0.004, lean=False)
    xa, xb, z, top = level(0, "right", False)
    books += book_row(rng, xa, xb, z, ["tech"], (0.205, 0.245), thick=(0.012, 0.028), depth=(0.15, 0.185),
                      y_front=front, max_h=top - z - 0.004, fill=0.93)
    # 2段目 (左): 上 = 漫画・単行本 (右に少し空き) / 下 = 文庫 (いっぱい)
    xa, xb, z, top = level(1, "left", True)
    books += book_row(rng, xa, xb, z, ["manga", "dark", "tech"], (0.175, 0.235), thick=(0.014, 0.032),
                      depth=(0.12, 0.15), y_front=front, max_h=top - z - 0.004, fill=0.86)
    xa, xb, z, top = level(1, "left", False)
    books += book_row(rng, xa, xb, z, ["bunko"], (0.148, 0.153), thick=(0.01, 0.02), depth=(0.105, 0.108),
                      y_front=front, max_h=top - z - 0.004, fill=0.97, lean=False)
    # 3段目 (右) の下: 平積みの白い本 (右寄り)
    xa, xb, z, top = level(2, "right", False)
    books += book_stack(rng, xb - 0.1, front + 0.07, z, ["misc"], [(0.21, 0.15), (0.21, 0.15), (0.19, 0.13)])
    # 最下段 (左) の上: 本
    xa, xb, z, top = level(3, "left", True)
    books += book_row(rng, xa, xa + 0.3, z, ["misc", "tech"], (0.18, 0.21), depth=(0.13, 0.16),
                      y_front=front, max_h=top - z - 0.004)
    books_object("bookshelf_books", books, parent=items)

    white = make_material("bookshelf_basket_white", "#F2F2EE", roughness=0.6)
    gray_cloth = fabric_material("bookshelf_cloth_gray", "cotton", (170, 170, 168))
    rattan = make_material("bookshelf_rattan", "#A07848", roughness=0.8)
    maroon = make_material("bookshelf_case_maroon", "#5C1E2A", roughness=0.7)
    black = make_material("bookshelf_bag_black", "#1B1B1E", roughness=0.8)
    gray_box = make_material("bookshelf_box_gray", "#8D9196", roughness=0.6)
    paper = make_material("bookshelf_paper", "#F3F2EC", roughness=0.9)
    boxes = []
    # 最上段 (右) の上の右: 白いかご
    xa, xb, z, top = level(0, "right", True)
    boxes += open_box(xb - 0.2, xb - 0.01, front, front + 0.26, z, z + 0.13, 0.006, white)
    # 3段目 (右) の上: 白いかご (中に灰色の布) + 籐のかご
    xa, xb, z, top = level(2, "right", True)
    boxes += open_box(xa + 0.01, xa + 0.26, front, front + 0.3, z, z + 0.12, 0.006, white)
    boxes += open_box(xa + 0.28, xb - 0.02, front + 0.02, front + 0.24, z, z + 0.085, 0.008, rattan)
    soft_boxes_object("bookshelf_cloth", [
        (xa + 0.025, xa + 0.245, front + 0.02, front + 0.28, z + 0.01, z + 0.16, gray_cloth, 0.04, (0.01, 0.01, 0.025)),
    ], parent=items, cuts=8, wrinkle=0.006, wrinkle_size=0.12, seed=4)
    # 3段目 (右) の下: えんじ色のケース (平ら) + 黒い袋
    xa, xb, z, top = level(2, "right", False)
    boxes += [(xa + 0.01, xa + 0.3, front + 0.01, front + 0.26, z, z + 0.035, maroon)]
    soft_boxes_object("bookshelf_bag", [
        (xa + 0.03, xa + 0.27, front + 0.03, front + 0.25, z + 0.035, z + 0.1, black, 0.03, (0.005, 0.005, 0.015)),
    ], parent=items, cuts=8, wrinkle=0.005, wrinkle_size=0.1, seed=6)
    # 最下段 (左) の下: 灰色と白の収納ケース
    xa, xb, z, top = level(3, "left", False)
    boxes += open_box(xa + 0.01, xa + 0.24, front, front + 0.33, z, z + 0.19, 0.006, gray_box)
    boxes += open_box(xa + 0.25, xb - 0.01, front + 0.02, front + 0.3, z, z + 0.15, 0.006, white)
    boxes_object("bookshelf_things", boxes, parent=items)
    # 天板の上の書類の束 (少し前にはみ出す)
    htop = FURNITURE["bookshelf"]["h"]
    solids_object("bookshelf_papers", [
        rot_box(-0.15, 0.15, -0.11, 0.11, 0, 0.018, paper, place(-0.26, -0.1, htop, yaw=4)),
        rot_box(-0.13, 0.13, -0.1, 0.1, 0, 0.03, paper, place(0.22, -0.08, htop, yaw=-3)),
        rot_box(-0.15, 0.15, -0.1, 0.1, 0, 0.008, paper, place(-0.22, -0.12, htop + 0.018, yaw=-6)),
    ], parent=items, bevel=0.002)

    # 扉に飾った物 (受けに立てる。受けの前板の内側は -hy - LIP_D + 0.012)。最上段 (左) = 青紫の絵 + 本の箱 / 2段目 (右) = 賞状 + 小さな段ボール箱
    lip_z = lambda row: cell_top(row) - cell + GAP + 0.012
    lip_in = -hy - LIP_D + 0.012
    image_quad("bookshelf_love", 0.30, 0.38, picture_material("bookshelf_love", "print_love.jpg"),
               place(-0.215, -hy - 0.0025, lip_z(0)), parent=items)
    box_mat = picture_material("bookshelf_book_box", "book_box.jpg", roughness=0.5)
    side = make_material("bookshelf_book_box_side", "#1E2638", roughness=0.6)
    boxes_object("bookshelf_book_box_body", [(-0.455, -0.285, lip_in + 0.001, -hy - 0.004, lip_z(0), lip_z(0) + 0.235, side)],
                 parent=items)
    image_quad("bookshelf_book_box_cover", 0.166, 0.231, box_mat, place(-0.37, lip_in + 0.0005, lip_z(0) + 0.002), parent=items)
    boxes_object("bookshelf_cert_board", [(0.03, 0.30, -hy - 0.012, -hy - 0.003, lip_z(1), lip_z(1) + 0.37,
                                           make_material("bookshelf_cert_board", "#F6F5F0", roughness=0.7))], parent=items)
    image_quad("bookshelf_cert", 0.25, 0.35, picture_material("bookshelf_cert", "certificate.jpg"),
               place(0.165, -hy - 0.0125, lip_z(1) + 0.01), parent=items)
    boxes_object("bookshelf_kraft_box", [(0.33, 0.45, lip_in + 0.001, -hy - 0.014, lip_z(1), lip_z(1) + 0.15,
                                          make_material("bookshelf_kraft", "#B98F5E", roughness=0.8))], parent=items)
    image_quad("bookshelf_paper_sheet", 0.2, 0.27, paper, place(0.33, -hy - 0.0015, lip_z(1)), parent=items)

    # 最下段 (右) の扉の受けに立てた月夜の絵 (写真。2026-10-27 ユーザー指定「きちんとラック部分に乗せて」)。横長の額で、受けより幅が広く、
    # 右の端は本棚の右の側板の外面に揃い、左は左の列へ少しかかる。額の前の下の縁を受けの前板の内側に当て、上の縁の背が扉 (と上の棚板の前の縁) にもたれる。
    # 額の上の縁は最下段の上の棚板より 2cm ほど上 (写真)。絵の画像の縦横比は tools/make_prints.py の make_moon と合わせる
    w, hgt, depth = MOON_W, MOON_H, 0.02
    right = cols["right"][1] + T                          # 右の側板の外面
    y0 = lip_in + 0.001                                   # 額の前の下の縁
    lean = math.degrees(math.asin((-hy - 0.001 - (y0 + depth)) / hgt))
    framed_picture("bookshelf_moon", w, hgt, 0.022, 0.045, "print_moon.jpg", "#D9D9D6",
                   place(right - w / 2, y0 + depth, lip_z(3), pitch=lean), parent=items, depth=depth)
