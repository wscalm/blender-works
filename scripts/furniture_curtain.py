"""カーテン (くすんだグレージュっぽい茶色の無地。ユーザー指定)。東壁の掃き出し窓に掛け、2枚とも閉めた状態 (ユーザー指定)。
レールはエアコンの下端の少し下 (layout.CURTAIN_ROD_Z。ユーザー指定)。銀色の丸い棒に、リングとフックで吊るす (写真 reference/IMG_1100)。
布の上端は芯地の入った二つ山ヒダ (フックの所でつまんだ小さな山が2つ)。その下はフックの所が手前に出た縦のヒダになり、
裾へ行くほど深く、少し不揃いになる。布は織り目と糸のむらのある画像 (tools/make_textures.py の curtain_fabric)。

ローカル座標: 原点 = 床の上の足元の中心 / 正面 = -Y / X = 正面から見て右 (= 南) / 背面 (壁側) = +Y
構成: Empty `curtain` の下に、布 `curtain_cloth` (2枚を1つのメッシュに)・銀色のレール `curtain_rod` `curtain_rod_brackets`・
リングとフック `curtain_rings` `curtain_hooks` (細いのでライトマップはレールの光を借りる)
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props import *
from layout import CURTAIN_ROD_Z, FURNITURE
from room_spec import *

C = FURNITURE["curtain"]
WIDTH = C["w"]          # レールの幅。窓 (1.8m) の両側に 10cm ずつ余らせる。エアコン (Y 2.65〜) には触れない
DEPTH = C["d"]          # 壁からの出
ROD_Z = CURTAIN_ROD_Z   # レールの中心の高さ
RING_R, WIRE = 0.019, 0.0025       # リングの半径 / 針金の太さ
Z_TOP = ROD_Z - RING_R - 0.016     # 布の上端 (リングの下にフック 1.6cm)
Z_BOTTOM = 0.015        # 裾 (床から 1.5cm)
HEAD = 0.075            # 上の芯地 (二つ山ヒダ) の高さ
FOLD = 0.045            # 芯地のすぐ下のヒダの深さ (山と谷の差)
FLARE = 1.3             # 裾でのヒダの深さの倍率
# フック (山) から次のフックまでの横の分け方 (0〜1)。つまんだ所 (フックの近く) は細かく
S_STEPS = (0.0, 0.025, 0.05, 0.08, 0.13, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.87, 0.92, 0.95, 0.975)
ROWS = 18               # 芯地の 7cm 下より下の縦の分割
# 布2枚 (閉めた状態): 布の左端・右端 (ローカル x)、ヒダ (フックの間) の数、形の seed、合わせ目の側 (+1 = 右端)、合わせ目で奥になるか。
# 合わせ目 (x = 0) では 8mm 重ねる (すき間から窓が見えないように)
PANELS = [(-WIDTH / 2, 0.004, 8, 11, +1, False), (-0.004, WIDTH / 2, 8, 23, -1, True)]


def _panel(x0, x1, pleats, seed, lead, behind):
    """布1枚: フックの所 (山) が手前に出た縦のヒダ。(verts, faces, U = 布に沿った長さ, フックの x の列)"""
    rng = random.Random(seed)
    amp = [rng.uniform(0.75, 1.25) for _ in range(pleats + 1)]       # 山ごとの深さの違い
    drift = [rng.uniform(-0.018, 0.018) for _ in range(pleats + 1)]  # 裾での山の横のずれ
    drift[0] = drift[-1] = 0.0   # 両端 (壁際と合わせ目) は動かさない
    amp[0 if lead < 0 else -1] = 0.8 if behind else 1.2   # 合わせ目: 北の布の端が手前、南の布の端はその奥に重なる
    gap = (x1 - x0) / pleats

    def between(vals, s):   # 山ごとの値を、山と山の間でなめらかにつなぐ
        k = min(int(s), pleats - 1)
        w = 0.5 - 0.5 * math.cos(math.pi * (s - k))
        return vals[k] * (1 - w) + vals[k + 1] * w

    ss = [k + s for k in range(pleats) for s in S_STEPS] + [float(pleats)]
    zs = ([Z_BOTTOM + (Z_TOP - 0.14 - Z_BOTTOM) * r / ROWS for r in range(ROWS)] +   # 上の 14cm (芯地とその下の移り目) は細かく
          [Z_TOP - 0.14 + 0.14 * r / 9 for r in range(10)])
    verts, arc = [], []
    for z in zs:
        t = (z - Z_BOTTOM) / (Z_TOP - Z_BOTTOM)                   # 0 = 裾, 1 = 上端
        head = smoothstep((z - (Z_TOP - HEAD - 0.05)) / 0.06)     # 芯地の形へ移る割合
        sway = max(0.0, 1 - t) ** 1.5
        length = 0.0
        for i, s in enumerate(ss):
            body = FOLD * (FLARE - (FLARE - 1) * t) * between(amp, s) * (0.5 + 0.5 * math.cos(2 * math.pi * s))
            pinch = 0.004 + 0.016 * math.exp(-((s - round(s)) / 0.09) ** 2)   # 芯地: 平らで、フックの所だけつまんだ山が出る
            y = -((1 - head) * body + head * pinch) + (0.003 * head if behind else 0.0)   # 重なる芯地どうしがぶつからないよう奥へ
            v = (x0 + gap * s + sway * between(drift, s), y, z)
            if i:
                length += math.dist(v, verts[-1])
            verts.append(v)
            arc.append(length)   # テクスチャ用の U = 布に沿った長さ (箱の投影だとヒダの斜面で模様が潰れる)
    n = len(ss)
    faces = [(r * n + i, r * n + i + 1, (r + 1) * n + i + 1, (r + 1) * n + i)
             for r in range(len(zs) - 1) for i in range(n - 1)]
    return verts, faces, arc, [x0 + gap * k for k in range(pleats + 1)]


def build_curtain():
    cloth_mat = make_material("curtain_cloth", "#FFFFFF", roughness=1.0, specular=0.12, double_sided=True,   # ヒダの間から裏が見える。ツヤはほぼ無し
                              texture="curtain_fabric_1k.jpg", texture_size=0.53)   # 無地 (織り目と糸のむらだけ)
    rod_mat = make_material("curtain_rod", "#C8CACC", roughness=0.35, metallic=0.6)

    root = add_empty("curtain", (C["x"], C["y"], C["z0"]), FACING_DEG[C["facing"]])

    verts, faces, uvs, seeds, hooks = [], [], [], [], []
    for k, panel in enumerate(PANELS):
        v, f, u, h = _panel(*panel)
        faces += [tuple(len(verts) + i for i in q) for q in f]
        uvs += [(a + 0.31 * k, p[2]) for a, p in zip(u, v)]   # 2枚の模様をずらす
        seeds += [(a + 2.0 * k, p[2]) for a, p in zip(u, v)]   # ライトマップの島: 1枚を1つの島に (2枚は重ならないよう離す)
        verts += v
        hooks += h
    cloth = mesh_object("curtain_cloth", verts, faces, [cloth_mat], parent=root)
    for name, values in (("UVMap", uvs), ("lightmap_seed", seeds)):
        uv = cloth.data.uv_layers.new(name=name)
        for loop in cloth.data.loops:
            uv.data[loop.index].uv = values[loop.vertex_index]
    cloth["lightmap_uv"] = "lightmap_seed"   # bake.add_lightmap_uvs
    for poly in cloth.data.polygons:
        poly.use_smooth = True

    # レール: 銀色の丸い棒 (両端に玉) + 壁への留め具2つ (リングの間)。リングは棒を囲み、フックで布の芯地の裏へ
    wall = DEPTH / 2                       # 壁面のローカル y
    ry = wall - 0.08                       # 棒の中心 (壁から 8cm)
    e = WIDTH / 2
    lathe_object("curtain_rod", [(0, -e - 0.055, 0), (0.012, -e - 0.05, 0), (0.02, -e - 0.04, 0), (0.02, -e - 0.02, 0), (0.012, -e - 0.015, 0),
                                 (0.012, e + 0.015, 0), (0.02, e + 0.02, 0), (0.02, e + 0.04, 0), (0.012, e + 0.05, 0), (0, e + 0.055, 0)],
                 [rod_mat], parent=root, segments=16,
                 matrix=Matrix.Translation((0, ry, ROD_Z)) @ Matrix.Rotation(math.radians(90), 4, 'Y'))
    bx = 0.8125                            # 留め具 (フックとフックの間)
    boxes_object("curtain_rod_brackets", [(x - 0.01, x + 0.01, ry, wall, ROD_Z - 0.008, ROD_Z + 0.008, rod_mat) for x in (-bx, bx)],
                 parent=root, bevel=0.002)
    tubes_object("curtain_rings", [circle(x, ry, ROD_Z, RING_R, n=16, axis="x") for x in hooks], WIRE, rod_mat,
                 parent=root, sides=5, closed=True, light_from="curtain_rod")
    tubes_object("curtain_hooks", [[(x, ry, ROD_Z - RING_R), (x, ry + 0.006, Z_TOP + 0.006), (x, -0.004, Z_TOP - 0.02)] for x in hooks],
                 0.0015, rod_mat, parent=root, sides=5, light_from="curtain_rod")
    return root
