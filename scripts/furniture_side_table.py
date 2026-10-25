"""白いサイドテーブル。天板 + 細い丸脚4本 (脚も白)。スツールの東隣、北壁沿い。

位置・大きさは layout.py (side_table)。ローカル座標: 原点 = 足元の中心 / 正面 = -Y / 幅は X
構成: Empty `side_table` の下に、天板 `side_table_top` と脚 `side_table_legs`。クリック対象には未登録 (スツールと同じ扱い)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from layout import FURNITURE

WHITE = "#F2F2EF"
TOP_T = 0.02     # 天板の厚み
LEG_R = 0.012    # 脚の半径 (直径 2.4cm の細い丸脚)
LEG_INSET = 0.04  # 天板の角から脚の中心まで
SIDES = 8        # 脚の断面の角数


def _round_leg(cx, cy, z1):
    """床から z1 までのまっすぐな八角柱。(verts, faces)。上下の面は床と天板で隠れるので作らない"""
    verts = [(cx + LEG_R * math.cos(a), cy + LEG_R * math.sin(a), z)
             for z in (0.0, z1) for a in (2 * math.pi * (i + 0.5) / SIDES for i in range(SIDES))]
    faces = [(i, (i + 1) % SIDES, SIDES + (i + 1) % SIDES, SIDES + i) for i in range(SIDES)]
    return verts, faces


def build_side_table():
    e = FURNITURE["side_table"]
    hx, hy, top = e["w"] / 2, e["d"] / 2, e["h"]
    root = add_empty("side_table", (e["x"], e["y"], e["z0"]), FACING_DEG[e["facing"]])
    white = make_material("side_table_white", WHITE, roughness=0.5)

    boxes_object("side_table_top", [(-hx, hx, -hy, hy, top - TOP_T, top, white)], parent=root)
    verts, faces = [], []
    for sx in (-1, 1):
        for sy in (-1, 1):
            v, f = _round_leg(sx * (hx - LEG_INSET), sy * (hy - LEG_INSET), top - TOP_T)
            faces += [tuple(len(verts) + i for i in poly) for poly in f]
            verts += v
    mesh_object("side_table_legs", verts, faces, [white], parent=root)
    return root
