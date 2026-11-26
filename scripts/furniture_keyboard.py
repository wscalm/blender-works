"""キーボード Logicool G813 (日本語配列) とマウス Logicool G604 LIGHTSPEED (どちらもユーザー指定の実在の商品)。デスク2の上、メインモニターの前。

キーボード: ヘアラインの濃い灰色のアルミの天板に、背の低いキー (GL スイッチ) が浮いて並ぶ (キーの下にスイッチがのぞく)。
  キーの並びと寸法は keyboard_spec.py (公式の写真から測った mm)。本体は奥が厚いくさび形。左上に G のロゴ、上の段に M1〜MR・
  ゲームモード・明るさの丸いボタン、右上に音量のローラー (黒い枠の中) とメディアの丸いボタン4つ、CAPS LOCK / NUM LOCK のランプ。
  キーの字は虹色に光る (RGB の初期の色。画像 textures/keyboard_legends.png は tools/make_desk_items.py が描く)。
  字は各キーの天面にわずかに浮かせた板 `keyboard_legends` (光る。ビューアでは足し算で重ねる。焼き付けでは隠す)。
  編んだケーブルは奥の辺から出て、メインモニターの台座の上 (柱の西) を通って机の奥へ落ちる
マウス: G604 の形を、公式の写真 (真上・親指の側の真横) から測った輪郭と高さで、断面 (前から後ろへ並べた輪) をつないだ曲面にする。
  左 (親指の側) に大きな張り出しと、その上の面に6つのボタン (G4〜G9)。金属の歯のホイールと、その後ろの細長いボタン2つ、
  左のボタンの縁の +/- ボタン、青い表示ランプ。手のひらの点々・継ぎ目・G のロゴ・ホイールの溝は画像 textures/mouse_g604_top.png を上から貼る
位置・大きさは layout.py (keyboard, mouse)。ローカル座標: 原点 = 底面の中心 / 正面 (座る人の側) = -Y / X = 正面から見て右
  (マウスは手のひらの側が -Y、親指の側が -X)
構成: Empty `keyboard` の下に `keyboard_case` (本体)・`keyboard_keys`・`keyboard_switches`・`keyboard_buttons` (丸いボタンとローラーの枠)・
`keyboard_roller`・`keyboard_legends`・`keyboard_leds`・`keyboard_feet`、部屋の座標の Empty `keyboard_cable_group` の下に `keyboard_cable`。
Empty `mouse` の下に `mouse_body`・`mouse_buttons` (親指の6つ・+/-・ホイールの後ろ)・`mouse_panel`・`mouse_wheel`・`mouse_led`・`mouse_feet`。
どちらもクリック対象には未登録
"""
import math
import os
import sys

import bmesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props import *
from layout import FURNITURE, rotation_deg
import keyboard_spec as KB

MM = 0.001


def _join(name, objs, parent):
    """同じ親の下の物をまとめて1つのメッシュにする (材質はまとめた後の並びに直す)"""
    bm = bmesh.new()
    mats = []
    for o in objs:
        me = o.data
        remap = []
        for m in me.materials:
            if m not in mats:
                mats.append(m)
            remap.append(mats.index(m))
        for p in me.polygons:
            p.material_index = remap[p.material_index] if remap else 0
        me.transform(o.matrix_basis)
        bm.from_mesh(me)
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(me)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for m in mats:
        mesh.materials.append(m)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = parent
    return obj


def _decal(obj):
    """面のすぐ上に重ねた光る板 (キーの字など): ビューアでは少し手前に描き (userData.decal)、焼き付けでは隠す (bake.py)"""
    obj["decal"] = 1
    obj["bake_skip"] = 1
    return obj


def _gear_x(name, x0, x1, y, z, r, depth, teeth, mat, parent):
    """X の向きの軸の歯車 (細かい溝のある円柱): マウスのホイール・キーボードの音量のローラー。半径 r、溝の深さ depth (m)"""
    verts, faces = [], []
    m = 2 * teeth
    for x in (x0, x1):
        for i in range(m):
            a = math.pi * i / teeth
            rr = r if i % 2 == 0 else r - depth
            verts.append((x, y + rr * math.cos(a), z + rr * math.sin(a)))
    faces.append(tuple(range(m)))
    faces.append(tuple(range(m, 2 * m)))
    for i in range(m):
        j = (i + 1) % m
        faces.append((i, j, m + j, m + i))
    obj = mesh_object(name, verts, faces, [mat], parent=parent)
    _fix_normals(obj)
    return obj


def _fix_normals(obj):
    """面を外向きにそろえる"""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


# ---------------------------------------------------------------- キーボード (G813)
PLATE_FRONT, PLATE_BACK = 10.5, 14.5   # 天板の上面の高さ (手前・奥、mm)。奥が厚いくさび形
CASE_BOTTOM = 1.0                      # 本体の底 (ゴムの脚の上)
CAP_LIFT, CAP_T = 3.0, 3.0             # キーの下面の天板からの高さ・キーの厚み (mm)。キーは浮いて見え、下にスイッチがのぞく
ROUND_H = 2.4                          # 丸いボタンの高さ (天板から)
LEGEND_GLOW = 0.9                      # 光る字の明るさ (emission)
CABLE_X = 280.0                        # ケーブルの出口 (左端から mm)


def _plate_z(y):
    """天板の上面の高さ (mm)。y = 奥の端から (mm)"""
    return PLATE_BACK - (PLATE_BACK - PLATE_FRONT) * y / KB.D


def _lx(x):
    """keyboard_spec の x (左端から mm) → ローカルの X (m)"""
    return (x - KB.W / 2) * MM


def _ly(y):
    """keyboard_spec の y (奥の端から mm) → ローカルの Y (m)"""
    return (KB.D / 2 - y) * MM


def _legend_mesh(name, rects, mat, parent):
    """光る字の板: rects = [(左, 右, 奥, 手前 (mm), z (m)), ...]。UV は画像 (キーボードの上面全体) の中のその位置"""
    verts, faces, uvs = [], [], []
    for xa, xb, ya, yb, z in rects:
        n = len(verts)
        corners = [(xa, yb), (xb, yb), (xb, ya), (xa, ya)]   # 上から見て反時計回り (面は上向き)
        verts += [(_lx(x), _ly(y), z) for x, y in corners]
        faces.append((n, n + 1, n + 2, n + 3))
        uvs += [(x / KB.W, 1 - y / KB.D) for x, y in corners]
    obj = mesh_object(name, verts, faces, [mat], parent=parent)
    layer = obj.data.uv_layers.new(name="UVMap")
    for li, uv in enumerate(uvs):
        layer.data[li].uv = uv
    return _decal(obj)


def _brushed_uvs(obj):
    """ヘアラインの UV: 筋 (画像の縦 = V) が本体の左右 (X) に沿うように、面の向きごとに平面に投影する"""
    me = obj.data
    layer = me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        n = p.normal
        for li in p.loop_indices:
            x, y, z = me.vertices[me.loops[li].vertex_index].co
            if abs(n.z) >= max(abs(n.x), abs(n.y)):
                layer.data[li].uv = (y, x)          # 上面
            elif abs(n.y) >= abs(n.x):
                layer.data[li].uv = (z, x)          # 手前・奥の面
            else:
                layer.data[li].uv = (z, y + 0.3)    # 左右の面 (筋は前後)


def _keyboard():
    e = FURNITURE["keyboard"]
    root = add_empty("keyboard", (e["x"], e["y"], e["z0"]), rotation_deg(e))
    hx, hy = KB.W / 2 * MM, KB.D / 2 * MM
    plate = make_material("keyboard_plate", "#FFFFFF", roughness=0.45, metallic=0.5, specular=0.5,
                          texture="keyboard_brushed.jpg", texture_size=0.1)   # ヘアラインの濃い灰色のアルミ
    rubber = make_material("keyboard_rubber", "#111112", roughness=0.9)
    cap = make_material("keyboard_cap", "#1D1E21", roughness=0.5, specular=0.45)
    switch = make_material("keyboard_switch", "#2A2B2F", roughness=0.6)
    black = make_material("keyboard_black", "#121214", roughness=0.55)

    # 本体: 底はゴムの脚の上。上面は奥へ上がるくさび形
    z0, zf, zb = CASE_BOTTOM * MM, PLATE_FRONT * MM, PLATE_BACK * MM
    case = solids_object("keyboard_case", [([(-hx, -hy, z0), (hx, -hy, z0), (hx, hy, z0), (-hx, hy, z0),
                                             (-hx, -hy, zf), (hx, -hy, zf), (hx, hy, zb), (-hx, hy, zb)], plate)],
                         parent=root, bevel=0.0012, segments=3)
    _brushed_uvs(case)
    boxes_object("keyboard_feet", [(-hx + 0.02, hx - 0.02, -hy + 0.008, -hy + 0.016, 0, z0 + 0.0003, rubber),
                                   (-hx + 0.02, hx - 0.02, hy - 0.016, hy - 0.008, 0, z0 + 0.0003, rubber)],
                 parent=root, bevel=0.0003)

    # キー: 天面 (キャップ) と、その下にのぞくスイッチ。L 字の Enter は上の段と下の段の2つの箱
    caps, switches, legends = [], [], []
    for k in KB.keys():
        if k["kind"] == "round":
            continue
        x, y, w, h = k["x"], k["y"], k["w"], k["h"]
        zp = _plate_z(y)
        y_back = y - h / 2
        dz = 0.0
        if k["kind"] == "enter2":   # 下の段は上の段の下まで伸ばしてつなぐ (天面は 0.1mm 低く: 重なる所がちらつかないように)
            y_back -= KB.GAP + 1.0
            dz = 0.1
        zc0, zc1 = (zp + CAP_LIFT) * MM, (zp + CAP_LIFT + CAP_T - dz) * MM
        caps.append((_lx(x - w / 2), _lx(x + w / 2), _ly(y + h / 2), _ly(y_back), zc0, zc1, cap, 0.0009))
        if k["kind"] != "enter2":
            s = 1.6
            switches.append((_lx(x - w / 2 + s), _lx(x + w / 2 - s), _ly(y + h / 2 - s), _ly(y - h / 2 + s),
                             (zp - 0.5) * MM, zc0 + 0.0003, switch))
        legends.append((x - w / 2, x + w / 2, y_back, y + h / 2, zc1 + 0.00012))
    boxes_object("keyboard_keys", caps, parent=root)
    boxes_object("keyboard_switches", switches, parent=root, bevel=0)

    # 丸いボタン (M1〜MR・ゲームモード・明るさ・メディア): 少し高い円盤
    pieces = []
    for k in KB.keys():
        if k["kind"] != "round":
            continue
        zp = _plate_z(k["y"]) * MM
        r = k["w"] / 2 * MM
        t = ROUND_H * MM
        pieces.append(lathe_object("_kb_round", [(0, zp - 0.0005, 0), (r, zp - 0.0005, 0), (r, zp + t - 0.0006, 0),
                                                  (r - 0.0004, zp + t - 0.0001, 0), (r - 0.0008, zp + t, 0), (0, zp + t, 0)],
                                   [cap], parent=root, segments=28, location=(_lx(k["x"]), _ly(k["y"]), 0)))
        q = 0.31 * k["w"]   # 字の板は丸い天面の内側に収める (外は画像も黒)
        legends.append((k["x"] - q, k["x"] + q, k["y"] - q, k["y"] + q, zp + t + 0.00012))
    # 音量のローラー: 奥の辺に接した黒い枠の中に、細かい溝の金属のローラーが寝ている
    R = KB.ROLLER
    zr = _plate_z(R["y1"])
    t = 1.6
    ox0, ox1, oy1 = R["r0"] - 1.4, R["r1"] + 1.4, R["y"] + R["d"] / 2 + 0.8   # 枠の内側 (穴)
    frame = [(R["x0"], ox0, 0.0, R["y1"]), (ox1, R["x1"], 0.0, R["y1"]), (ox0, ox1, oy1, R["y1"])]
    pieces.append(boxes_object("_kb_roller_frame", [(_lx(a), _lx(b), _ly(d), _ly(c), (zr - 0.4) * MM, (zr + t) * MM, black, 0.0008)
                                                    for a, b, c, d in frame], parent=root))
    pieces.append(boxes_object("_kb_roller_hole", [(_lx(ox0), _lx(ox1), _ly(oy1), _ly(0.3), (zr - 0.4) * MM, (zr + 0.05) * MM,
                                                    black)], parent=root, bevel=0))
    buttons = _join("keyboard_buttons", pieces, root)
    for p in buttons.data.polygons:
        p.use_smooth = True
    buttons.data.set_sharp_from_angle(angle=math.radians(40))
    metal = make_material("keyboard_roller", "#5E6166", roughness=0.35, metallic=0.6)   # 濃い灰色の金属
    roller = _gear_x("keyboard_roller", _lx(R["r0"]), _lx(R["r1"]), _ly(R["y"]), (zr + 4.6) * MM - R["d"] / 2 * MM,
                     R["d"] / 2 * MM, 0.0004, 36, metal, root)   # 細かい溝 (軸に沿った筋) のローラー
    roller["lightmap_proxy"] = "keyboard_case"

    # 光る字 (キーの天面・丸いボタンの上) と、天板に印刷した物 (G のロゴ・CAPS LOCK / NUM LOCK の字)
    glow = make_material("keyboard_legends_glow", "#000000", emission=LEGEND_GLOW, texture="keyboard_legends.png",
                         texture_size=1.0, emission_texture=True)
    g = KB.G_LOGO
    s = g["size"] / 2 + 1.5
    legends.append((g["x"] - s, g["x"] + s, g["y"] - s, g["y"] + s, (_plate_z(g["y"]) + 0.15) * MM))
    legends.append((KB.LOCK_LEDS[0][1] - 13, KB.LOCK_LEDS[-1][1] + 13, 8.0, 12.5, (_plate_z(10) + 0.15) * MM))
    _legend_mesh("keyboard_legends", legends, glow, root)
    led_on = make_material("keyboard_led_on", "#F2F6FF", emission=1.5)
    led_off = make_material("keyboard_led_off", "#3A3B3F", roughness=0.4)
    zl = _plate_z(16.1)
    boxes_object("keyboard_leds", [(_lx(x - 1.3), _lx(x + 1.3), _ly(16.8), _ly(15.4), (zl - 0.2) * MM, (zl + 0.35) * MM,
                                    led_on if on else led_off) for _, x, on in KB.LOCK_LEDS], parent=root, bevel=0.0002)
    _cable(root)
    return root


def _cable(root):
    """編んだケーブル: 奥の辺 (左端から CABLE_X) から出て、メインモニターの台座の前の斜面と上面を通り (柱の西をよける)、
    台座の奥から机の奥の端へ落ちる。部屋の座標で通る点を決める (台座の高さは furniture_monitor.py の GC_BASE_Z: 縁 4.7mm・上面 13.7mm)"""
    kb, mon = FURNITURE["keyboard"], FURNITURE["monitor_main"]
    a = math.radians(rotation_deg(kb))
    lx, ly = _lx(CABLE_X), _ly(0)
    ex, ey = kb["x"] + lx * math.cos(a) - ly * math.sin(a), kb["y"] + lx * math.sin(a) + ly * math.cos(a)
    z = kb["z0"]
    r = 0.0019
    mx, my = mon["x"], mon["y"]
    front, top_front, top_back, back = my + 0.1153, my + 0.1153 - 0.049, my - 0.0953, my - 0.1103   # 台座の前の縁・上面の前・上面の奥・奥の縁 (Y)
    x1 = mx - 0.064   # 台座の上は柱 (X ±0.0425) の西を通す
    pts = [(ex, ey, z + 0.0075), (ex, ey - 0.006, z + 0.0068), (ex - 0.0025, ey - 0.013, z + 0.0036), (ex - 0.0075, ey - 0.020, z + r + 0.0002),
           (ex - 0.0135, front + 0.0034, z + 0.004), (ex - 0.0175, front - 0.0006, z + 0.0047 + r),
           (ex - 0.0235, (front + top_front) / 2, z + 0.0092 + r), (x1 + 0.010, top_front, z + 0.0137 + r),
           (x1 + 0.002, top_front - 0.03, z + 0.0137 + r), (x1, (top_front + top_back) / 2, z + 0.0137 + r),
           (x1, top_back + 0.006, z + 0.0137 + r), (x1, top_back - 0.006, z + 0.0110 + r), (x1, back + 0.0004, z + 0.0047 + r),
           (x1, back - 0.004, z + 0.0030), (x1, FURNITURE["desk2"]["y"] - FURNITURE["desk2"]["d"] / 2 + 0.002, z + r),
           (x1, FURNITURE["desk2"]["y"] - FURNITURE["desk2"]["d"] / 2 - 0.0025, z - 0.001),
           (x1, FURNITURE["desk2"]["y"] - FURNITURE["desk2"]["d"] / 2 - 0.0045, z - 0.012),
           (x1, FURNITURE["desk2"]["y"] - FURNITURE["desk2"]["d"] / 2 - 0.005, z - 0.16)]
    path = _catmull(pts, 3)
    g = world_group("keyboard_cable_group", root)
    braid = make_material("keyboard_cable", "#1A1A1C", roughness=0.85)
    tubes_object("keyboard_cable", [path], r, braid, parent=g, sides=10)
    # 出口の根元の太い所
    tubes_object("keyboard_cable_boot", [[(ex, ey + 0.0015, z + 0.0075), (ex, ey - 0.008, z + 0.0072)]], 0.0032, braid, parent=g, sides=12)


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


# ---------------------------------------------------------------- マウス (G604)
# 公式の写真 (真上・親指の側の真横) から測った寸法 (mm)。yf = 前の端から、x = 中心から右 (親指と反対の側) へ、z = 机から
MS_LEN = 130.0
MS_TOP = [(0, 11.5), (3, 14.2), (6, 16.7), (12, 21.0), (17, 25.3), (23, 29.7), (30, 33.0), (36, 35.8), (42, 38.6), (48, 40.9),
          (54, 43.0), (60, 44.4), (66, 44.9), (73, 45.0), (80, 44.6), (87, 43.6), (93, 42.0), (98, 40.2), (103, 38.1), (108.5, 34.9),
          (114, 31.0), (119.5, 25.8), (125, 18.9), (128, 14.0), (130, 10.5)]                     # いちばん高い所
MS_BOTTOM = [(0, 9.0), (3.5, 6.6), (6, 5.4), (9, 4.3), (12, 2.8), (15, 1.7), (18, 1.2), (22, 1.0), (112, 1.0), (117, 1.4),
             (121, 2.6), (125, 5.0), (128, 7.0), (130, 9.0)]                                       # 底 (前と後ろは斜めに上がる)
MS_RIGHT = [(0, 11.0), (1.9, 14.5), (5, 20.0), (9.3, 27.5), (14, 32.0), (21.5, 35.0), (30, 36.3), (40, 37.1), (58.7, 38.2),
            (77, 39.3), (90, 39.3), (101, 37.1), (110.6, 33.0), (120, 25.5), (126.5, 16.2), (129.3, 11.5), (130, 9.0)]   # 右の輪郭
MS_LEFT = [(0, 1.5), (1.9, -2.0), (5, -6.5), (9.3, -13.0), (14, -18.0), (21.5, -21.5), (30, -22.6), (43.8, -23.5), (55, -26.0),
           (70, -27.0), (85, -26.2), (97.7, -22.5), (105, -19.5), (114, -15.3), (121.8, -7.9), (125, -3.5), (127.4, 1.4),
           (129.3, 5.5), (130, 9.0)]                                                              # 左 (親指のボタンの面)
MS_WING = [(43.8, -23.5), (46.6, -29.0), (49.4, -34.0), (55, -38.5), (64, -39.8), (77, -39.5), (86.5, -36.7), (92, -31.0),
           (97.7, -22.5)]                                                                         # 親指を乗せる張り出しの外の縁
MS_CREST = [(0, 3.0), (40, 0.0), (70, -5.0), (95, -5.0), (115, 0.0), (130, 9.0)]                   # いちばん高い所の x
# 親指のボタン (yf の範囲, z の範囲)。前の列 (G9・G6) は少し低い
MS_THUMB = [(45.0, 59.5, 26.5, 31.5), (45.0, 59.5, 21.0, 26.0), (61.0, 74.0, 29.8, 34.8), (61.0, 74.0, 24.0, 28.8),
            (75.4, 92.0, 29.5, 34.5), (75.4, 92.0, 24.0, 28.5)]
MS_PANEL = (43.4, 92.8, 19.8, 36.6)   # 親指のボタンの台 (少し出た黒い面)
MS_WHEEL = dict(x=7.1, yf=31.5, r=11.0, w=6.6, rise=3.6)   # ホイール (中心の x・yf、半径、幅、上の面から出る高さ)
MS_PILL = dict(x=6.3, yf0=41.5, yf1=66.5, w=9.4)            # ホイールの後ろの細長いボタン (前後の2つ)
MS_LED = (6.2, 71.6)


def _monotone(table, t):
    """表 [(t, 値), ...] をなめらかにつないだ値 (単調な3次エルミート補間。はみ出さない)"""
    ts = [p[0] for p in table]
    if t <= ts[0]:
        return table[0][1]
    if t >= ts[-1]:
        return table[-1][1]
    i = max(k for k in range(len(ts) - 1) if ts[k] <= t)
    d = [(table[k + 1][1] - table[k][1]) / (table[k + 1][0] - table[k][0]) for k in range(len(table) - 1)]

    def slope(k):
        if k == 0:
            return d[0]
        if k == len(table) - 1:
            return d[-1]
        if d[k - 1] * d[k] <= 0:
            return 0.0
        return 2 / (1 / d[k - 1] + 1 / d[k])   # 調和平均 (行き過ぎない)
    (t0, v0), (t1, v1) = table[i], table[i + 1]
    h = t1 - t0
    s = (t - t0) / h
    m0, m1 = slope(i), slope(i + 1)
    return ((2 * s ** 3 - 3 * s ** 2 + 1) * v0 + (s ** 3 - 2 * s ** 2 + s) * h * m0
            + (-2 * s ** 3 + 3 * s ** 2) * v1 + (s ** 3 - s ** 2) * h * m1)


def _lerp2(a, b, f):
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


_RINGS = {}


def _ring(yf):
    """前の端から yf mm の断面の輪郭 [(x, z), ...] (mm)。底を左から右へ → 右の側面を上へ → 頂を左へ → 左の側面を下へ (反時計回り)。
    点の数はどの断面も同じ (前後の断面の点を順につなぐ)"""
    key = round(yf, 3)
    if key in _RINGS:
        return _RINGS[key]
    h, zb = _monotone(MS_TOP, yf), _monotone(MS_BOTTOM, yf)
    xr, xl = _monotone(MS_RIGHT, yf), _monotone(MS_LEFT, yf)
    xc = min(max(_monotone(MS_CREST, yf), xl + 0.35 * (xr - xl)), xr - 0.35 * (xr - xl))
    wing = _monotone(MS_WING, yf) if MS_WING[0][0] < yf < MS_WING[-1][0] else xl
    w = max(0.0, xl - wing)
    f = smoothstep(w / 6)
    xw = xl - w
    t = h - zb
    rb = min(2.5, 0.25 * t)
    zR = zb + max(0.18 * t, rb + 0.05)
    zL = zb + 0.45 * t
    nr, nl = 2.3, 2.8                                 # 右の肩・左の肩の角ばり方 (超楕円の指数)
    no_wing = [(xl, zL + (zb + rb - zL) * s) for s in (0.25, 0.5, 0.75)] + [(xl, zb + rb), (xl + rb, zb)]
    with_wing = [(xl + 0.5, zL - 1.5), (xw + 3.0, 12.5), (xw, 9.5), (xw + 0.8, zb + 2.5), (xw + 3.0, zb)]
    chain = [_lerp2(a, b, f) for a, b in zip(no_wing, with_wing)]
    c5 = chain[-1]
    pts = []
    for k in range(8):                               # 底 (左の角から右の角へ)
        pts.append((c5[0] + (xr - rb - c5[0]) * k / 8, zb))
    for k in range(4):                               # 右の下の角
        a = math.radians(-90 + 90 * k / 4)
        pts.append((xr - rb + rb * math.cos(a), zb + rb + rb * math.sin(a)))
    for k in range(2):                               # 右の側面の下のまっすぐな所
        pts.append((xr, zb + rb + (zR - zb - rb) * k / 2))
    for k in range(16):                              # 右の肩から頂へ
        a = math.pi / 2 * k / 16
        pts.append((xc + (xr - xc) * math.cos(a) ** (2 / nr), zR + (h - zR) * math.sin(a) ** (2 / nr)))
    for k in range(14):                              # 頂から左の肩へ
        a = math.pi / 2 * k / 14
        pts.append((xc - (xc - xl) * math.sin(a) ** (2 / nl), zL + (h - zL) * math.cos(a) ** (2 / nl)))
    ctrl = [pts[-1], (xl, zL)] + chain + [pts[1]]   # 左の側面 (親指の張り出し) は点を通るなめらかな線
    for i in range(1, len(ctrl) - 2):
        p0, p1, p2, p3 = (Vector(c) for c in ctrl[i - 1:i + 3])
        for k in range(3):
            s = k / 3
            q = 0.5 * (2 * p1 + (p2 - p0) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s + (3 * p1 - p0 - 3 * p2 + p3) * s ** 3)
            pts.append((q.x, q.y))
    pts = [(x, max(z, zb)) for x, z in pts]
    _RINGS[key] = pts
    return pts


def _y(yf):
    """前の端から yf mm → ローカルの Y (m)。前 = +Y"""
    return (MS_LEN / 2 - yf) * MM


def _cross(ring, axis, value):
    """輪郭 ring が 軸 axis (0 = x, 1 = z) の値 value の線と交わる所の、もう一方の値の一覧"""
    out = []
    for a, b in zip(ring, ring[1:] + ring[:1]):
        if (a[axis] - value) * (b[axis] - value) < 0 or a[axis] == value:
            s = (value - a[axis]) / (b[axis] - a[axis]) if b[axis] != a[axis] else 0.0
            out.append(a[1 - axis] + (b[1 - axis] - a[1 - axis]) * s)
    return out


def _face_x(yf, z):
    """左の側面 (親指の側) の、高さ z の所の x (mm)"""
    xs = _cross(_ring(yf), 1, z)
    return min(xs) if xs else _monotone(MS_LEFT, yf)


def _top_z(x, yf):
    """上の面の、(x, yf) の所の高さ (mm)"""
    zs = _cross(_ring(yf), 0, x)
    return max(zs) if zs else _monotone(MS_TOP, yf)


def _mouse_body(root, mat):
    yfs = [0.15, 0.6, 1.3, 2.2, 3.3, 4.6, 6.0, 7.6, 9.3, 11.2, 13.3, 15.6, 18.0]
    yfs += [20.5 + 2.5 * i for i in range(10)] + [43.8, 45.2, 46.6, 48.0, 49.4, 51.2, 53.0, 55.0]
    yfs += [57.5 + 2.5 * i for i in range(14)] + [92.0, 94.0, 96.0, 97.7, 99.5, 101.5]
    yfs += [104.0 + 2.5 * i for i in range(7)] + [121.5, 123.0, 124.4, 125.7, 126.9, 127.9, 128.7, 129.3, 129.75]
    rings = [_ring(yf) for yf in yfs]
    n = len(rings[0])
    verts, faces = [], []
    for yf, ring in zip(yfs, rings):
        verts += [(x * MM, _y(yf), z * MM) for x, z in ring]
    for k in range(len(rings) - 1):
        a, b = k * n, (k + 1) * n
        for i in range(n):
            j = (i + 1) % n
            faces.append((a + i, a + j, b + j, b + i))
    for ring, yf, sign in ((rings[0], 0.0, 1), (rings[-1], MS_LEN, -1)):   # 前と後ろの端は、真ん中の点への扇でふさぐ
        c = len(verts)
        verts.append((sum(p[0] for p in ring) / n * MM, _y(yf), sum(p[1] for p in ring) / n * MM))
        base = 0 if sign > 0 else (len(rings) - 1) * n
        for i in range(n):
            j = (i + 1) % n
            faces.append((c, base + j, base + i) if sign > 0 else (c, base + i, base + j))
    obj = mesh_object("mouse_body", verts, faces, [mat], parent=root)
    me = obj.data
    for p in me.polygons:
        p.use_smooth = True
    # 上から貼る画像 (前 = 画像の上、親指の側 = 画像の左)。側面 (ほぼ垂直な面) は画像の隅の無地の所
    layer = me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        flat = p.normal.z > 0.3
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            layer.data[li].uv = (0.5 + co.x / 0.080, 0.5 + co.y / 0.130) if flat else (0.03, 0.97)
    return obj


def _on_left_face(obj, z_shear=None):
    """親指の側の部品 (x = 側面からの出っ張り (mm、- が外) で作った物) を、側面の曲がりに沿わせて置く。
    z_shear = (傾き, yf の基準): 前後で高さを変える (上の面の傾きに沿う +/- ボタン)"""
    for v in obj.data.vertices:
        x, y, z = v.co
        yf = MS_LEN / 2 - y / MM
        zz = z / MM
        if z_shear:
            zz += z_shear[0] * (yf - z_shear[1])
        v.co = ((_face_x(yf, zz) + x / MM) * MM, y, zz * MM)
    obj.data.update()


def _surface_matrix(x, yf, lift=0.0):
    """上の面の (x, yf) に、面の傾き (前後・左右) に合わせて置く変換 (ローカルの z = 面の外向き)"""
    z = _top_z(x, yf)
    d = 1.5
    sy = (_top_z(x, yf - d) - _top_z(x, yf + d)) / (2 * d)    # 前 (+Y) へ行くほど低いと +
    sx = (_top_z(x + d, yf) - _top_z(x - d, yf)) / (2 * d)
    n = Vector((-sx, -sy, 1.0)).normalized()
    rot = Vector((0, 0, 1)).rotation_difference(n).to_matrix().to_4x4()
    return Matrix.Translation((x * MM, _y(yf), (z + lift) * MM)) @ rot


def _mouse():
    e = FURNITURE["mouse"]
    root = add_empty("mouse", (e["x"], e["y"], e["z0"]), rotation_deg(e))
    body = make_material("mouse_body", "#FFFFFF", roughness=0.5, specular=0.4, texture="mouse_g604_top.png", texture_size=1.0)
    gloss = make_material("mouse_button", "#1A1A1C", roughness=0.3, specular=0.5)   # 親指のボタンなど (ツヤのある黒)
    panel = make_material("mouse_panel", "#101011", roughness=0.45)
    rubber = make_material("mouse_feet", "#0E0E0F", roughness=0.9)
    _mouse_body(root, body)

    pieces = []
    for yf0, yf1, z0, z1 in MS_THUMB:   # 親指の6つのボタン: 側面から 1.4mm 出る、角の丸いふくらんだ板
        p = soft_boxes_object("_ms_thumb", [(-1.4 * MM, 1.5 * MM, _y(yf1), _y(yf0), z0 * MM, z1 * MM, gloss, 0.0012, (0.0003, 0, 0))],
                              parent=root, cuts=6)
        _on_left_face(p)
        pieces.append(p)
    for yf0, yf1 in ((21.5, 33.0), (33.6, 44.8)):   # 左のボタンの縁の +/- (上の面の傾きに沿って後ろほど高い)
        zc = 0.5 * (_top_z(-20.0, yf0) + _top_z(-20.0, yf1)) - 2.2
        slope = (_top_z(-20.0, yf1) - _top_z(-20.0, yf0)) / (yf1 - yf0)
        p = soft_boxes_object("_ms_dpi", [(-0.9 * MM, 1.5 * MM, _y(yf1), _y(yf0), (zc - 2.2) * MM, (zc + 2.2) * MM, gloss, 0.0009,
                                           (0.0002, 0, 0))], parent=root, cuts=6)
        _on_left_face(p, (slope, (yf0 + yf1) / 2))
        pieces.append(p)
    P = MS_PILL   # ホイールの後ろの細長いボタン (前後の2つ。1つの角の丸い板に、真ん中の細い溝)
    yc = (P["yf0"] + P["yf1"]) / 2
    m = _surface_matrix(P["x"], yc, -0.5)
    pieces.append(rounded_rect_lathe("_ms_pill", P["w"] * MM, (P["yf1"] - P["yf0"]) * MM, P["w"] / 2 * MM * 0.97,
                                     [(None, 0, 0), (0, 0, 0), (0, 0.0007, 0), (0.0003, 0.0010, 0), (None, 0.0010, 0)],
                                     [gloss], parent=root, matrix=m))
    groove = make_material("mouse_groove", "#050506", roughness=0.6)
    pieces.append(solids_object("_ms_pill_groove", [rot_box(-P["w"] / 2 * MM + 0.0006, P["w"] / 2 * MM - 0.0006, -0.0002, 0.0002,
                                                            0.0006, 0.00108, groove, m)], parent=root, bevel=0))
    _join("mouse_buttons", pieces, root)

    # 親指のボタンの台 (少し出た黒い面。角の丸い長方形を側面に沿わせる)
    yf0, yf1, z0, z1 = MS_PANEL
    p = rounded_rect_lathe("mouse_panel", (yf1 - yf0) * MM, (z1 - z0) * MM, 0.006,
                           [(None, 0, 0), (0, 0, 0), (0, 0.0012, 0), (0.0004, 0.0017, 0), (None, 0.0017, 0)], [panel], parent=root)
    yc, zc = (yf0 + yf1) / 2, (z0 + z1) / 2
    for v in p.data.vertices:   # 板の (X, Y, Z) → 側面の (yf, z, 外向き)
        X, Y, Z = v.co
        yf, z = yc + X / MM, zc + Y / MM
        v.co = ((_face_x(yf, z) + 1.0 - Z / MM) * MM, _y(yf), z * MM)
    p.data.update()   # (板の X → -Y・Y → Z・Z → -X は回転なので、面の向きは外のまま)

    # ホイール: 金属の歯車 (細かい歯) を、溝の中から 3.6mm 出す
    W = MS_WHEEL
    zc = _top_z(W["x"], W["yf"]) + W["rise"] - W["r"]
    metal = make_material("mouse_wheel", "#5A5C61", roughness=0.32, metallic=0.6)
    wheel = _gear_x("mouse_wheel", (W["x"] - W["w"] / 2) * MM, (W["x"] + W["w"] / 2) * MM, _y(W["yf"]), zc * MM,
                    W["r"] * MM, 0.0007, 30, metal, root)
    wheel["lightmap_proxy"] = "mouse_body"

    led = make_material("mouse_led", "#3AA0FF", emission=2.0)
    rounded_rect_lathe("mouse_led", 0.0016, 0.0016, 0.0008, [(None, 0, 0), (0, 0, 0), (0, 0.0003, 0), (None, 0.0003, 0)],
                       [led], parent=root, matrix=_surface_matrix(*MS_LED, -0.1))
    boxes_object("mouse_feet", [(-0.018, 0.028, _y(110), _y(24), 0, 0.0012, rubber)], parent=root, bevel=0.0004)   # 底の脚 (浮かないように)
    return root


def build_keyboard_mouse():
    return _keyboard(), _mouse()
