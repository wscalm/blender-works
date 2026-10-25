"""小物を作るためのヘルパー (本・回転体・管・回した直方体・絵の板・ワールド座標で置く物の親)。common.py の上に乗る。

使い方: from props import *   (common の関数も一緒に入る)
"""
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

# ---------------------------------------------------------------- 本
# 本の柄は1枚の画像 textures/books_atlas.jpg (tools/make_prints.py が描く) に並んでいる。
# 1冊分のマスは 64 x 512 px: 左 40 px = 背、右 24 px = 上から 表紙 (256) / 天 (128) / 小口 (128)。32 列 x 2 段 = 64 冊分
ATLAS_W, ATLAS_H = 2048, 1024
CELL_W, CELL_H, SPINE_W = 64, 512, 40
ATLAS_COLS = 32
BOOK_KINDS = {   # tools/make_prints.py の BOOK_KINDS と同じ
    "tech": range(0, 20), "dark": range(20, 28), "manga": range(28, 44), "bunko": range(44, 60), "misc": range(60, 64),
}


def book_material():
    """全ての本で共有する材質 (柄は UV で選ぶ)"""
    return bpy.data.materials.get("books") or make_material("books", "#FFFFFF", roughness=0.7, specular=0.35,
                                                             texture="books_atlas.jpg")


def _atlas_rect(i, part):
    """i 番目の本の part ('spine' | 'cover' | 'top' | 'edge') の UV の範囲 (u0, v0, u1, v1)。にじまないよう 2px 内側"""
    cx, cy = (i % ATLAS_COLS) * CELL_W, (i // ATLAS_COLS) * CELL_H
    x0, x1 = (cx, cx + SPINE_W) if part == "spine" else (cx + SPINE_W, cx + CELL_W)
    y0, y1 = {"spine": (0, 512), "cover": (0, 256), "top": (256, 384), "edge": (384, 512)}[part]
    p = 2
    return (x0 + p) / ATLAS_W, 1 - (cy + y1 - p) / ATLAS_H, (x1 - p) / ATLAS_W, 1 - (cy + y0 + p) / ATLAS_H


def book(design, t, d, h, matrix):
    """本1冊。ローカル座標: 厚み t = X (-t/2〜t/2)、奥行 d = Y (背 = -d/2、小口 = +d/2)、高さ h = Z (0〜h)。matrix で置く"""
    return dict(design=design, t=t, d=d, h=h, matrix=matrix)


def books_object(name, books, parent=None):
    """本の集まりを1つのメッシュにする。面ごとに柄の画像の 背・表紙・天・小口 を貼る (UV `UVMap` を自分で作る)"""
    verts, faces, uvs = [], [], []
    for b in books:
        t, d, h, m = b["t"], b["d"], b["h"], b["matrix"]
        base = len(verts)
        for iz in (0, 1):
            for iy in (0, 1):
                for ix in (0, 1):
                    verts.append(tuple(m @ Vector(((ix - 0.5) * t, (iy - 0.5) * d, iz * h))))

        def V(ix, iy, iz):
            return base + ix + 2 * iy + 4 * iz
        s, c, tp, e = (_atlas_rect(b["design"], p) for p in ("spine", "cover", "top", "edge"))
        quads = [   # (4 頂点 (外から見て反時計回り), 4 UV)
            ((V(0, 0, 0), V(1, 0, 0), V(1, 0, 1), V(0, 0, 1)), ((s[0], s[1]), (s[2], s[1]), (s[2], s[3]), (s[0], s[3]))),   # 背 (-Y)
            ((V(1, 1, 0), V(0, 1, 0), V(0, 1, 1), V(1, 1, 1)), ((e[0], e[1]), (e[2], e[1]), (e[2], e[3]), (e[0], e[3]))),   # 小口 (+Y)
            ((V(0, 1, 0), V(0, 0, 0), V(0, 0, 1), V(0, 1, 1)), ((c[0], c[1]), (c[2], c[1]), (c[2], c[3]), (c[0], c[3]))),   # 表紙 (-X)
            ((V(1, 0, 0), V(1, 1, 0), V(1, 1, 1), V(1, 0, 1)), ((c[0], c[1]), (c[2], c[1]), (c[2], c[3]), (c[0], c[3]))),   # 表紙 (+X)
            ((V(0, 0, 1), V(1, 0, 1), V(1, 1, 1), V(0, 1, 1)), ((tp[0], tp[3]), (tp[2], tp[3]), (tp[2], tp[1]), (tp[0], tp[1]))),   # 天 (背の側が縁)
            ((V(0, 0, 0), V(0, 1, 0), V(1, 1, 0), V(1, 0, 0)), ((tp[0], tp[3]), (tp[0], tp[1]), (tp[2], tp[1]), (tp[2], tp[3]))),   # 地
        ]
        for f, uv in quads:
            faces.append(f)
            uvs += uv
    obj = mesh_object(name, verts, faces, [book_material()], parent=parent)
    layer = obj.data.uv_layers.new(name="UVMap")
    for i, uv in enumerate(uvs):
        layer.data[i].uv = uv
    return obj


def book_row(rng, x0, x1, z, kinds, heights, thick=(0.012, 0.03), depth=(0.13, 0.16), y_front=None, y_back=None,
             fill=1.0, lean=True, max_h=None, gap=(0.0, 0.0015)):
    """棚の X 範囲 x0〜x1 に、背を -Y (手前) に向けた本を立てて並べる。z = 棚板の上面。
    y_front を渡すと背を手前に揃え (少しずつ奥へずらす)、y_back を渡すと奥に揃える。
    fill = 幅のどこまで詰めるか。lean = 最後に1冊、手前の本に寄りかかって傾いた本を置く。戻り値は book() の列"""
    pool = [i for k in kinds for i in BOOK_KINDS[k]]
    out, x = [], x0 + 0.002
    end = x0 + (x1 - x0) * fill
    last_h = 0.0
    while True:
        t = rng.uniform(*thick)
        h = rng.uniform(*heights)
        d = rng.uniform(*depth)
        if max_h:
            h = min(h, max_h)
        if x + t > end:
            break
        y = y_front + rng.uniform(0, 0.008) + d / 2 if y_front is not None else y_back - rng.uniform(0, 0.006) - d / 2
        out.append(book(rng.choice(pool), t, d, h, Matrix.Translation((x + t / 2, y, z))))
        x += t + rng.uniform(*gap)
        last_h = h
    if lean and x1 - x > 0.04:   # 寄りかかった本: 左下の角を軸に、上を手前の本 (-X) へ倒す
        t, d = rng.uniform(*thick), rng.uniform(*depth)
        h = min(rng.uniform(*heights), last_h + 0.03)
        th = math.radians(rng.uniform(9, 18))
        px = x + h * math.sin(th)
        if px + t * math.cos(th) < x1 - 0.002 and (not max_h or t * math.sin(th) + h * math.cos(th) < max_h):
            y = y_front + 0.004 + d / 2 if y_front is not None else y_back - 0.004 - d / 2
            m = Matrix.Translation((px, y, z)) @ Matrix.Rotation(-th, 4, 'Y') @ Matrix.Translation((t / 2, 0, 0))
            out.append(book(rng.choice(pool), t, d, h, m))
    return out


def book_stack(rng, cx, cy, z, kinds, sizes, thick=(0.012, 0.025), yaw=4.0):
    """平積みの本。sizes = [(高さ h, 奥行 d), ...] を下から。背は -Y (手前)。少しずつずらして回す"""
    pool = [i for k in kinds for i in BOOK_KINDS[k]]
    out = []
    for h, d in sizes:
        t = rng.uniform(*thick)
        m = (Matrix.Translation((cx + rng.uniform(-0.008, 0.008), cy + rng.uniform(-0.006, 0.006), z + t / 2))
             @ Matrix.Rotation(math.radians(rng.uniform(-yaw, yaw)), 4, 'Z')
             @ Matrix.Rotation(math.radians(90), 4, 'Y') @ Matrix.Translation((0, 0, -h / 2)))
        out.append(book(rng.choice(pool), t, d, h, m))
        z += t
    return out


# ---------------------------------------------------------------- 回転体・管
def lathe_object(name, profile, mats, parent=None, segments=32, location=(0, 0, 0), smooth=True, matrix=None):
    """断面 profile = [(半径 r, 高さ z, 材質の番号), ...] を Z 軸のまわりに回した物 (瓶・柱・脚・ボタンなど)。
    断面は 下の中心 (r=0) → 外側を上へ → 上の中心 (r=0) の順に並べると、面は全て外向きになる。
    k 番目と k+1 番目の点の間の帯は、k 番目の点の材質。matrix を渡すと、その変換で置く (location は無視)"""
    verts, faces, face_mats, rings = [], [], [], []
    for r, z, _ in profile:
        if r == 0:
            rings.append(None)
            verts.append((0.0, 0.0, z))
            rings[-1] = -(len(verts))   # 中心の点 (負の番号で印)
            continue
        rings.append(len(verts))
        for i in range(segments):
            a = 2 * math.pi * i / segments
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for k in range(len(profile) - 1):
        a, b, mi = rings[k], rings[k + 1], profile[k][2]
        for i in range(segments):
            j = (i + 1) % segments
            if a < 0:      # 下の中心から外へ
                faces.append((-a - 1, b + j, b + i))
            elif b < 0:    # 外から上の中心へ
                faces.append((a + i, a + j, -b - 1))
            else:
                faces.append((a + i, a + j, b + j, b + i))
            face_mats.append(mi)
    if matrix is not None:
        verts = [tuple(matrix @ Vector(v)) for v in verts]
    obj = mesh_object(name, verts, faces, mats, face_mats, parent=parent)
    if matrix is None:
        obj.location = location
    for p in obj.data.polygons:
        p.use_smooth = smooth
    return obj


def tube_mesh(path, radius, sides=8, closed=False):
    """折れ線 path [(x, y, z), ...] に沿った細い管 (針金・フック・カーテンのリング・コンセントの線)。(verts, faces) を返す。端は閉じない"""
    pts = [Vector(p) for p in path]
    n = len(pts)
    verts, faces = [], []
    prev_side = None
    for k, p in enumerate(pts):
        if closed:
            tan = (pts[(k + 1) % n] - pts[k - 1]).normalized()
        else:
            tan = (pts[min(k + 1, n - 1)] - pts[max(k - 1, 0)]).normalized()
        if prev_side is None:
            ref = Vector((0, 0, 1)) if abs(tan.z) < 0.9 else Vector((1, 0, 0))
            side = tan.cross(ref).normalized()
        else:   # ねじれないよう、前の向きを今の接線に直交させて使う
            side = (prev_side - tan * prev_side.dot(tan)).normalized()
        up = tan.cross(side)
        prev_side = side
        for i in range(sides):
            a = 2 * math.pi * i / sides
            verts.append(tuple(p + (side * math.cos(a) + up * math.sin(a)) * radius))
    segs = n if closed else n - 1
    for k in range(segs):
        k2 = (k + 1) % n
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((k * sides + i, k * sides + j, k2 * sides + j, k2 * sides + i))
    return verts, faces


def tubes_object(name, paths, radius, mat, parent=None, sides=8, closed=False, light_from=None):
    """複数の管を1つのメッシュにする。paths = [折れ線, ...]。closed=True なら全部輪にする。
    light_from: 細すぎてライトマップの島が潰れる管 (針金など) は、近くの物 (名前) の光を全体で借りる (bake.add_lightmap_uvs)"""
    verts, faces = [], []
    for path in paths:
        v, f = tube_mesh(path, radius, sides, closed)
        faces += [tuple(len(verts) + i for i in q) for q in f]
        verts += v
    obj = mesh_object(name, verts, faces, [mat], parent=parent)
    for p in obj.data.polygons:
        p.use_smooth = True
    if light_from:
        obj["lightmap_proxy"] = light_from
    return obj


def strap_mesh(path, width, thick, face_hint=(0, 1, 0)):
    """折れ線 path に沿った平たい帯 (かばんの持ち手)。帯の面は face_hint の向きを向く。(verts, faces) を返す"""
    pts = [Vector(p) for p in path]
    n = len(pts)
    hint = Vector(face_hint).normalized()
    verts, faces = [], []
    for k, p in enumerate(pts):
        tan = (pts[min(k + 1, n - 1)] - pts[max(k - 1, 0)]).normalized()
        w = hint.cross(tan).normalized() * (width / 2)
        nrm = tan.cross(w).normalized() * (thick / 2)
        verts += [tuple(p - w - nrm), tuple(p + w - nrm), tuple(p + w + nrm), tuple(p - w + nrm)]
    for k in range(n - 1):
        a, b = 4 * k, 4 * (k + 1)
        for i in range(4):
            j = (i + 1) % 4
            faces.append((a + i, a + j, b + j, b + i))
    return verts, faces


def bezier(p0, p1, p2, n=10):
    """2次のベジェ曲線の点の列 (p0 → p2。p1 の方へふくらむ)"""
    out = []
    for k in range(n + 1):
        t = k / n
        out.append(tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c for a, b, c in zip(p0, p1, p2)))
    return out


def circle(cx, cy, cz, r, n=48, axis="y"):
    """円の折れ線 (axis の軸に垂直な面内)。管の輪に使う"""
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        c, s = r * math.cos(a), r * math.sin(a)
        out.append((cx + c, cy, cz + s) if axis == "y" else (cx + c, cy + s, cz) if axis == "z" else (cx, cy + c, cz + s))
    return out


# ---------------------------------------------------------------- 枕・クッション
def pillow_object(name, w, d, t, mats, matrix, parent=None, n=22, flat_bottom=0.0, wrinkle=0.004, seed=0,
                  piping=0.0, uv_scale=1.0):
    """枕・クッション: 2枚の布の縁を縫い合わせて綿を詰めた形。縁は薄く真ん中が厚い。辺の中ほどは綿に引かれて内へ反り、角はとがる。
    縁の近くには縫い目へ寄るしわ (wrinkle m)。ローカル座標: 中心 = 原点、幅 w (X)・奥行 d (Y)・厚み t (Z、上下に t/2 ずつ)。matrix で置く。
    flat_bottom (0〜1): 下の面を平らにつぶす割合 (ベッドに置いた枕)。piping > 0 で縫い目に太さ piping (m) の玉縁 (mats[1]、無ければ mats[0])。
    UV `UVMap` は上から見た x, y に uv_scale を掛けた物 (縞の柄はこの向き)"""
    rng = random.Random(seed)
    waves = [(rng.uniform(55, 120), rng.uniform(0, math.pi), rng.uniform(0, 6.3)) for _ in range(5)]

    def wr(x, y):
        return sum(math.sin(k * (x * math.cos(a) + y * math.sin(a)) + ph) for k, a, ph in waves) / 5

    grid = [math.sin(math.pi / 2 * (-1 + 2 * i / n)) for i in range(n + 1)]   # 縁の近くほど細かい
    h = lambda s: max(0.0, 1 - abs(s) ** 2.5) ** 0.55                         # 縁で 0、真ん中で 1

    def xy(su, sv):
        return (su * w / 2 * (1 - 0.07 * (1 - sv * sv) * abs(su) ** 3),       # 辺の中ほどが内へ反る
                sv * d / 2 * (1 - 0.07 * (1 - su * su) * abs(sv) ** 3))

    verts, uvs, index = [], [], {}
    for side in (1, -1):   # 上の面、下の面 (縁の頂点は共有)
        for i, su in enumerate(grid):
            for j, sv in enumerate(grid):
                edge = i in (0, n) or j in (0, n)
                if side < 0 and edge:
                    index[(side, i, j)] = index[(1, i, j)]
                    continue
                x, y = xy(su, sv)
                f = h(su) * h(sv)
                if side < 0 and flat_bottom:
                    f = min(1.0, f * (1 + 3 * flat_bottom))
                z = side * (t / 2 * f + wrinkle * (1 - f) ** 1.5 * wr(x, y))
                index[(side, i, j)] = len(verts)
                verts.append(tuple(matrix @ Vector((x, y, z))))
                uvs.append((x * uv_scale, y * uv_scale))
    faces = []
    for i in range(n):
        for j in range(n):
            q = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
            faces.append(tuple(index[(1, *k)] for k in q))              # 上の面 (上から見て反時計回り)
            faces.append(tuple(index[(-1, *k)] for k in reversed(q)))   # 下の面
    face_mats = [0] * len(faces)
    if piping > 0:   # 縫い目を一周する玉縁
        ring = [(i, 0) for i in range(n)] + [(n, j) for j in range(n)] + [(i, n) for i in range(n, 0, -1)] + [(0, j) for j in range(n, 0, -1)]
        pv, pf = tube_mesh([Vector((*xy(grid[i], grid[j]), 0.0)) * (1 + piping / max(w, d)) for i, j in ring], piping, sides=6, closed=True)
        base = len(verts)
        verts += [tuple(matrix @ Vector(p)) for p in pv]
        uvs += [(p[0] * uv_scale, p[1] * uv_scale) for p in pv]
        faces += [tuple(base + k for k in q) for q in pf]
        face_mats += [min(1, len(mats) - 1)] * len(pf)
    obj = mesh_object(name, verts, faces, mats, face_mats, parent=parent)
    layer = obj.data.uv_layers.new(name="UVMap")
    for loop in obj.data.loops:
        layer.data[loop.index].uv = uvs[loop.vertex_index]
    if piping <= 0:   # 焼き付けの島 (bake.add_lightmap_uvs) は表と裏を1枚ずつ (曲面を細かい島に分けると、継ぎ目がまだらに見える)
        seed = obj.data.uv_layers.new(name="lightmap_seed")
        for poly in obj.data.polygons:
            top = poly.index % 2 == 0   # 面は 表・裏 の順に交互
            for li in poly.loop_indices:
                u, v = uvs[obj.data.loops[li].vertex_index]
                seed.data[li].uv = (u / uv_scale, v / uv_scale) if top else (1.1 * w - u / uv_scale, v / uv_scale)
        obj["lightmap_uv"] = "lightmap_seed"
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


# ---------------------------------------------------------------- 回した直方体・絵の板
def rot_box(x0, x1, y0, y1, z0, z1, mat, matrix, bevel=None):
    """軸に平行な直方体を matrix で回して置いた6面体 (solids_object に渡す形)。bevel を付けると面取りの幅"""
    pts = [tuple(matrix @ Vector(p)) for p in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                               (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    return (pts, mat) if bevel is None else (pts, mat, bevel)


def place(x, y, z, yaw=0.0, pitch=0.0, roll=0.0):
    """置く位置と向き: Z まわりに yaw 度 (上から見て反時計回り) → その前に X まわりに pitch 度 (+ で上が奥 (+Y) へ倒れる)・Y まわりに roll 度"""
    return (Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(yaw), 4, 'Z')
            @ Matrix.Rotation(math.radians(-pitch), 4, 'X') @ Matrix.Rotation(math.radians(roll), 4, 'Y'))


def image_quad(name, w, h, mat, matrix, parent=None):
    """画像を1枚貼った長方形 (絵・賞状・画面)。ローカル座標: X -w/2〜w/2、Z 0〜h、面は -Y を向く。UV は画像全体 (0〜1)"""
    pts = [(-w / 2, 0, 0), (w / 2, 0, 0), (w / 2, 0, h), (-w / 2, 0, h)]
    obj = mesh_object(name, [tuple(matrix @ Vector(p)) for p in pts], [(0, 1, 2, 3)], [mat], parent=parent)
    layer = obj.data.uv_layers.new(name="UVMap")
    for i, uv in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        layer.data[i].uv = uv
    return obj


def picture_material(name, image, roughness=0.6, specular=0.4):
    """絵・印刷物の材質 (画像を UV 0〜1 に1枚貼る)"""
    return make_material(name, "#FFFFFF", roughness=roughness, specular=specular, texture=image, texture_size=1.0)


def framed_picture(name, w, h, frame_w, mat_w, image, frame_color, matrix, parent=None, depth=0.02, mat_color="#F4F3EE"):
    """額に入った絵: 額縁 (4本) + 台紙 + 絵。ローカル座標: 額の外寸 X -w/2〜w/2、Z 0〜h、絵の面は -Y を向き、背面が y = 0"""
    frame = make_material(f"{name}_frame", frame_color, roughness=0.4)
    mount = make_material(f"{name}_mount", mat_color, roughness=0.8)
    hw = w / 2
    solids = [
        rot_box(-hw, hw, -depth, 0, 0, frame_w, frame, matrix),                    # 下
        rot_box(-hw, hw, -depth, 0, h - frame_w, h, frame, matrix),                # 上
        rot_box(-hw, -hw + frame_w, -depth, 0, frame_w, h - frame_w, frame, matrix),   # 左右
        rot_box(hw - frame_w, hw, -depth, 0, frame_w, h - frame_w, frame, matrix),
        rot_box(-hw + frame_w, hw - frame_w, -0.008, 0, frame_w, h - frame_w, mount, matrix),   # 台紙 (額の奥に)
    ]
    body = solids_object(f"{name}_frame", solids, parent=parent, bevel=0.002)
    iw, ih = w - 2 * (frame_w + mat_w), h - 2 * (frame_w + mat_w)
    pic = image_quad(f"{name}_image", iw, ih, picture_material(f"{name}_image", image),
                     matrix @ Matrix.Translation((0, -0.0085, frame_w + mat_w)), parent=parent)
    return body, pic


# ---------------------------------------------------------------- 置き方
def parent_keep(obj, parent):
    """今のワールド座標のまま parent の子にする"""
    bpy.context.view_layer.update()
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    return obj


def world_group(name, parent):
    """parent の子で、ワールド座標そのままの Empty (この下の物は部屋の座標で作れる。クリックすると parent の家具になる)"""
    g = add_empty(name)
    return parent_keep(g, parent)


def open_box(x0, x1, y0, y1, z0, z1, wall, mat, bottom=None):
    """上の開いた箱 (かご・ケース) の板5枚 (boxes_object に渡す形)"""
    b = bottom if bottom is not None else wall
    return [
        (x0, x1, y0, y1, z0, z0 + b, mat),
        (x0, x1, y0, y0 + wall, z0 + b, z1, mat), (x0, x1, y1 - wall, y1, z0 + b, z1, mat),
        (x0, x0 + wall, y0 + wall, y1 - wall, z0 + b, z1, mat), (x1 - wall, x1, y0 + wall, y1 - wall, z0 + b, z1, mat),
    ]


def set_planar_uvs(obj, axes=("x", "z"), scale=1.0):
    """テクスチャ用の UV を、ローカル座標の2軸の平面投影で作る (縞の向きを揃えたい物)"""
    ia = ["xyz".index(a) for a in axes]
    layer = obj.data.uv_layers.new(name="UVMap")
    for loop in obj.data.loops:
        co = obj.data.vertices[loop.vertex_index].co
        layer.data[loop.index].uv = (co[ia[0]] * scale, co[ia[1]] * scale)


FACE_OF_AXIS = {(0, -1): "left", (0, 1): "right", (1, -1): "front", (1, 1): "back", (2, -1): "bottom", (2, 1): "top"}


def atlas_box_uvs(obj, bounds, rects, size):
    """印刷のある箱: 面ごとに、1枚の画像の中の長方形を貼る UV `UVMap` を作る (どの面も外から見て正立)。
    bounds = 箱の (x0, x1, y0, y1, z0, z1) (メッシュの座標)。rects = {面: (左, 上, 右, 下)} (画像の画素。size = 画像の (幅, 高さ))。
    面は front (-Y) / back (+Y) / left (-X。正面から見て左) / right (+X) / top / bottom。rects に無い面は "plain" を貼る。
    面取りの面は近い方の面の端の色になる"""
    x0, x1, y0, y1, z0, z1 = bounds
    W, H = size
    me = obj.data
    layer = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        i = max(range(3), key=lambda k: abs(poly.normal[k]))
        face = FACE_OF_AXIS[(i, 1 if poly.normal[i] > 0 else -1)]
        px0, py0, px1, py1 = rects.get(face) or rects["plain"]
        for li in poly.loop_indices:
            x, y, z = me.vertices[me.loops[li].vertex_index].co
            u, v = {"front": ((x - x0) / (x1 - x0), (z - z0) / (z1 - z0)),
                    "back": ((x1 - x) / (x1 - x0), (z - z0) / (z1 - z0)),
                    "left": ((y1 - y) / (y1 - y0), (z - z0) / (z1 - z0)),
                    "right": ((y - y0) / (y1 - y0), (z - z0) / (z1 - z0)),
                    "top": ((x - x0) / (x1 - x0), (y - y0) / (y1 - y0)),
                    "bottom": ((x - x0) / (x1 - x0), (y1 - y) / (y1 - y0))}[face]
            u, v = min(1.0, max(0.0, u)), min(1.0, max(0.0, v))
            layer.data[li].uv = ((px0 + u * (px1 - px0)) / W, 1 - (py1 - v * (py1 - py0)) / H)


def smoothstep(t):
    """0〜1 へなめらかに変わる (t <= 0 で 0、t >= 1 で 1)"""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def folds(seed, amp, k=(18.0, 34.0), tilt=0.35, n=4):
    """布のたるみ (主に縦のひだ) の関数 f(u, z) を返す。u = 布に沿った横の位置、z = 高さ。値 = 布の面に垂直なずれ (最大 amp)。
    k = ひだの細かさ (rad/m)、tilt = ひだの傾き"""
    rng = random.Random(seed)
    waves = [(rng.uniform(*k), rng.uniform(-tilt, tilt), rng.uniform(0, 6.28), rng.uniform(0.5, 1.0)) for _ in range(n)]
    total = sum(w[3] for w in waves)
    return lambda u, z: amp * sum(a * math.sin(kk * (u + t * z) + ph) for kk, t, ph, a in waves) / total


def deform(obj, func):
    """メッシュの頂点をローカル座標で動かす。func((x, y, z)) -> (x, y, z)"""
    for v in obj.data.vertices:
        v.co = func(tuple(v.co))
    obj.data.update()
