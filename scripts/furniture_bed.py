"""ダブルベッド (ダークブラウンの土台とヘッドボード、土台と同じ大きさのくすんだピンクの厚いマットレス、グレーのタオル地の敷きパッド、ネイビーの枕、黒い毛布の塊)。

位置・大きさは layout.py。ローカル座標: 原点 = ベッドの中心の床 / 正面 = -Y (足元側) / 背面 = +Y (ヘッドボード側)
構成: Empty `bed` の下に、`bed_frame` (土台・脚。ウォールナットの木目を暗くする) と `bed_headboard` (木目を薄くした画像。ユーザー指定)、
`bed_bedding` (マットレス。土台と同じ幅と長さで、土台の上面は隠れて見えない (ユーザー指定))・
`bed_cover` (敷きパッド: マットレスの上に掛けたグレーのタオル地。キルティングの縫い目が薄く見える (ユーザー指定))、
`bed_pillow` (枕。props.pillow_object)、`bed_blanket` (毛布)。
毛布は黒のフリースで「無造作に、少し高さが出るくらい塊になっている」(ユーザー指定) ので、Blender の布のシミュレーションで、
広げた布をベッドの上でたぐり寄せて形を作る (_messy_blanket)
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props import *
from layout import BED_TOP, FURNITURE

INSET = "#5E4231"       # ヘッドボードの化粧パネル (フレームより少し明るい茶)
MATTRESS = "#C49A96"    # くすんだピンク (ユーザー指定)
COVER = "#A3A3A1"       # 敷きパッド (グレー。ユーザー指定。タオル地にキルティング = common.FABRIC["towel"])
PILLOW = "#2C3A55"      # 枕カバー (ネイビー。ユーザー指定)
# 毛布: 黒のフリース (ユーザー指定)。tools/make_textures.py の blanket_fleece
BLANKET = dict(texture="blanket_fleece_1k.jpg", texture_size=0.55)
MATTRESS_TOP = BED_TOP - 0.01   # マットレス本体の上面 (この上に厚さ 1cm 分の敷きパッド)
MATTRESS_BOTTOM = 0.32          # マットレスの下面 = 土台の上面 (厚さ 0.24。ユーザー指定「厚め」)


def build_bed():
    e = FURNITURE["bed"]
    hx, hy, top = e["w"] / 2, e["d"] / 2, e["h"]
    root = add_empty("bed", (e["x"], e["y"], e["z0"]), FACING_DEG[e["facing"]])

    dark = wood_material("bed_frame", "walnut", roughness=0.5, target=DARK_BROWN)
    head = wood_material("bed_headboard", "walnut_soft", roughness=0.5, target=DARK_BROWN)
    inset = wood_material("bed_headboard_inset", "walnut_soft", roughness=0.5, target=INSET)

    hb, post = 0.08, 0.07      # ヘッドボードの厚み / 脚柱の太さ
    yb = hy - hb               # ヘッドボードの前面
    boxes_object("bed_headboard", [   # 脚柱2本 + 板 + 笠木 + 化粧パネル
        (-hx, -hx + post, yb, hy, 0, top, head),
        (hx - post, hx, yb, hy, 0, top, head),
        (-hx + post, hx - post, yb, hy, 0.22, top - 0.05, head),
        (-hx, hx, yb - 0.005, hy, top - 0.05, top, head),
        (-hx + 0.14, hx - 0.14, yb - 0.012, yb, 0.36, top - 0.17, inset),
    ], parent=root)
    boxes_object("bed_frame", [       # 土台: 側板2枚 + 足元の板 + 床板 + 足元の脚2本。上面はマットレスの下面で、マットレスに隠れる
        (-hx, -hx + 0.06, -hy, yb, 0.18, MATTRESS_BOTTOM, dark),
        (hx - 0.06, hx, -hy, yb, 0.18, MATTRESS_BOTTOM, dark),
        (-hx, hx, -hy, -hy + 0.06, 0.18, MATTRESS_BOTTOM, dark),
        (-hx + 0.06, hx - 0.06, -hy + 0.06, yb, 0.24, MATTRESS_BOTTOM, dark),
        (-hx, -hx + post, -hy, -hy + post, 0, 0.18, dark),
        (hx - post, hx, -hy, -hy + post, 0, 0.18, dark),
    ], parent=root)

    # マットレス: 土台と同じ幅と長さで、土台の上に乗る (土台の上面は見えない。ユーザー指定)。厚さ 0.24
    # 敷きパッドは上面と、側面の上の 3cm だけを覆う (マットレスのピンクが側面に見える)。縁は丸く、上面に浅いしわ
    mw = hx                    # マットレスの半幅 = 土台の半幅
    m0, m1 = -hy, yb - 0.003   # 足元の端 = 土台の足元の端 / 頭の端 = ヘッドボードの前
    soft_boxes_object("bed_bedding", [
        (-mw, mw, m0, m1, MATTRESS_BOTTOM, MATTRESS_TOP, fabric_material("bed_mattress", "cotton", MATTRESS), 0.04, (0.003, 0.003, 0.0)),
    ], parent=root, cuts=12)
    soft_boxes_object("bed_cover", [
        (-mw - 0.004, mw + 0.004, m0 - 0.004, m1, MATTRESS_TOP - 0.03, BED_TOP, fabric_material("bed_cover", "towel", COVER), 0.02, (0.0, 0.0, 0.0)),
    ], parent=root, cuts=24, wrinkle=0.003, wrinkle_size=0.5, seed=7)
    # 枕1つ (頭側の中央): 2枚の布を縫い合わせた形。下の面はベッドに押されて平ら
    pillow_object("bed_pillow", 0.66, 0.40, 0.11, [fabric_material("bed_pillow", "cotton", PILLOW)],
                  Matrix.Translation((0.0, 0.76, BED_TOP + 0.05)) @ Matrix.Rotation(math.radians(3), 4, 'Z'),
                  parent=root, flat_bottom=0.8, wrinkle=0.005, seed=5)

    colliders = [bpy.data.objects[n] for n in ("bed_bedding", "bed_cover", "bed_pillow", "bed_frame", "bed_headboard", "room_floor")
                 if n in bpy.data.objects]
    _messy_blanket(root, make_material("bed_blanket", "#FFFFFF", roughness=1.0, specular=0.3, **BLANKET), colliders, hx, hy)
    return root


BLANKET_W, BLANKET_L = 1.50, 1.90   # 毛布の大きさ
SPACING = 0.03                      # 布の格子の間隔
FRAMES = 80                         # シミュレーションのフレーム数 (24fps で 3.3 秒。落ちて、引き寄せられて塊になる)
SMOOTH_ITER, SUBDIV, DECIMATE = 1, 1, 0.5   # 落とした後のならし (回数)・細分 (段数)・面を減らす割合
BLANKET_CENTER, BLANKET_YAW = (-0.05, -0.30), -20.0   # 広げた毛布を置く中心 (ベッドのローカル座標) と向き (度)
DROP = 0.05                         # 広げた毛布を置く高さ (ベッドの上面から)
FRICTION = 4.0                      # ベッドと布の摩擦 (大きいと布が滑らず、寄らない)
# たぐり寄せ: 布の各点を、広げた位置から「寄せた位置」へ弱いばねで引っ張る (布の pin の目標を形のキーで動かす)。
# 寄せた位置 = 中心 GATHER (ベッドのローカル座標) のまわりに、向き GATHER_ANGLE の軸に沿って (kx, ky) 倍に縮め、真ん中ほど高い山 (高さ GATHER_H)
GATHER, GATHER_ANGLE, GATHER_K, GATHER_H = (-0.08, -0.36), 15.0, (0.50, 0.26), 0.26
GATHER_FRAMES = 40                  # 寄せ終わるまでのフレーム数 (そのあと FRAMES まで落ち着かせる)
PIN_WEIGHT, PIN_STIFFNESS = (0.08, 0.20), 3.0   # ばねの強さ (真ん中・縁。縁を少し強く引く。縁が強すぎると縁がフリルのように縮れる)
BENDING = 30.0                      # 曲げにくさ (厚いフリース。小さいと紙を丸めたような細かいしわになる)


def _messy_blanket(root, mat, colliders, hx, hy):
    """毛布: 平らな布をベッドの上で、一点のまわりへたぐり寄せて落とし、無造作な塊にする (ユーザー指定「少し高さが出るくらい塊」)。

    布の各点を、広げた位置から寄せた位置 (縮めた布の山) へ弱いばねで引っ張る (布の pin の目標を形のキーで動かす)。
    布の長さは元のままなので、余った分が大きなしわになって重なり、高さ 約 25cm の塊になる。
    東の端はソファーの背に当たらないよう、ベッドの東端より内側。結果は毎回同じ
    (力場で引き寄せる方法は布のかたさに負けてほとんど動かず、見えない山にかぶせる方法は中が空の布に見えたので、この方法にした)
    """
    nu, nv = round(BLANKET_W / SPACING), round(BLANKET_L / SPACING)
    du, dv = BLANKET_W / nu, BLANKET_L / nv
    yaw = math.radians(BLANKET_YAW)
    cx, cy = BLANKET_CENTER
    gx, gy = GATHER
    ga = math.radians(GATHER_ANGLE)
    ca, sa = math.cos(ga), math.sin(ga)
    kx, ky = GATHER_K
    local, goal, uvs, weights = [], [], [], []
    for i in range(nu + 1):
        for j in range(nv + 1):
            u, v = i * du, j * dv
            x, y = u - BLANKET_W / 2, v - BLANKET_L / 2
            z = 0.012 * math.sin(7.0 * u + 2.0 * v) + 0.01 * math.sin(3.0 * v - 5.0 * u + 1.0)   # 少しのうねり (対称に縮まないように)
            x, y = cx + x * math.cos(yaw) - y * math.sin(yaw), cy + x * math.sin(yaw) + y * math.cos(yaw)
            local.append((x, y, BED_TOP + DROP + z))
            # 寄せた位置: GATHER のまわりで、傾けた軸に沿って縮める + 少しのゆがみ
            dx, dy = x - gx, y - gy
            a1, a2 = dx * ca + dy * sa, -dx * sa + dy * ca
            a1, a2 = a1 * kx + 0.04 * math.sin(4.0 * a2 + 1.3), a2 * ky + 0.04 * math.sin(3.0 * a1 - 0.7)
            px, py = gx + a1 * ca - a2 * sa, gy + a1 * sa + a2 * ca
            rho2 = (a1 / (kx * 0.8)) ** 2 + (a2 / (ky * 1.0)) ** 2
            goal.append((px, py, BED_TOP + 0.02 + GATHER_H * max(0.0, 1 - rho2)))
            uvs.append((u, v))
            edge = min(u, v, BLANKET_W - u, BLANKET_L - v)
            t = max(0.0, 1 - edge / 0.25)                     # 縁から 25cm で 1 → 0
            weights.append(PIN_WEIGHT[0] + (PIN_WEIGHT[1] - PIN_WEIGHT[0]) * t)
    xs, ys = [p[0] for p in goal], [p[1] for p in goal]
    print(f"BLANKET GOAL: x {min(xs):.2f}〜{max(xs):.2f}  y {min(ys):.2f}〜{max(ys):.2f}  (bed half {hx:.2f} x {hy:.2f})")

    bpy.context.view_layer.update()
    faces = [(i * (nv + 1) + j, (i + 1) * (nv + 1) + j, (i + 1) * (nv + 1) + j + 1, i * (nv + 1) + j + 1)
             for i in range(nu) for j in range(nv)]
    world = root.matrix_world
    obj = mesh_object("bed_blanket", [world @ Vector(p) for p in local], faces, [mat])
    mesh = obj.data
    uv = mesh.uv_layers.new(name="UVMap")   # テクスチャは布の上の長さで貼る (1 = 1m)
    for loop in mesh.loops:
        uv.data[loop.index].uv = uvs[loop.vertex_index]
    obj.shape_key_add(name="Basis")
    key = obj.shape_key_add(name="gather", from_mix=False)
    for k, p in enumerate(goal):
        key.data[k].co = obj.matrix_world.inverted() @ (world @ Vector(p))
    key.value = 0.0
    key.keyframe_insert("value", frame=1)
    key.value = 1.0
    key.keyframe_insert("value", frame=GATHER_FRAMES)
    group = obj.vertex_groups.new(name="pin")
    for k, w in enumerate(weights):
        group.add([k], w, 'REPLACE')
    cloth = obj.modifiers.new("cloth", 'CLOTH')
    st = cloth.settings
    st.quality = 10
    st.mass = 0.25
    st.air_damping = 2.0
    st.tension_stiffness = st.compression_stiffness = 15
    st.shear_stiffness = 5
    st.bending_stiffness = BENDING
    st.vertex_group_mass = "pin"         # たぐり寄せのばね (形のキー gather へ引っ張る)
    st.pin_stiffness = PIN_STIFFNESS
    cs = cloth.collision_settings
    cs.collision_quality = 5
    cs.distance_min = 0.003
    cs.use_self_collision = True
    cs.self_distance_min = 0.003
    cloth.point_cache.frame_start, cloth.point_cache.frame_end = 1, FRAMES
    for o in colliders:
        o.modifiers.new("collision", 'COLLISION')
        o.collision.thickness_outer = 0.003
        o.collision.cloth_friction = FRICTION

    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, FRAMES
    for f in range(1, FRAMES + 1):
        scene.frame_set(f)
    _bake_modifiers(obj)
    for o in colliders:
        for m in [m for m in o.modifiers if m.type == 'COLLISION']:
            o.modifiers.remove(m)
    obj.vertex_groups.clear()
    _despike(obj)
    scene.frame_set(1)

    # 3cm の格子の折れ目が角張って見えるので、少しならしてから1回細分してなめらかにし、平らな所の面を減らす (しわの所は残る)
    smooth = obj.modifiers.new("smooth", 'SMOOTH')
    smooth.factor, smooth.iterations = 0.5, SMOOTH_ITER
    subdiv = obj.modifiers.new("subdiv", 'SUBSURF')
    subdiv.levels = subdiv.render_levels = SUBDIV
    if DECIMATE < 1:
        obj.modifiers.new("decimate", 'DECIMATE').ratio = DECIMATE
    _bake_modifiers(obj)
    # 厚み 7mm (上へ)。上の面と縁は別の材質の枠に分けておき (ライトマップの展開を分けるため)、展開を作ったら1つに戻す
    n = len(obj.data.vertices)
    obj.data.materials.append(mat)
    obj.data.materials.append(mat)
    solid = obj.modifiers.new("solid", 'SOLIDIFY')
    solid.thickness, solid.offset = 0.007, 1.0
    solid.use_even_offset = solid.use_quality_normals = True
    solid.material_offset, solid.material_offset_rim = 1, 2
    _bake_modifiers(obj)
    _lightmap_seed(obj, n)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj.parent = root
    obj.matrix_parent_inverse = root.matrix_world.inverted()
    zs = [v.co.z for v in obj.data.vertices]
    print(f"BLANKET: {len(zs)} verts, z {min(zs):.3f}〜{max(zs):.3f}")
    to_bed = root.matrix_world.inverted()   # 毛布の頂点は部屋の座標
    xs = [(to_bed @ v.co).x for v in obj.data.vertices]
    ys = [(to_bed @ v.co).y for v in obj.data.vertices]
    print(f"BLANKET (bed local): x {min(xs):.2f}〜{max(xs):.2f}  y {min(ys):.2f}〜{max(ys):.2f}")
    if max(xs) > hx - 0.03:   # ソファーの背 (ベッドの東端) に当たる
        print(f"WARNING: blanket reaches the sofa side (x {max(xs):.3f} > {hx - 0.03:.3f})")
    return obj


def _lightmap_seed(obj, n):
    """毛布のライトマップの島の元 (bake.add_lightmap_uvs が使う): 下の面 (元の布、頂点 0〜n-1) は布の展開 UVMap のまま、
    上の面 (頂点 n〜) は横へずらし、縁は下の面の島の外周の外へ厚みの分だけ細く付ける。曲面を細かい島に分けると継ぎ目が見えるため"""
    mesh = obj.data
    uv = mesh.uv_layers["UVMap"].data
    seed = mesh.uv_layers.new(name="lightmap_seed").data
    base = {}   # 元の布の頂点 → UV
    for p in mesh.polygons:
        if p.material_index == 0:
            for li in p.loop_indices:
                base[mesh.loops[li].vertex_index] = Vector(uv[li].uv)

    def outward(t):   # 布の展開の外周 (0〜BLANKET_W, 0〜BLANKET_L) のうち一番近い辺の外向き
        return min(((t.x, (-1, 0)), (BLANKET_W - t.x, (1, 0)), (t.y, (0, -1)), (BLANKET_L - t.y, (0, 1))))[1]
    for p in mesh.polygons:
        for li in p.loop_indices:
            vi = mesh.loops[li].vertex_index
            if p.material_index == 0:
                seed[li].uv = uv[li].uv
            elif p.material_index == 1:
                seed[li].uv = (uv[li].uv[0] + BLANKET_W + 0.3, uv[li].uv[1])
            else:
                t = base[vi if vi < n else vi - n]
                seed[li].uv = t if vi < n else t + Vector(outward(t)) * 0.007
        p.material_index = 0
    while len(mesh.materials) > 1:
        mesh.materials.pop()
    obj["lightmap_uv"] = "lightmap_seed"
    gap = [(mesh.vertices[i + n].co - mesh.vertices[i].co).length for i in range(0, n, max(1, n // 50))]
    print(f"BLANKET SHELL: n={n}, verts={len(mesh.vertices)}, thickness {min(gap):.4f}〜{max(gap):.4f}")


def _despike(obj, limit=0.03, rounds=3):
    """布のシミュレーションで飛び出した点 (まわりの点の平均から limit 以上離れた点) を、まわりの平均に戻す"""
    mesh = obj.data
    nbr = [[] for _ in mesh.vertices]
    for e in mesh.edges:
        a, b = e.vertices
        nbr[a].append(b)
        nbr[b].append(a)
    fixed = 0
    for _ in range(rounds):
        cos = [v.co.copy() for v in mesh.vertices]
        for i, ns in enumerate(nbr):
            if ns:
                avg = sum((cos[n] for n in ns), Vector()) / len(ns)
                if (cos[i] - avg).length > limit:
                    mesh.vertices[i].co = avg
                    fixed += 1
    mesh.update()
    print(f"BLANKET DESPIKE: {fixed} points")


def _bake_modifiers(obj):
    """モディファイアの結果 (今のフレームの形) をメッシュに焼き込み、モディファイアとシェイプキーを消す"""
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    old = obj.data
    obj.modifiers.clear()
    obj.data = new
    new.name = old.name
    bpy.data.meshes.remove(old)
