"""カーテン (くすんだグレージュっぽい茶色の無地。ユーザー指定)。東壁の掃き出し窓に掛け、2枚とも閉めた状態 (ユーザー指定)。
レールはエアコンの下端の少し下 (layout.CURTAIN_ROD_Z。ユーザー指定)。金属 (アルミ) の角いレールで、中を走るランナーに布のフックを引っ掛ける
(2026-10-27 ユーザー指定「リングを通して吊るすものではなく、フックをひっかけるタイプ。カーテンとの距離はかなり近く、低い視点から見るとレールは見えない」)。
フックは A フック (布の上端がレールより上に出て、レールの前を隠す) にして、布の芯地の裏をレールの前の面の数 mm 前に吊るす。
座った目の高さからはレールは布に隠れて見えない。
布の上端は芯地の入った二つ山ヒダ (フックの所でつまんだ小さな山が2つ)。その下はフックの所が手前に出た縦のヒダになり、
裾へ行くほど深く、少し不揃いになる。布は織り目と糸のむらのある画像 (tools/make_textures.py の curtain_fabric)。

ローカル座標: 原点 = 床の上の足元の中心 / 正面 = -Y / X = 正面から見て右 (= 南) / 背面 (壁側) = +Y
構成: Empty `curtain` の下に、布 `curtain_cloth` (2枚を1つのメッシュに)・レール `curtain_rail` (下に溝・両端にキャップ)・壁の金具 `curtain_rail_brackets`・
ランナー `curtain_runners` とフック `curtain_hooks` (小さいのでライトマップはレールの光を借りる)
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
RAIL_W, RAIL_H = 0.020, 0.014      # レールの断面 (奥行・高さ)
RAIL_Y = 0.048                     # 壁からレールの中心まで (レールの前の面と布の芯地の裏は 3〜6mm)
RUNNER_Z = ROD_Z - RAIL_H / 2 - 0.005   # ランナーの下の輪 (フックを掛ける所) の高さ
Z_TOP = ROD_Z + 0.02               # 布の上端 (A フック: レールの上端より 1.3cm 上に出て、レールの前を隠す)
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
    """布1枚: フックの所 (山) が手前に出た縦のヒダ。(verts, faces, U = 布に沿った長さ, フックの (x, 芯地の y) の列)"""
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
    hooks = []   # フック (x, その所の芯地の y)。山 (つまんだ所) ごと。布の両端のフックは端から 1.5cm 内側 (横から見えないように)
    for k in range(pleats + 1):
        s = k + (0.015 / gap if k == 0 else -0.015 / gap if k == pleats else 0.0)
        hooks.append((x0 + gap * s, -(0.004 + 0.016 * math.exp(-((s - round(s)) / 0.09) ** 2)) + (0.003 if behind else 0.0)))
    return verts, faces, arc, hooks


def build_curtain():
    cloth_mat = make_material("curtain_cloth", "#FFFFFF", roughness=1.0, specular=0.12, double_sided=True,   # ヒダの間から裏が見える。ツヤはほぼ無し
                              texture="curtain_fabric_1k.jpg", texture_size=0.53)   # 無地 (織り目と糸のむらだけ)
    rail_mat = make_material("curtain_rail", "#C8CACC", roughness=0.35, metallic=0.6)   # アルミ
    cap_mat = make_material("curtain_rail_cap", "#D6D6D3", roughness=0.5)                # 両端のキャップ (樹脂)
    slot_mat = make_material("curtain_rail_slot", "#2B2B2D", roughness=0.7)              # 下の溝 (中の暗がり)
    runner_mat = make_material("curtain_runner", "#ECECE8", roughness=0.5)               # ランナー (白い樹脂)

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

    # レール: アルミの角いレール (下の面の中央に溝。両端に樹脂のキャップ) を、壁の金具3つで吊る。
    # 中のランナーの下の輪に、布の芯地の裏に差したフックを引っ掛ける。フックは布のつまんだ山 (hooks) の裏に差す
    wall = DEPTH / 2                       # 壁面のローカル y
    ry = wall - RAIL_Y                     # レールの中心
    e = WIDTH / 2                          # レールの端 = 布の端 (端のフックはレールの端のランナー。キャップだけ外に出る)
    z0, z1 = ROD_Z - RAIL_H / 2, ROD_Z + RAIL_H / 2
    boxes_object("curtain_rail", [
        (-e, e, ry - RAIL_W / 2, ry + RAIL_W / 2, z0, z1, rail_mat),
        (-e + 0.004, e - 0.004, ry - 0.003, ry + 0.003, z0 - 0.0006, z0 + 0.001, slot_mat, 0.0),
        (-e - 0.007, -e, ry - RAIL_W / 2 - 0.001, ry + RAIL_W / 2 + 0.001, z0 - 0.001, z1 + 0.001, cap_mat),
        (e, e + 0.007, ry - RAIL_W / 2 - 0.001, ry + RAIL_W / 2 + 0.001, z0 - 0.001, z1 + 0.001, cap_mat),
    ], parent=root, bevel=0.0015)
    brackets = []
    for x in (-0.85, 0.0, 0.85):           # 壁の板 + レールの上に掛かる腕
        brackets += [(x - 0.013, x + 0.013, wall - 0.004, wall, z0 - 0.006, z1 + 0.012, rail_mat),
                     (x - 0.009, x + 0.009, ry - RAIL_W / 2 + 0.002, wall - 0.004, z1, z1 + 0.006, rail_mat)]
    boxes_object("curtain_rail_brackets", brackets, parent=root, bevel=0.0015)
    runners = boxes_object("curtain_runners", [(x - 0.005, x + 0.005, ry - 0.005, ry + 0.005, RUNNER_Z - 0.003, ROD_Z, runner_mat)
                                               for x, _ in hooks], parent=root, bevel=0.0015)
    runners["lightmap_proxy"] = "curtain_rail"
    # フック: ランナーの輪から下へ → 前へ出て、芯地の裏 (布の 4mm 奥) を下へ
    paths = []
    for x, back in hooks:
        paths.append([(x, ry, RUNNER_Z + 0.002), (x, ry, RUNNER_Z - 0.006), (x, back + 0.004, RUNNER_Z - 0.016), (x, back + 0.004, RUNNER_Z - 0.045)])
    tubes_object("curtain_hooks", paths, 0.0015, rail_mat, parent=root, sides=5, light_from="curtain_rail")
    return root
