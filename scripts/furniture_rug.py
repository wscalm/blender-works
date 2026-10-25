"""ラグ (写真 reference/IMG_1100: ベージュのキルトに、茶色の犬・灰色の猫の絵と筆記体の字。角は丸く、縁は薄茶の縁取り)。
ソファーの前に、ソファーと同じ大きさで敷く。

位置・大きさは layout.py (rug)。ローカル座標: 原点 = 中心の床 / 幅は X (ソファーの幅の向き) / -Y = ソファーの側
柄はラグ全体で1枚の画像 textures/rug_print.jpg (tools/make_prints.py の make_rug。大きさを変えたら画像も作り直す)。
縁は厚みの半分ほどの丸みでふっくらさせる。構成: Empty `rug` の下に `rug_body`
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from layout import FURNITURE

CORNER_R = 0.08   # 角の丸み (tools/make_prints.py の RUG_CORNER と同じ)
ARC = 10          # 角1つの円弧の分割数
# 縁の断面: (外周からの内側への距離, 高さ / 厚み)。上面の平らな所 → 丸い縁 → 床
EDGE = [(0.012, 1.0), (0.005, 0.97), (0.002, 0.86), (0.0, 0.55), (0.0015, 0.18), (0.004, 0.0)]


def _outline(hx, hy, r, inset):
    """角の丸い長方形の周 (反時計回り)。inset だけ内側へ寄せる"""
    pts = []
    for cx, cy, a0 in ((hx - r, -hy + r, -90), (hx - r, hy - r, 0), (-hx + r, hy - r, 90), (-hx + r, -hy + r, 180)):
        for k in range(ARC + 1):
            a = math.radians(a0 + 90 * k / ARC)
            pts.append((cx + (r - inset) * math.cos(a), cy + (r - inset) * math.sin(a)))
    return pts


def build_rug():
    e = FURNITURE["rug"]
    hx, hy, h = e["w"] / 2, e["d"] / 2, e["h"]
    root = add_empty("rug", (e["x"], e["y"], e["z0"]), FACING_DEG[e["facing"]])
    rings = [[(x, y, h * zf) for x, y in _outline(hx, hy, CORNER_R, inset)] for inset, zf in EDGE]
    n = len(rings[0])
    verts = [v for ring in rings for v in ring]
    faces = [tuple(range(n))]   # 上面 (平ら)
    for r in range(len(rings) - 1):
        faces += [(r * n + i, (r + 1) * n + i, (r + 1) * n + (i + 1) % n, r * n + (i + 1) % n) for i in range(n)]
    mat = make_material("rug", "#FFFFFF", roughness=1.0, specular=0.2, texture="rug_print.jpg", texture_size=1.0)
    obj = mesh_object("rug_body", verts, faces, [mat], parent=root)
    layer = obj.data.uv_layers.new(name="UVMap")   # 上から見た位置 → 画像 (ラグ全体で 0〜1)
    for loop in obj.data.loops:
        x, y, _ = obj.data.vertices[loop.vertex_index].co
        layer.data[loop.index].uv = ((x + hx) / (2 * hx), (y + hy) / (2 * hy))
    for p in obj.data.polygons[1:]:   # 縁だけなめらかに (上面は平ら)
        p.use_smooth = True
    return root
