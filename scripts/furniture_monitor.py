"""デスク2の上のモニター2台と、サブモニターの台の白い箱。モニターはどちらもユーザーが型番を指定した実在の商品なので、メーカーの図面・写真の寸法で作る。

メインモニター = アイ・オー・データ GigaCrysta LCD-GC242HXB/D (23.6型、西寄り = PC の側。机に直に置く):
  細い黒い枠 (上下 14.4mm・左右 13mm) の画面。スタンドは一番上まで伸ばしている (高さ 522mm)。
  スタンドは、画面の裏の高さを変えられる柱 (幅 81mm) が下で前へ曲がって台座に乗る形 (配線を通す縦長の穴がある)。
  台座はヘアラインの黒で、左右の斜めの面が青。下の枠の真ん中に斜体の GigaCrysta のロゴ、右下にボタンの印と青い電源ランプ
サブモニター = 東芝 REGZA 19S22 (19型の液晶テレビ。東隣): ツヤのある黒い枠。左下に TOSHIBA、左上に薄く REGZA、右下の下に出た受光部と緑のランプ。
  台座はロの字の枠。高さが合わないので白い箱の台に乗せる (ユーザー指定の組み方: 白い小物入れ2つを口が手前に見えるように立てて並べ、
  2つ用のふたをかぶせる。左の小物入れは奥、右は手前に寄せる)。台の高さは組み方で決まり、画面の上端はメインより 8cm 低い。
  座るのはメインの前なので、サブは箱ごと座る人の方へ斜めに向ける (layout.py の yaw)
画面はどちらも点いている (ユーザー指定)。メイン = VS Code で Upper10 の app.py を書いている画面 / サブ = Chrome の窓2つ (Upper10 のトップと Flask の日本語訳ドキュメント)。
画像は tools/make_screens.py が描く (screen_main.png・screen_sub.png)。枠の字も同じツールの mark_*.png (枠と同じ色の地に字)。
画面の画像は自分で光る (emission。ライトマップを使わない。焼き付けでは机やキーボードを照らす弱い光源になる)。
位置・大きさは layout.py (monitor_main, monitor_boxes, monitor_sub。screen_front = 画面の前面が台座の中心より何 m 前か)。
ローカル座標: 原点 = 台座の底の中心 / 正面 (画面) = -Y / X = 正面から見て右
構成: Empty `monitor_main` の下に `monitor_main_body` (画面の板・枠の縁・背面の板・柱の上の部分)・`monitor_main_back` (背面の厚くなる所)・
`monitor_main_stand` (曲がった柱)・`monitor_main_base` (台座)・`monitor_main_screen` (画面の黒い面)・`monitor_main_image` (光る画面)・
`monitor_main_logo` `monitor_main_buttons` (枠の字)・`monitor_main_led`。Empty `monitor_sub` の下も同じような並び
(`monitor_sub_stand` = 台座と首、枠の字は `monitor_sub_toshiba` `monitor_sub_regza`)。Empty `monitor_boxes` の下に `monitor_boxes_body`。箱はクリック対象に未登録。
箱の中身 (左 = 綿棒のケース / 右 = 畳んだ紙のゴミ箱。2026-10-27) は furniture_desk_items.py が `monitor_boxes_items` の下に作る
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props import *
from layout import FURNITURE, GC_BASE, box_cases, rotation_deg

LIP = 0.0012          # 画面のまわりの枠の縁が、画面の板の前面より前へ出る厚み
SCREEN_RECESS = 0.0006   # 画面の黒い面は縁の前面より奥 (縁と同じ面にすると、ちらつく)
GLOW = {"monitor_main": 0.8, "monitor_sub": 0.6}   # 画面の明るさ (emission の強さ。ビューアでは 色 x この値。1 未満なので bloom でにじまない)
LID_RIM = 0.040       # サブの台のふたの縁の深さ (天板の上面から。写真)

# GigaCrysta LCD-GC242HXB の図面 (mm を m に)。高さはスタンドを一番上まで伸ばしたとき (台座の底から)
GC = dict(w=0.5503, h=0.326, top=0.522, edge=0.0134, depth=0.0452,
          opening=(0.5244, 0.2972), active=(0.5213, 0.2932))
# 柱の曲がった部分の側面の形 (y, z)。図面の側面図から読んだ点 (y = 台座の中心から後ろへ)。前の面は上から下へ、後ろの面は下から上へ
GC_STAND_FRONT = [(0.0500, 0.180), (0.0661, 0.1618), (0.0710, 0.1510), (0.0734, 0.1373), (0.0726, 0.1235), (0.0690, 0.1078),
                  (0.0631, 0.0882), (0.0553, 0.0706), (0.0455, 0.0529), (0.0337, 0.0353), (0.0220, 0.0255), (0.0023, 0.0196),
                  (-0.0202, 0.0167)]
GC_STAND_REAR = [(0.0396, 0.0157), (0.0514, 0.0255), (0.0631, 0.0392), (0.0729, 0.0549), (0.0808, 0.0745), (0.0867, 0.0961),
                 (0.0906, 0.1176), (0.0929, 0.1373), (0.0945, 0.1627), (0.0949, 0.180)]
# 台座の形 GC_BASE は layout.py (台座の青い辺に文庫本を沿わせて置くため)
GC_BASE_INSET = (0.049, 0.009, 0.015, 0.015, 0.015, 0.009)   # 台座の上面の、各辺からの引っ込み (前は長い斜面・左右は青い面)
GC_BASE_Z = (0.0047, 0.0137)   # 台座の縁の高さ・上面の高さ

# REGZA 19S22 (東芝の寸法図と写真)。枠 462 x 271 (台座の上 29mm から)。画面の寸法 434 x 236
RZ = dict(w=0.462, bottom=0.029, top=0.300, edge=0.022, opening=(0.442, 0.248), opening_top=0.009, active=(0.434, 0.236))


def _bake_modifiers(obj):
    """モディファイアの結果をメッシュに焼き込み、モディファイアを消す"""
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    old = obj.data
    obj.modifiers.clear()
    obj.data = new
    new.name = old.name
    bpy.data.meshes.remove(old)


def _catmull(points, n=4):
    """点の列を通るなめらかな曲線 (Catmull-Rom) の点の列。各区間を n 等分する"""
    pts = [Vector(p) for p in points]
    pts = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1:i + 3]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                    + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3)))
    out.append(tuple(points[-1]))
    return out


def _inset(poly, insets):
    """反時計回りの多角形の、辺 i (poly[i] → poly[i+1]) を insets[i] だけ内側へずらした多角形"""
    lines = []
    for i, a in enumerate(poly):
        a, b = Vector(a), Vector(poly[(i + 1) % len(poly)])
        d = (b - a).normalized()
        lines.append((a + Vector((-d.y, d.x)) * insets[i], d))
    out = []
    for i in range(len(poly)):   # 頂点 i = ずらした辺 i-1 と辺 i の交点
        (p, d), (q, e) = lines[i - 1], lines[i]
        s = ((q.x - p.x) * e.y - (q.y - p.y) * e.x) / (d.x * e.y - d.y * e.x)
        out.append(tuple(p + d * s))
    return out


def _prism_x(name, poly, half_w, mat, parent):
    """側面の形 poly [(y, z), ...] (+X から見て反時計回り) を X の向きに押し出した柱。half_w(z) = その高さでの幅の半分"""
    n = len(poly)
    verts = [(-half_w(z), y, z) for y, z in poly] + [(half_w(z), y, z) for y, z in poly]
    faces = [tuple(range(n, 2 * n)), tuple(reversed(range(n)))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mesh_object(name, verts, faces, [mat], parent=parent)


def _stadium_y(name, cx, z0, z1, width, y0, y1, parent, segs=10):
    """縦長の角の丸い穴 (幅 width、高さ z0〜z1) の形の柱を Y の向きに伸ばした物 (穴を開ける型。穴を開ける物と同じ親の下に置く)"""
    r = width / 2
    ring = [(cx + r * math.cos(math.pi * (1 + k / segs)), z0 + r + r * math.sin(math.pi * (1 + k / segs))) for k in range(segs + 1)]
    ring += [(cx + r * math.cos(math.pi * k / segs), z1 - r + r * math.sin(math.pi * k / segs)) for k in range(segs + 1)]
    n = len(ring)
    verts = [(x, y0, z) for x, z in ring] + [(x, y1, z) for x, z in ring]
    faces = [tuple(range(n)), tuple(reversed(range(n, 2 * n)))] + [(i, n + i, n + (i + 1) % n, (i + 1) % n) for i in range(n)]
    return mesh_object(name, verts, faces, [], parent=parent)


def _finish(obj, bevel=0.0015, angle=40, smooth=35):
    """角を丸め (angle 度より鋭い辺だけ)、なめらかに表示する (smooth 度より鋭い辺は角のまま)"""
    mod = obj.modifiers.new("bevel", 'BEVEL')
    mod.width, mod.segments = bevel, 2
    mod.limit_method, mod.angle_limit = 'ANGLE', math.radians(angle)
    _bake_modifiers(obj)
    obj.data.shade_smooth()
    obj.data.set_sharp_from_angle(angle=math.radians(smooth))


def _screen(name, root, w, bottom, top, mats, opening_w, oz0, oz1, active, z_active, yf):
    """画面のまわり: 黒い画面の面と光る画像を作り、枠の縁 (板の前面から LIP だけ出た4本。boxes_object の形) を返す。
    画面の板は幅 w・高さ bottom〜top、枠の内側 (画面が見える所) は 幅 opening_w・高さ oz0〜oz1"""
    frame, screen, image = mats
    ox = opening_w / 2
    k = 0.001   # 縁は板の外周より 1mm 内側 (板の角の丸みを見せる)
    items = [(-w / 2 + k, w / 2 - k, yf, yf + LIP, oz1, top - k, frame, 0.0004),              # 上
             (-w / 2 + k, w / 2 - k, yf, yf + LIP, bottom + k, oz0, frame, 0.0004),           # 下
             (-w / 2 + k, -ox, yf, yf + LIP, oz0, oz1, frame, 0.0004), (ox, w / 2 - k, yf, yf + LIP, oz0, oz1, frame, 0.0004)]
    boxes_object(f"{name}_screen", [(-ox, ox, yf + SCREEN_RECESS, yf + LIP, oz0, oz1, screen, 0.0002)], parent=root)
    image_quad(f"{name}_image", active[0], active[1], image,
               Matrix.Translation((0, yf + SCREEN_RECESS - 0.0003, z_active - active[1] / 2)), parent=root)
    return items


def _mark(name, image, w, h, x, z, yf, parent):
    """枠に印刷された字 (地の色は枠と同じ画像)。中心 (x, z) に、縁の前面から 0.2mm 前へ"""
    return image_quad(name, w, h, picture_material(name, image, roughness=0.5),
                      Matrix.Translation((x, yf - 0.0002, z - h / 2)), parent=parent)


def _gigacrysta():
    name = "monitor_main"
    e = FURNITURE[name]
    root = add_empty(name, (e["x"], e["y"], e["z0"]), rotation_deg(e))
    frame = make_material("gc_frame", "#151517", roughness=0.5)
    back = make_material("gc_back", "#1A1A1C", roughness=0.45)
    stand = make_material("gc_stand", "#141416", roughness=0.45)
    base = make_material("gc_base", "#1D1D20", roughness=0.32, metallic=0.3)   # ヘアラインの黒
    blue = make_material("gc_blue", "#2C43D6", roughness=0.3, metallic=0.2)
    screen = make_material("gc_screen", "#0A0B0D", roughness=0.35)            # ノングレア
    image = make_material("monitor_main_image", "#FFFFFF", roughness=0.35, emission=GLOW[name],
                          texture="screen_main.png", emission_texture=True)

    w, H, top = GC["w"], GC["h"], GC["top"]
    zb, zc = top - H, top - H / 2           # 画面の板の下端・中心
    yf = -e["screen_front"]                 # 画面の前面 (縁の前面)
    yb = yf + GC["edge"]                    # 板の縁の背面
    ow, oh = GC["opening"]
    items = _screen(name, root, w, zb, top, (frame, screen, image), ow, zc - oh / 2, zc + oh / 2, GC["active"], zc, yf)
    sw = 0.0408   # 柱の幅の半分 (上の部分)
    boxes_object(f"{name}_body", items + [
        (-w / 2, w / 2, yf + LIP, yb, zb, top, frame, 0.0025),                                   # 画面の板
        (-0.214, 0.214, yf + 0.034, yf + GC["depth"], 0.245, 0.476, back, 0.004),               # 背面の真ん中の板
        (-0.06, 0.06, yf + GC["depth"], yf + GC["depth"] + 0.0086, 0.30, 0.42, back, 0.002),   # 壁掛けの金具の板
        (-0.032, 0.032, yf + GC["depth"] + 0.0086, 0.052, zc - 0.025, zc + 0.025, stand, 0.004),   # 傾きを変える軸
        (-sw, sw, 0.0500, 0.0949, 0.172, 0.398, stand, 0.003),                                    # 柱の上の部分 (高さを変える筒)
        (-sw - 0.0004, -sw + 0.0004, 0.0850, 0.0905, 0.18, 0.39, blue, 0.0002),                   # 柱の左右の青い線
        (sw - 0.0004, sw + 0.0004, 0.0850, 0.0905, 0.18, 0.39, blue, 0.0002),
    ], parent=root)
    solids_object(f"{name}_back", [([   # 板の背面の、縁から真ん中の板へ厚くなる所
        (-w / 2 + 0.025, yb - 0.001, zb + 0.02), (w / 2 - 0.025, yb - 0.001, zb + 0.02), (0.214, yf + 0.035, 0.245), (-0.214, yf + 0.035, 0.245),
        (-w / 2 + 0.025, yb - 0.001, top - 0.02), (w / 2 - 0.025, yb - 0.001, top - 0.02), (0.214, yf + 0.035, 0.476), (-0.214, yf + 0.035, 0.476),
    ], back)], parent=root, bevel=0.003)

    # 曲がった柱: 側面の形を押し出し (幅は下ほど少し広い)、配線を通す穴 (幅 30 x 高さ 74mm、机から 79〜153mm) を抜く
    z_foot = GC_BASE_Z[1] - 0.0007
    poly = _catmull(GC_STAND_FRONT) + [(-0.0202, z_foot), (0.0380, z_foot)] + _catmull(GC_STAND_REAR)
    obj = _prism_x(f"{name}_stand", poly, lambda z: 0.0425 - 0.0017 * z / 0.18, stand, root)
    cutter = _stadium_y("_monitor_hole", 0, 0.079, 0.153, 0.030, 0.03, 0.12, root)
    mod = obj.modifiers.new("hole", 'BOOLEAN')
    mod.operation, mod.solver, mod.object = 'DIFFERENCE', 'EXACT', cutter
    _bake_modifiers(obj)
    mesh = cutter.data
    bpy.data.objects.remove(cutter)
    bpy.data.meshes.remove(mesh)
    _finish(obj)

    # 台座: 底の縁 → 斜めの面 → 平らな上面。左右の縁と斜めの面は青
    outer, inner = GC_BASE, _inset(GC_BASE, GC_BASE_INSET)
    n = len(outer)
    verts = [(x, y, 0) for x, y in outer] + [(x, y, GC_BASE_Z[0]) for x, y in outer] + [(x, y, GC_BASE_Z[1]) for x, y in inner]
    faces, mats = [tuple(reversed(range(n))), tuple(range(2 * n, 3 * n))], [0, 0]
    for i in range(n):
        j = (i + 1) % n
        faces += [(i, j, n + j, n + i), (n + i, n + j, 2 * n + j, 2 * n + i)]
        mats += [1, 1] if i in (1, 5) else [0, 0]
    mesh_object(f"{name}_base", verts, faces, [base, blue], mats, parent=root)

    # 下の枠の印: 真ん中に GigaCrysta のロゴ、右に OSD のボタンの印 (▽ 4つと電源)。電源ランプは右下の角の近く (点いている = 青)
    zm = zb + (H - oh) / 4   # 下の枠の高さの真ん中
    _mark(f"{name}_logo", "mark_gigacrysta_logo.png", 0.050, 0.007, 0, zm, yf, root)
    _mark(f"{name}_buttons", "mark_gigacrysta_buttons.png", 0.084, 0.006, 0.134 + 0.042, zm, yf, root)
    boxes_object(f"{name}_led", [(0.2205, 0.2235, yf - 0.0003, yf + 0.001, zb + 0.0016, zb + 0.0026,
                                  make_material("gc_led", "#4F7CFF", emission=2.5))], parent=root, bevel=0.0002)
    return root


def _regza():
    name = "monitor_sub"
    e = FURNITURE[name]
    root = add_empty(name, (e["x"], e["y"], e["z0"]), rotation_deg(e))
    frame = make_material("rz_frame", "#0F0F11", roughness=0.18)    # ツヤのある黒
    back = make_material("rz_back", "#17171A", roughness=0.5)
    stand = make_material("rz_stand", "#101012", roughness=0.15)
    screen = make_material("rz_screen", "#08090B", roughness=0.1)
    image = make_material("monitor_sub_image", "#FFFFFF", roughness=0.1, emission=GLOW[name],
                          texture="screen_sub.png", emission_texture=True)

    w, zb, top = RZ["w"], RZ["bottom"], RZ["top"]
    yf = -e["screen_front"]
    ow, oh = RZ["opening"]
    oz1 = top - RZ["opening_top"]
    oz0 = oz1 - oh
    items = _screen(name, root, w, zb, top, (frame, screen, image), ow, oz0, oz1, RZ["active"], (oz0 + oz1) / 2, yf)
    boxes_object(f"{name}_body", items + [
        (-w / 2, w / 2, yf + LIP, yf + RZ["edge"], zb, top, frame, 0.003),          # 画面の板 (縁の厚み 22mm)
        (-0.215, 0.215, yf + RZ["edge"] - 0.001, yf + 0.045, 0.036, 0.275, back, 0.006),   # 背面の段
        (-0.15, 0.15, yf + 0.044, yf + 0.071, 0.036, 0.235, back, 0.008),           # 背面のふくらみ (基板と電源)
        (0.174, 0.201, yf + 0.001, yf + 0.016, zb - 0.008, zb + 0.001, frame, 0.002),   # 右下の受光部 (枠の下へ 8mm 出る)
    ], parent=root)
    # 台座: ロの字の枠 (230 x 143mm。前の辺が高い) と、後ろの辺から画面の裏へ上がる首
    hx, hy = 0.115, 0.0715
    boxes_object(f"{name}_stand", [
        (-hx, hx, -hy, -0.048, 0, 0.012, stand), (-hx, hx, 0.0, hy, 0, 0.008, stand),
        (-hx, -hx + 0.02, -0.048, 0.0, 0, 0.009, stand), (hx - 0.02, hx, -0.048, 0.0, 0, 0.009, stand),
        (-0.03, 0.03, 0.005, 0.060, 0.006, 0.08, back, 0.004),
    ], parent=root, bevel=0.002)
    zm = (zb + oz0) / 2
    _mark(f"{name}_toshiba", "mark_toshiba.png", 0.028, 0.006, -0.208, zm, yf, root)
    _mark(f"{name}_regza", "mark_regza.png", 0.026, 0.005, -0.205, (oz1 + top) / 2, yf, root)
    boxes_object(f"{name}_led", [(0.1775, 0.1805, yf + 0.0004, yf + 0.0012, zb - 0.0055, zb - 0.0035,
                                  make_material("rz_led", "#3BE36B", emission=2.0))], parent=root, bevel=0.0002)
    return root


def _case(x0, x1, y0, y1, z1, t, mat):
    """口が手前 (-Y) に見えるように立てた小物入れ (厚み t の板5枚。boxes_object に渡す形)"""
    return [(x0, x0 + t, y0, y1, 0, z1, mat), (x1 - t, x1, y0, y1, 0, z1, mat),            # 左右 (もとの長い側面)
            (x0 + t, x1 - t, y0, y1, 0, t, mat), (x0 + t, x1 - t, y0, y1, z1 - t, z1, mat),   # 下と上 (もとの短い側面)
            (x0 + t, x1 - t, y1 - t, y1, t, z1 - t, mat)]                                 # 奥 (もとの底)


def _boxes():
    """サブモニターの台 (ユーザー指定の組み方): 白い小物入れ2つを口が手前に見えるように立てて左右に並べ、2つ用のふたをかぶせる。
    左の小物入れはふたの奥の縁へ、右は手前の縁へ寄せる (前後にすき間があると、ふたがずれて安定しない)。
    2つの間はすき間なし、ふたの左右の縁とは 2mm ずつ遊びがある。小物入れの位置は layout.box_cases。
    中身 (左 = 綿棒のケース / 右 = 畳んだ紙のゴミ箱。2026-10-27 ユーザー指定) は furniture_desk_items.py"""
    e = FURNITURE["monitor_boxes"]
    hx, hy, top = e["w"] / 2, e["d"] / 2, e["h"]
    cases, t = box_cases()
    root = add_empty("monitor_boxes", (e["x"], e["y"], e["z0"]), rotation_deg(e))
    mat = make_material("monitor_box", "#F4F4F0", roughness=0.8)   # 白い紙の箱
    items = _case(*cases["left"], t, mat) + _case(*cases["right"], t, mat)   # 左 = 奥 / 右 = 手前
    z = top - LID_RIM
    items += [(-hx, hx, -hy, hy, top - t, top, mat),                                                   # ふたの天板
              (-hx, hx, -hy, -hy + t, z, top - t, mat), (-hx, hx, hy - t, hy, z, top - t, mat),          # 前後の縁
              (-hx, -hx + t, -hy + t, hy - t, z, top - t, mat), (hx - t, hx, -hy + t, hy - t, z, top - t, mat)]   # 左右の縁
    boxes_object("monitor_boxes_body", items, parent=root)
    return root


def build_monitors():
    _boxes()
    return _gigacrysta(), _regza()
