"""木のスツール (reference/864-g01-2.jpg)。角柱の脚 4 本 + 座面 + 座面の下の幕板 + 脚の下のほうの貫。

全く同じ物が2つある: ソファーの北の `stool` と、本棚とデスク2の前に斜めに置いた `stool2` (2026-10-26 ユーザー指定)。
`stool2` の座面には、薄い丸い座布団 (LAKOLE のシートクッション。くすんだピンク) が乗っている (2026-10-27 ユーザー指定)。
位置・大きさは layout.py。ローカル座標: 原点 = 足元の中心 / 正面 = -Y / 幅は X
構成: Empty `stool` の下に、メッシュ `stool_body` (座面 / 脚・幕板・貫 の2色)。`stool2` も同じ + 座布団 `stool2_cushion`
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from layout import FURNITURE, rotation_deg

SEAT = "#E6C795"      # 座面 (明るいナチュラルな木)
FRAME = "#D9B67F"     # 脚・幕板・貫 (座面より少しだけ濃い)
CUSHION = "#C29894"   # 座布団 (くすんだピンク。ユーザー指定)
# 座布団の直径と真ん中の厚み: 座面 (0.37 角) の辺が隠れ、四隅だけ少しのぞく大きさ (ユーザー指定「座面がすべて隠れるか隠れないかくらい」)。
# 2026-10-27 ユーザー指定「もう少しだけ大きく、少し分厚く」で 0.42 → 0.45・2.2cm → 3cm
CUSHION_D, CUSHION_T = 0.45, 0.030


def _stool(name, seat, frame):
    e = FURNITURE[name]
    hx, hy, top = e["w"] / 2, e["d"] / 2, e["h"]
    root = add_empty(name, (e["x"], e["y"], e["z0"]), rotation_deg(e))

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
    boxes_object(f"{name}_body", boxes, parent=root)
    return root


def _cushion(root, e):
    """座面に乗せた薄い丸い座布団 (2026-10-27 ユーザー指定「LAKOLE のシートクッション。円形で、座面がすべて隠れるか隠れないかくらい。くすんだピンク」)。
    厚さ CUSHION_T の円盤で、縁は厚みの半分ほどの丸み (断面 profile。厚みに比例)。上面は真ん中が厚みの 1/7 ほどふくらみ、下の面は座面に押されて平ら。
    座面からはみ出した所 (辺の中ほど。4cm ほど) は、はみ出した長さに応じて下へ垂れる (厚いので垂れは小さく、一番はみ出した所で 1cm ほど)。縁の近くに浅いしわ。
    UV `UVMap` は上から見た位置 (1 = 1m)。焼き付けの島は上半分と下半分を1枚ずつ (断面に沿った長さで広げる。曲面を細かい島に分けると継ぎ目が見えるため)"""
    hx, hy, top = e["w"] / 2, e["d"] / 2, e["h"]
    R, t = CUSHION_D / 2, CUSHION_T
    ox, oy = 0.006, -0.008                # 手で置いたので、座面の真ん中から少しずれている
    na = 72                               # 1周の分割
    # 断面: (外周からの内側への距離, 高さ / 厚み)。上面の真ん中 → 丸い縁 → 下の面の真ん中。0.5 の所が縫い目 (上半分と下半分の境)
    flat = [R - (R - 1.36 * t) * k / 6 for k in range(6)]   # 平らな所の輪 (真ん中 → 丸い縁の手前)
    profile = ([(inset, 1.0) for inset in flat] +
               [(1.36 * t, 1.0), (0.73 * t, 0.97), (0.36 * t, 0.9), (0.14 * t, 0.76), (0.0, 0.5),
                (0.14 * t, 0.24), (0.36 * t, 0.1), (0.73 * t, 0.03), (1.36 * t, 0.0)] +
               [(inset, 0.0) for inset in reversed(flat)])
    seam = profile.index((0.0, 0.5))
    rng = random.Random(11)
    waves = [(rng.uniform(45, 95), rng.uniform(0, math.pi), rng.uniform(0, 6.3)) for _ in range(5)]

    def wr(x, y):                         # 縁の近くのしわ
        return sum(math.sin(k * (x * math.cos(a) + y * math.sin(a)) + ph) for k, a, ph in waves) / 5

    def droop(x, y):                      # 座面の外へはみ出した長さ d に応じて垂れる量
        d = math.hypot(max(0.0, abs(x) - hx), max(0.0, abs(y) - hy))
        return 0.1 * d + 3 * d * d

    # 断面に沿った長さ (焼き付けの島の半径): 上半分は上面の真ん中から、下半分は下面の真ん中から測る (縫い目の輪は両方の島の外周)
    pts = [(R - inset, f * t) for inset, f in profile]
    arc_top, arc_bottom = [0.0] * len(profile), [0.0] * len(profile)
    for k in range(1, seam + 1):
        arc_top[k] = arc_top[k - 1] + math.dist(pts[k], pts[k - 1])
    for k in range(len(profile) - 2, seam - 1, -1):
        arc_bottom[k] = arc_bottom[k + 1] + math.dist(pts[k], pts[k + 1])

    verts, rings = [], []
    for k, (inset, f) in enumerate(profile):
        r = R - inset
        ring = []
        for j in range(na if r > 1e-9 else 1):
            a = 2 * math.pi * j / na
            lx, ly = r * math.cos(a), r * math.sin(a)
            x, y = ox + lx, oy + ly
            edge = max(0.0, 1 - inset / 0.05)  # 縁から 5cm で 0 → 縁で 1
            dome = t / 7 * (1 - (r / R) ** 2) if f >= 1.0 else 0.0
            z = top + f * t + dome + 0.0015 * edge * wr(x, y) - droop(x, y)
            if f <= 0.0:
                z = top + 0.0005 - droop(x, y)   # 平らな下の面は座面から 0.5mm 浮かせる (焼き付けで面が重ならないように)
            ring.append(len(verts))
            verts.append((x, y, z))
        rings.append(ring)
    faces, upper = [], []
    for k in range(len(profile) - 1):
        a, b = rings[k], rings[k + 1]
        for j in range(na):
            jj = (j + 1) % na
            if len(a) == 1:
                faces.append((a[0], b[j], b[jj]))
            elif len(b) == 1:
                faces.append((a[jj], a[j], b[0]))
            else:
                faces.append((a[j], b[j], b[jj], a[jj]))
            upper.append(k < seam)
    obj = mesh_object(f"{root.name}_cushion", verts, faces, [fabric_material("stool_cushion", "cotton", CUSHION)], parent=root)
    ring_of = {vi: k for k, ring in enumerate(rings) for vi in ring}
    uv = obj.data.uv_layers.new(name="UVMap")
    seed = obj.data.uv_layers.new(name="lightmap_seed")
    for poly in obj.data.polygons:
        for li in poly.loop_indices:
            vi = obj.data.loops[li].vertex_index
            x, y, _ = verts[vi]
            uv.data[li].uv = (x, y)
            k = ring_of[vi]
            a = math.atan2(y - oy, x - ox)
            if upper[poly.index]:
                seed.data[li].uv = (arc_top[k] * math.cos(a), arc_top[k] * math.sin(a))
            else:
                seed.data[li].uv = (2.4 * R - arc_bottom[k] * math.cos(a), arc_bottom[k] * math.sin(a))
        poly.use_smooth = True
    obj["lightmap_uv"] = "lightmap_seed"   # bake.add_lightmap_uvs
    return obj


def build_stool():
    seat = wood_material("stool_seat", "light_soft", roughness=0.6, target=SEAT)
    frame = wood_material("stool_frame", "light_soft", roughness=0.6, target=FRAME)
    roots = [_stool(name, seat, frame) for name in ("stool", "stool2")]
    _cushion(roots[1], FURNITURE["stool2"])
    return roots
