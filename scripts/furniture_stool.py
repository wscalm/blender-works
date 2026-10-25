"""木のスツール (reference/864-g01-2.jpg)。角柱の脚 4 本 + 座面 + 座面の下の幕板 + 脚の下のほうの貫。

位置・大きさは layout.py。ローカル座標: 原点 = 足元の中心 / 正面 = -Y / 幅は X
構成: Empty `stool` の下に、メッシュ `stool_body` (座面 / 脚・幕板・貫 の2色)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from layout import FURNITURE

SEAT = "#E6C795"      # 座面 (明るいナチュラルな木)
FRAME = "#D9B67F"     # 脚・幕板・貫 (座面より少しだけ濃い)


def build_stool():
    e = FURNITURE["stool"]
    hx, hy, top = e["w"] / 2, e["d"] / 2, e["h"]
    root = add_empty("stool", (e["x"], e["y"], e["z0"]), FACING_DEG[e["facing"]])

    seat = wood_material("stool_seat", "light_soft", roughness=0.6, target=SEAT)
    frame = wood_material("stool_frame", "light_soft", roughness=0.6, target=FRAME)

    t_seat = 0.035             # 座面の厚み
    leg = 0.05                 # 脚の太さ (正方形)
    inset = 0.006              # 座面の縁から脚を少し引っ込める
    lx, ly = hx - inset, hy - inset                  # 脚の外側
    ix, iy = lx - leg, ly - leg                      # 脚の内側 (幕板・貫が渡る範囲)
    z_seat = top - t_seat
    t_rail = 0.022             # 幕板・貫の厚み
    r_out = 0.006              # 幕板・貫は脚の外面より少し引っ込める

    boxes = [(-hx, hx, -hy, hy, z_seat, top, seat)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            boxes.append((sx * ix, sx * lx, sy * iy, sy * ly, 0, z_seat, frame))
    # 幕板 (座面の下) と貫 (脚の下のほう): 前後は X 方向に、左右は Y 方向に渡す
    for z0, z1 in ((z_seat - 0.055, z_seat), (0.26 * top, 0.26 * top + 0.04)):   # 貫は高さの約 1/4 のところ
        for sy in (-1, 1):
            boxes.append((-ix, ix, sy * (ly - r_out - t_rail), sy * (ly - r_out), z0, z1, frame))
        for sx in (-1, 1):
            boxes.append((sx * (lx - r_out - t_rail), sx * (lx - r_out), -iy, iy, z0, z1, frame))
    boxes_object("stool_body", boxes, parent=root)
    return root
