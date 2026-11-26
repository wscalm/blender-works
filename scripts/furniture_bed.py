"""ダブルベッド (ダークブラウンの土台とヘッドボード、土台と同じ大きさのくすんだピンクの厚いマットレス、グレーのタオル地の敷きパッド、ネイビーの枕、黒い毛布の塊)。

位置・大きさは layout.py。ローカル座標: 原点 = ベッドの中心の床 / 正面 = -Y (足元側) / 背面 = +Y (ヘッドボード側)
構成: Empty `bed` の下に、`bed_frame` (土台・脚。ウォールナットの木目を暗くする) と `bed_headboard` (木目を薄くした画像。ユーザー指定)、
`bed_bedding` (マットレス。土台と同じ幅と長さで、土台の上面は隠れて見えない (ユーザー指定))・
`bed_cover` (敷きパッド: マットレスの上に敷いたグレーのタオル地。キルティングの縫い目が薄く見える (ユーザー指定)。
ラグくらいの薄さ (厚さ 1.2cm。2026-10-27 ユーザー指定「もっと薄い」)。同じ日の続きの指示「少しだけ大きく、角を丸く。はみ出た部分は重力に従って垂らす」で、
マットレスより 4cm ずつ大きい角の丸い布にして、はみ出た分をマットレスの側面へ垂らした (_draped_cover))、
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
MATTRESS_TOP = BED_TOP - 0.01   # マットレス本体の上面 (この上に厚さ 1cm の敷きパッド)
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

    # マットレス: 土台と同じ幅と長さで、土台の上に乗る (土台の上面は見えない。ユーザー指定)。厚さ 0.24。上の縁の丸みは 1.5cm
    mw = hx                    # マットレスの半幅 = 土台の半幅
    m0, m1 = -hy, yb - 0.003   # 足元の端 = 土台の足元の端 / 頭の端 = ヘッドボードの前
    soft_boxes_object("bed_bedding", [
        (-mw, mw, m0, m1, MATTRESS_BOTTOM, MATTRESS_TOP, fabric_material("bed_mattress", "cotton", MATTRESS), 0.015, (0.003, 0.003, 0.0)),
    ], parent=root, cuts=12)
    # 毛布の布のシミュレーションがぶつかる敷きパッドは、前の形 (マットレスの上面だけに乗る、縁より 3mm 外の薄い箱) のまま
    # (毛布の形を変えないため)。シミュレーションの後で消して、垂らした敷きパッド (_draped_cover) に置き換える。上面の高さはどちらも BED_TOP
    cover = fabric_material("bed_cover", "towel", COVER)
    proxy = soft_boxes_object("bed_cover", [
        (-mw - 0.003, mw + 0.003, m0 - 0.003, m1, MATTRESS_TOP - 0.006, BED_TOP, cover, 0.007, (0.0, 0.0, 0.0)),
    ], parent=root, cuts=24, wrinkle=0.002, wrinkle_size=0.5, seed=7)
    # 枕1つ (頭側の中央): 2枚の布を縫い合わせた形。下の面はベッドに押されて平ら
    pillow_object("bed_pillow", 0.66, 0.40, 0.11, [fabric_material("bed_pillow", "cotton", PILLOW)],
                  Matrix.Translation((0.0, 0.76, BED_TOP + 0.05)) @ Matrix.Rotation(math.radians(3), 4, 'Z'),
                  parent=root, flat_bottom=0.8, wrinkle=0.005, seed=5)

    colliders = [bpy.data.objects[n] for n in ("bed_bedding", "bed_cover", "bed_pillow", "bed_frame", "bed_headboard", "room_floor")
                 if n in bpy.data.objects]
    _messy_blanket(root, make_material("bed_blanket", "#FFFFFF", roughness=1.0, specular=0.3, **BLANKET), colliders, hx, hy)
    mesh = proxy.data
    bpy.data.objects.remove(proxy)
    bpy.data.meshes.remove(mesh)
    _draped_cover(root, cover, mw, m0, m1)
    return root


# 敷きパッド (_draped_cover)
COVER_OVER = 0.04     # 広げた布がマットレスの上面の縁から外へ出る長さ (足元・左右・頭の側)。ユーザー指定「少しだけ大きく」
# 角の丸み (広げた布を上から見た半径)。ユーザー指定「角を丸く」。垂れの長さが一定になる丸み (6.7cm) より少し大きくして、裾が角で 5mm ほど上がる
# (10cm だと角の 6cm ほどの間で裾が 1.4cm も上がり、角が切れ込んだように見えた)
COVER_CORNER = 0.08
COVER_T = 0.012       # 厚さ (ラグくらい)。上面は BED_TOP なので、平らな所の下の面はマットレスに 2mm 沈む
COVER_BEND = 0.03     # マットレスの縁で曲がる半径 (下の面)。キルティングで少し硬いので、マットレスの角の丸み (1.5cm) より大きく回る
COVER_GAP = 0.003     # 垂れた所とマットレスの側面のすき間 (側面は真ん中が 3mm ふくらむ)
COVER_FLARE = 5.0     # 垂れた所が下ほど外へ開く量 (垂れた長さ s に対して FLARE x s^2。裾で 2mm)
COVER_PUFF = 0.006    # 角で余った布が外へふくらむ量 (余りの割合 1 のとき)
COVER_HEM_WAVE = 0.003    # 裾の波打ち (外へ。最大)
# 手で敷いたので、マットレスの真ん中からずれて少し回っている (広げた布の中心のずれ (m) と、上から見て反時計回りの角度 (度))。
# 足元の東の側 (目から見える) の垂れが 1.5cm 長く、足元の辺は西の端ほど長い (1cm)。西の側の足元は 1.5cm 短い
COVER_SHIFT, COVER_TURN = (0.008, -0.005), 0.4


def _draped_cover(root, mat, mw, m0, m1):
    """敷きパッド (2026-10-27 ユーザー指定「少しだけ大きくし、角を丸く。マットレスからはみ出た部分は重力に従って垂らす」)。
    平らに広げると、マットレスの上面より COVER_OVER ずつ大きい、角の丸い (上から見て半径 COVER_CORNER) 厚さ COVER_T の布。
    マットレスに乗せた形は、広げた布の各点を写して作る (drape): 上面は平ら (高さ BED_TOP)、マットレスの縁で半径 COVER_BEND で曲がり、
    はみ出た分は側面に沿って真下へ垂れる。布の長さは変わらないので、角の丸い所ほど垂れが短く、裾は角で上がる。角では余った布が外へふくらむ。
    手で敷いたので、真ん中から少しずれて回っている (COVER_SHIFT・COVER_TURN。垂れの長さが辺ごとに少し違う)。裾は少し波打つ。
    頭の側はヘッドボードとのすき間へ、東の側はソファーの背とスツールの座面の中へ垂れる (押し込まれたように見える)。
    縁は厚みの半円で丸め (パイピング)、裏へ少し回り込む。下の面 (マットレスに隠れる) は作らない。
    UV `UVMap` (タオル地の画像) と焼き付けの島は、広げた布の上の位置 (1 = 1m。垂れた所も布の上の長さなので、模様は側面へ続く)。
    ローカル座標はベッドと同じ (原点 = ベッドの中心の床 / -Y = 足元)"""
    T, Rw, g, Rc = COVER_T, COVER_BEND, COVER_GAP, COVER_CORNER
    zb = BED_TOP - T                                     # 平らな所の下の面
    px, py0, py1 = mw + COVER_OVER, m0 - COVER_OVER, m1 + COVER_OVER   # 広げた布の範囲 (X -px〜px / Y py0〜py1)
    fx, fy0, fy1 = mw + g - Rw, m0 - g + Rw, m1 + g - Rw   # この長方形の外で曲がり始める (曲がり終えた所が側面から g の位置)
    arc = math.pi / 2 * Rw                               # 曲がる所の布の長さ
    rng = random.Random(17)
    waves = [(2 * math.pi / rng.uniform(0.18, 0.35), rng.uniform(0, math.pi), rng.uniform(0, 6.3)) for _ in range(4)]

    def drape(x, y):
        """広げた布の点 (x, y) → マットレスに乗せた布の下の面の点"""
        cx, cy = min(max(x, -fx), fx), min(max(y, fy0), fy1)
        dx, dy = x - cx, y - cy
        d = math.hypot(dx, dy)
        if d < 1e-9:
            return Vector((x, y, zb))
        if d <= arc:
            s, h, z = 0.0, Rw * math.sin(d / Rw), zb - Rw * (1 - math.cos(d / Rw))
        else:
            s = d - arc                                  # 縁から下へ垂れた長さ
            h, z = Rw + COVER_FLARE * s * s, zb - Rw - s
        if abs(dx) > 1e-9 and abs(dy) > 1e-9:            # 角: 布の周の長さ (d に比例) が曲がった後の半径 h まで縮む。余った分だけ外へふくらむ
            k = math.sin(2 * math.atan2(abs(dy), abs(dx))) ** 2
            h += COVER_PUFF * max(0.0, 1 - h / d) * k
        wave = sum(math.sin(f * (cx * math.cos(a) + cy * math.sin(a)) + ph) for f, a, ph in waves) / len(waves)
        h += COVER_HEM_WAVE * wave * min(1.0, s / 0.015)
        return Vector((cx + dx / d * h, cy + dy / d * h, z))

    def normal(x, y, e=1e-4):
        n = (drape(x + e, y) - drape(x - e, y)).cross(drape(x, y + e) - drape(x, y - e))
        return n.normalized()

    # 広げた布の格子: 縁の近くほど細かい (曲がる所と垂れる所)。角の Rc 四方は、正方形の格子を同心の円弧へ写して丸める
    band = [b for b in (0.0, 0.003, 0.007, 0.012, 0.017, 0.022, 0.028, 0.034, 0.040, 0.046, 0.052, 0.058, 0.064, 0.070, 0.077, 0.087)
            if b < Rc - 0.004] + [Rc]

    def axis(lo, hi, step=0.08):
        n = max(1, math.ceil((hi - lo - 2 * Rc) / step))
        inner = [lo + Rc + (hi - lo - 2 * Rc) * k / n for k in range(1, n)]
        return [lo + b for b in band] + inner + [hi - b for b in reversed(band)]
    xs, ys = axis(-px, px), axis(py0, py1)

    def corner_center(x, y):
        """(x, y) が角の正方形の中なら、角の円弧の中心"""
        if abs(x) <= px - Rc + 1e-9 or py0 + Rc - 1e-9 <= y <= py1 - Rc + 1e-9:
            return None
        return (math.copysign(px - Rc, x), py0 + Rc if y < py0 + Rc else py1 - Rc)

    def plan(x, y):
        c = corner_center(x, y)
        if c is None:
            return x, y
        a, b = abs(x - c[0]), abs(y - c[1])
        r = max(a, b)
        th = math.pi / 4 * (b / a) if a >= b else math.pi / 2 - math.pi / 4 * (a / b)
        return c[0] + math.copysign(r * math.cos(th), x - c[0]), c[1] + math.copysign(r * math.sin(th), y - c[1])

    # 広げた布の上の位置 (UV もこれ) → ベッドの上の位置 (手で敷いたずれと回り)。布の中心は (0, (py0 + py1) / 2)
    turn = math.radians(COVER_TURN)
    ct, st, cy0 = math.cos(turn), math.sin(turn), (py0 + py1) / 2

    def on_bed(x, y):
        return (COVER_SHIFT[0] + x * ct - (y - cy0) * st, COVER_SHIFT[1] + cy0 + x * st + (y - cy0) * ct)

    nu, nv = len(xs), len(ys)
    flat = [[plan(x, y) for y in ys] for x in xs]
    verts, seeds = [], []
    for i in range(nu):
        for j in range(nv):
            x, y = flat[i][j]
            bx, by = on_bed(x, y)
            verts.append(drape(bx, by) + normal(bx, by) * T)   # 上の面 = 下の面から法線の向きへ厚さの分
            seeds.append((x, y))
    faces = [(i * nv + j, (i + 1) * nv + j, (i + 1) * nv + j + 1, i * nv + j + 1) for i in range(nu - 1) for j in range(nv - 1)]

    # 縁 (裾): 外周の各点で、厚みの半円 (上の面 → 布の先 → 下の面) と、裏へ 6mm 回り込む所
    outline = ([i * nv for i in range(nu)] + [(nu - 1) * nv + j for j in range(1, nv)] +
               [i * nv + nv - 1 for i in range(nu - 2, -1, -1)] + [j for j in range(nv - 2, 0, -1)])   # 上から見て反時計回り
    steps = [math.radians(b) for b in (30, 60, 90, 120, 150, 180)]
    tail = 0.006
    rims = []
    for vi in outline:
        x, y = seeds[vi]
        c = corner_center(x, y)
        if c is not None:
            m = Vector((x - c[0], y - c[1])).normalized()
        else:
            m = Vector((1 if x > px - 1e-6 else -1 if x < -px + 1e-6 else 0, 1 if y > py1 - 1e-6 else -1 if y < py0 + 1e-6 else 0))
        bx, by = on_bed(x, y)
        mx, my = m.x * ct - m.y * st, m.x * st + m.y * ct   # 外向きをベッドの向きへ回す
        b0, n0 = drape(bx, by), normal(bx, by)
        out = (drape(bx + mx * 1e-4, by + my * 1e-4) - b0).normalized()   # 布に沿って外へ
        ring = [vi]
        for beta in steps:
            ring.append(len(verts))
            verts.append(b0 + n0 * (T / 2) * (1 + math.cos(beta)) + out * (T / 2) * math.sin(beta))
            seeds.append((x + m.x * T / 2 * beta, y + m.y * T / 2 * beta))
        ring.append(len(verts))
        verts.append(drape(bx - mx * tail, by - my * tail))
        seeds.append((x + m.x * (T / 2 * math.pi + tail), y + m.y * (T / 2 * math.pi + tail)))
        rims.append(ring)
    for k in range(len(rims)):
        a, b = rims[k], rims[(k + 1) % len(rims)]
        faces += [(b[s], a[s], a[s + 1], b[s + 1]) for s in range(len(a) - 1)]

    obj = mesh_object("bed_cover", verts, faces, [mat], parent=root)
    uv = obj.data.uv_layers.new(name="UVMap")
    seed = obj.data.uv_layers.new(name="lightmap_seed")
    for loop in obj.data.loops:
        uv.data[loop.index].uv = seed.data[loop.index].uv = seeds[loop.vertex_index]
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj["lightmap_uv"] = "lightmap_seed"   # bake.add_lightmap_uvs
    zs = [v[2] for v in verts]
    print(f"BED COVER: {len(verts)} verts, {len(faces)} faces, z {min(zs):.3f}〜{max(zs):.3f}, "
          f"flat {2 * px:.3f} x {py1 - py0:.3f} (corner r {Rc})")
    return obj


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
