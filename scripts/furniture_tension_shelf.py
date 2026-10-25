"""突っ張り棒の棚 (写真 reference/IMG_1099)。デスク2の奥 (南壁とデスクのすき間) に、床から天井まで突っ張る黒い柱2本を立て、
黒っぽい棚板2枚を柱の金具で宙に浮かせる。幅は「デスク2の左から 5分の4」(ユーザー指定)。

下の棚板: 奥に本を立てて並べ、手前に平積みの本が2山 (写真)。上の棚板: 夕焼けの海の絵 (白い台紙の額) と茶色の絵本を壁に立て掛ける。
棚板の高さ (1.45 / 1.82) は写真から見積もった (モニターの上端 1.26 より上)。柱の上の方に銀色の継ぎ目と、天井と床に黒い受け。
位置・大きさは layout.py (tension_shelf)。ローカル座標: 原点 = 足元の中心 / 正面 = -Y (部屋の側) / 正面から見て右 = +X / 背面 (+Y) = 南壁
構成: Empty `tension_shelf` の下に `tension_shelf_poles` (柱・受け・継ぎ目)、`tension_shelf_boards` (棚板・金具)、
`tension_shelf_books`、`tension_shelf_painting_*`、`tension_shelf_picture_book*`。クリック対象には未登録
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props import *
from layout import FURNITURE
from room_spec import ROOM_H

POLE_R = 0.016        # 柱の太さ (半径)
POLE_Y = 0.125        # 柱の中心 (ローカル Y。南壁から 3.5cm)
BOARD_TOPS = (1.45, 1.82)   # 棚板の上面の高さ (下・上)
BOARD_T = 0.02
JOINT_Z = 2.0         # 柱の継ぎ目 (この上は細い管が伸びて天井を押す)


def build_tension_shelf():
    e = FURNITURE["tension_shelf"]
    hx, hy = e["w"] / 2, e["d"] / 2
    root = add_empty("tension_shelf", (e["x"], e["y"], e["z0"]), FACING_DEG[e["facing"]])
    black = make_material("tension_pole", "#1E1E20", roughness=0.4)
    silver = make_material("tension_joint", "#C3C5C7", roughness=0.3, metallic=0.7)
    board = wood_material("tension_board", "walnut_soft", roughness=0.5, target=(58, 52, 48))

    px = hx - POLE_R   # 柱の中心 (左右)
    for sx in (-1, 1):
        lathe_object(f"tension_shelf_pole_{'e' if sx < 0 else 'w'}", [   # (正面から見て左 = 東 / 右 = 西)
            (0, 0, 0), (0.03, 0, 0), (0.03, 0.012, 0), (POLE_R, 0.012, 0),          # 床の受け
            (POLE_R, JOINT_Z - 0.02, 1), (0.018, JOINT_Z - 0.02, 1), (0.018, JOINT_Z + 0.01, 1),   # 継ぎ目 (銀)
            (0.0125, JOINT_Z + 0.01, 0), (0.0125, ROOM_H - 0.014, 0),                  # 上の細い管
            (0.035, ROOM_H - 0.014, 0), (0.035, ROOM_H - 0.001, 0), (0, ROOM_H - 0.001, 0),   # 天井の受け
        ], [black, silver], parent=root, segments=20, location=(sx * px, POLE_Y, 0))
    knobs = [(sx * px - 0.01, sx * px + 0.01, POLE_Y - POLE_R - 0.025, POLE_Y - POLE_R, z - 0.012, z + 0.012, black)
             for sx in (-1, 1) for z in (2.15,)]   # 突っ張りを締めるつまみ

    # 棚板: 柱の間はいっぱいの奥行。柱の外側は柱の前までの切り欠き。下に柱へ留める金具
    boxes = list(knobs)
    for top in BOARD_TOPS:
        z0 = top - BOARD_T
        boxes += [(-px + POLE_R + 0.001, px - POLE_R - 0.001, -hy, hy - 0.02, z0, top, board)]
        for sx in (-1, 1):
            boxes += [
                (sx * (px - POLE_R - 0.001), sx * hx, -hy, POLE_Y - POLE_R - 0.004, z0, top, board),   # 柱の前の端
                (sx * (px - 0.012), sx * (px + 0.012), POLE_Y - 0.11, POLE_Y - POLE_R, z0 - 0.022, z0, black),   # 金具の腕
                (sx * (px - 0.022), sx * (px + 0.022), POLE_Y - 0.022, POLE_Y + 0.022, z0 - 0.05, z0 + 0.004, black),   # 柱を挟む金具
            ]
    boxes_object("tension_shelf_boards", boxes, parent=root)

    # 下の棚板の本: 奥に立てて並べ (東端 = 正面から見て左に背の高い上製本)、手前に平積みが2山
    rng = random.Random(8)
    z = BOARD_TOPS[0]
    back = hy - 0.025
    books = book_row(rng, -px + POLE_R + 0.003, -0.33, z, ["dark"], (0.23, 0.26), thick=(0.028, 0.04),
                     depth=(0.13, 0.135), y_back=back, lean=False)
    books += book_row(rng, -0.33, 0.2, z, ["tech", "misc", "manga", "dark"], (0.18, 0.225), thick=(0.012, 0.03),
                      depth=(0.125, 0.135), y_back=back, fill=0.95)
    books += book_stack(rng, -0.17, -0.092, z, ["tech", "misc", "dark"], [(0.21, 0.148), (0.21, 0.148), (0.2, 0.14), (0.18, 0.128)])
    books += book_stack(rng, 0.30, -0.08, z, ["bunko", "misc", "tech"], [(0.182, 0.128), (0.182, 0.128), (0.148, 0.105),
                                                                         (0.148, 0.105), (0.148, 0.105)], thick=(0.01, 0.018))
    books_object("tension_shelf_books", books, parent=root)

    # 上の棚板: 夕焼けの絵 (額の外寸 0.58 x 0.46) と絵本 (0.24 x 0.29) を壁に立て掛ける。上の縁が壁から 2mm
    z = BOARD_TOPS[1]
    wall = hy
    for name, x, w, h, foot in (("painting", -0.12, 0.58, 0.46, 0.05), ("picture_book", 0.325, 0.24, 0.29, 0.03)):
        lean = math.degrees(math.asin((foot - 0.002) / h))
        m = place(x, wall - foot, z, pitch=lean)
        if name == "painting":
            framed_picture("tension_shelf_painting", w, h, 0.012, 0.05, "print_sunset.jpg", "#E6E4DF", m, parent=root)
        else:
            brown = make_material("tension_picture_book", "#5A3626", roughness=0.6)
            solids_object("tension_shelf_picture_book", [rot_box(-w / 2, w / 2, -0.012, 0, 0, h, brown, m)], parent=root, bevel=0.002)
            image_quad("tension_shelf_picture_book_cover", w - 0.004, h - 0.004,
                       picture_material("tension_picture_book_cover", "picture_book.jpg", roughness=0.5),
                       m @ Matrix.Translation((0, -0.0125, 0.002)), parent=root)
    return root
