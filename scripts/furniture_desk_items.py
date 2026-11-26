"""デスク2の上の小物 (2026-10-25 ユーザー指定。当時の写真とは違う)。モニター・キーボード・マウス以外の物。

- 文庫本2冊 (メインモニターの台座の左右。どちらも台座の青い辺に接する): 左 (東) =「物理さんで無双してたらモテモテになりました (1)」、
  右 (西) = 同じ (2)。表紙を上に、頭を台座の奥へ。表紙・裏表紙・背・紙の小口を1枚の画像 (textures/book_physics1.jpg・book_physics2.jpg。
  tools/make_desk_items.py が書影から描く) に並べ、面ごとに貼る (layout.book_atlas)
- セリアの木製のコースター (ラバーウッドコースター ロゴ柄 角): 本 (2) のさらに右 (西)、マウスの奥。角の丸い四角の板の上面に
  白っぽい木目と焼き印のような ORIGINAL TASTE (textures/coaster_top.jpg)。大きさは写真からの見積もり (9.5cm 角・厚み 9mm)
- ダイソーのペンスタンド (チャコールグレー、サイズ L。商品は 9 x 9 x 11cm だが、2026-10-27 にユーザー指定で縦横 1cm ずつ小さく 8 x 8 x 11cm。
  色もユーザー指定でチャコールより明るいグレー (帯の画像 penstand_band.jpg と内側の色)):
  コースターの奥。PP の帯を互い違いに編んだ四角柱
  (各面 横2 x 縦4 の帯のマス。横の帯と縦の帯が市松に表へ出る。上の縁は帯で巻く。帯の表面の筋は textures/penstand_band.jpg)。
  中に白い柄のハサミ (刃は下)・黒いボールペン2本・赤ペン
- Amazon Echo Show 5 (第3世代 チャコール): 本 (1) とサブモニターの台の間。画面を座る人の方へ向ける。後ろへ 12°傾いた黒いガラスの板
  (148 x 86mm。右上にカメラ) に、光る時計の画面 (textures/screen_echo.png = tools/make_screens.py)。後ろは布張りのくさび形。電源の線は机の奥へ
- 新聞紙で折った卓上のゴミ箱 (2026-10-27 ユーザー指定。参考の動画「畳める！チラシで作る深めのゴミ箱」): Echo Show の前。上の開いた箱 (9cm 角・高さ 8.1cm)。
  壁の折り目と三角の折り返しは画像 (textures/paper_trash.jpg。面の並びは layout.trash_atlas)
- サブモニターの台の小物入れの中身 (2026-10-27 ユーザー指定): 左 = 綿棒を詰めた透明な円筒のケース / 右 = 畳んだ紙のゴミ箱のストック
  (畳むと底の正方形の薄い板になる。新聞紙とチラシ。縁を手前に向けて立て、残りの数が数えられる)。小物入れの位置は layout.box_cases
位置・大きさは layout.py (book1, book2, coaster, pen_stand, echo_show, trash_box)。
構成: Empty `desk2` の下の、部屋の座標の Empty `desk2_items` の下に、物ごとの Empty `desk2_book1` `desk2_book2` `desk2_coaster` `desk2_pen_stand`
`desk2_echo_show` `desk2_trash_box` (layout の位置と向き。ローカル座標: 原点 = 足元の中心 / 正面 = -Y) と、その下のメッシュ。クリックするとデスク2になる。
小物入れの中身は Empty `monitor_boxes` (台のローカル座標) の下の Empty `monitor_boxes_items` の下 (`monitor_boxes_swab_case` `_swab_lid` `_swabs`
`monitor_boxes_trash_stock1`〜)。台はクリック対象に未登録
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props import *
from layout import FURNITURE, VIEW, book_atlas, box_cases, rotation_deg, trash_atlas
from room_spec import CEILING_LIGHT, ROOM_H

BOOKS = {"book1": "book_physics1.jpg", "book2": "book_physics2.jpg"}
PEN_RIM = 0.0135     # ペン立ての上の縁の帯の高さ
PEN_BAND_T = 0.0016  # 編んだ帯の厚み (芯の外へ出る分)
ECHO_TILT = 12.0     # Echo Show の前の板の傾き (度)
ECHO_PANEL = (0.148, 0.086, 0.007)   # 前の板の幅・高さ・厚み
ECHO_SCREEN = (0.1249, 0.0625)       # 画面 (5.5型、横長 2:1)
ECHO_GLOW = 0.55
TRASH_WALL = 0.0009    # 紙のゴミ箱の壁の厚み (紙が2〜3枚重なる)
TRASH_FLOOR = 0.0015   # 底の厚み
STOCK_T = 0.0028       # 畳んだゴミ箱 1枚の厚み (コースターより薄い。ユーザー指定「少し薄いコースターサイズ」)
STOCK = ("news", "blue", "news", "news", "red", "news", "blue", "news", "red")   # 小物入れに立てて並べた畳んだゴミ箱の紙 (真ん中の仕切りの側から)
SWAB_CASE = (0.034, 0.079)          # 綿棒のケースの半径・本体の高さ (直径 6.8cm。ふたを入れて高さ 8.4cm)
SWAB_LEN, SWAB_TIP = 0.075, (0.0062, 0.0024)   # 綿棒の長さ・先の綿の (長さの半分, 半径)


def _item(g, name):
    """layout の位置・向きの Empty (desk2_<名前>)。g = 部屋の座標の Empty"""
    e = FURNITURE[name]
    item = add_empty(f"desk2_{name}", (e["x"], e["y"], e["z0"]), rotation_deg(e))
    item.parent = g
    return item


def _edge_profile(t, r_bottom, r_top, n=3):
    """角の丸い板の断面 (rounded_rect_lathe の profile): 厚み t、下の縁の丸み r_bottom・上の縁の丸み r_top"""
    prof = [(None, 0.0, 0)]
    for k in range(n + 1):
        a = math.pi / 2 * k / n
        prof.append((r_bottom * (1 - math.sin(a)), r_bottom * (1 - math.cos(a)), 0))
    for k in range(n + 1):
        a = math.pi / 2 * k / n
        prof.append((r_top * (1 - math.cos(a)), t - r_top + r_top * math.sin(a), 0))
    prof.append((None, t, 0))
    return prof


# ---------------------------------------------------------------- 文庫本
def _book(g, name):
    e = FURNITURE[name]
    item = _item(g, name)
    w, l, t = e["w"], e["d"], e["h"]
    mat = picture_material(f"{name}_print", BOOKS[name], roughness=0.42, specular=0.45)   # 表紙はツヤのあるカバー
    obj = boxes_object(f"desk2_{name}_body", [(-w / 2, w / 2, -l / 2, l / 2, 0, t, mat)], parent=item, bevel=0.0008)
    rects, size = book_atlas(name)
    atlas_box_uvs(obj, (-w / 2, w / 2, -l / 2, l / 2, 0, t), rects, size)


# ---------------------------------------------------------------- コースター
def _coaster(g):
    e = FURNITURE["coaster"]
    item = _item(g, "coaster")
    s = e["w"]
    mat = picture_material("coaster_top", "coaster_top.jpg", roughness=0.7, specular=0.3)
    obj = rounded_rect_lathe("desk2_coaster_body", s, s, 0.012, _edge_profile(e["h"], 0.0012, 0.0016), [mat], parent=item)
    layer = obj.data.uv_layers.new(name="UVMap")   # 上から貼る (字の上 = 画像の上 = ローカルの +Y = 奥)
    for loop in obj.data.loops:
        co = obj.data.vertices[loop.vertex_index].co
        layer.data[loop.index].uv = (0.5 + co.x / s, 0.5 + co.y / s)


# ---------------------------------------------------------------- ペン立て
def _band_uvs(obj, vertical):
    """編んだ帯の UV (1 = 1m。材質の texture_size で帯の画像1枚の大きさにする)。帯の向き = 画像の横。
    vertical: 縦の帯 (画像を 90°回して貼る)"""
    me = obj.data
    layer = me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        n = p.normal
        for li in p.loop_indices:
            x, y, z = me.vertices[me.loops[li].vertex_index].co
            along = x if abs(n.y) >= abs(n.x) else y      # 面に沿った横の位置
            if abs(n.z) > max(abs(n.x), abs(n.y)):
                along, z = x, y
            layer.data[li].uv = (z, along) if vertical else (along, z)


def _pen(name, base, top, spin, body_color, grip_color, parent):
    """ボールペン (先が下)。base = 先の位置、top = ノックの方向の点 (ペン立てのローカル座標)。spin = クリップの向き (度)"""
    metal = make_material("pen_metal", "#B9BCC0", roughness=0.3, metallic=0.7) if "pen_metal" not in bpy.data.materials \
        else bpy.data.materials["pen_metal"]
    body = make_material(f"{name}_body", body_color, roughness=0.35, specular=0.5)
    grip = make_material(f"{name}_grip", grip_color, roughness=0.7)
    d = (Vector(top) - Vector(base)).normalized()
    m = Matrix.Translation(base) @ Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4() @ Matrix.Rotation(math.radians(spin), 4, 'Z')
    # (半径, 高さ, 材質): 先の金具 → 握る所のゴム → 軸 → 上のノック
    prof = [(0, 0, 0), (0.0005, 0.0004, 0), (0.0011, 0.0028, 2), (0.0040, 0.0075, 2), (0.0050, 0.011, 2), (0.0050, 0.042, 2),
            (0.0048, 0.044, 1), (0.0049, 0.118, 1), (0.0045, 0.124, 0), (0.0030, 0.1265, 0), (0.0028, 0.1355, 0),
            (0.0020, 0.1375, 0), (0, 0.1375, 0)]
    lathe_object(name, prof, [metal, body, grip], parent=parent, segments=16, matrix=m)
    solids_object(f"{name}_clip", [rot_box(0.0047, 0.0058, -0.0010, 0.0010, 0.090, 0.126, metal, m)], parent=parent, bevel=0.0003)


def _scissors(name, pivot, lean, yaw, parent):
    """白い柄のハサミ (刃を下にして立てる)。pivot = 留め金の位置。ハサミの面はローカルの XZ 面"""
    white = make_material("scissors_handle", "#EDEDEA", roughness=0.45, specular=0.45)
    steel = make_material("scissors_blade", "#C9CCD0", roughness=0.25, metallic=0.8)
    m = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(lean), 4, 'Y')
    solids = []
    for s in (-1, 1):   # 閉じた刃2枚 (下へ細くなる)
        y0, y1 = (0.0, 0.0011) if s > 0 else (-0.0011, 0.0)
        pts = [(-0.0045, y0, -0.004), (0.0045, y0, -0.004), (0.0045, y1, -0.004), (-0.0045, y1, -0.004),
               (-0.0045, y0, 0.006), (0.0045, y0, 0.006), (0.0045, y1, 0.006), (-0.0045, y1, 0.006)]
        solids.append(([tuple(m @ Vector(p)) for p in pts], steel))
        tip = [(-0.0045, y0, -0.088), (-0.0025, y0, -0.088), (-0.0025, y1, -0.088), (-0.0045, y1, -0.088),
               (-0.0045, y0, -0.004), (0.0045, y0, -0.004), (0.0045, y1, -0.004), (-0.0045, y1, -0.004)]
        solids.append(([tuple(m @ Vector(p)) for p in tip], steel))
    solids_object(f"{name}_blades", solids, parent=parent, bevel=0.0002)
    rivet = make_material("scissors_rivet", "#8E9196", roughness=0.3, metallic=0.8)
    lathe_object(f"{name}_rivet", [(0, -0.0016, 0), (0.0022, -0.0016, 0), (0.0022, 0.0016, 0), (0, 0.0016, 0)], [rivet], parent=parent,
                 segments=12, matrix=m @ Matrix.Rotation(math.radians(90), 4, 'X'))

    def ellipse(cx, cz, rx, rz, n=20):
        return [tuple(m @ Vector((cx + rx * math.cos(2 * math.pi * k / n), 0, cz + rz * math.sin(2 * math.pi * k / n)))) for k in range(n)]
    loops = [ellipse(-0.0125, 0.046, 0.0115, 0.020), ellipse(0.0105, 0.040, 0.0085, 0.0135)]   # 指の輪 (大)・親指の輪 (小)
    tubes_object(f"{name}_handles", loops, 0.0032, white, parent=parent, sides=10, closed=True)
    shanks = [[tuple(m @ Vector(p)) for p in ((-0.0015, 0, 0.004), (-0.006, 0, 0.016), (-0.0105, 0, 0.0265))],
              [tuple(m @ Vector(p)) for p in ((0.0015, 0, 0.004), (0.006, 0, 0.016), (0.0098, 0, 0.0268))]]
    tubes_object(f"{name}_shanks", shanks, 0.0034, white, parent=parent, sides=10)


def _pen_stand(g):
    e = FURNITURE["pen_stand"]
    item = _item(g, "pen_stand")
    hw, H = e["w"] / 2, e["h"]
    band = make_material("pen_stand_band", "#FFFFFF", roughness=0.8, specular=0.35, texture="penstand_band.jpg", texture_size=0.022)
    liner = make_material("pen_stand_liner", "#46474B", roughness=0.85)   # 内側の芯 (帯の暗い所くらいの灰色)
    core = hw - PEN_BAND_T
    boxes_object("desk2_pen_stand_core", open_box(-core, core, -core, core, 0, H - 0.003, 0.002, liner, bottom=0.003),
                 parent=item, bevel=0.0006)
    rows, gap = 4, 0.0009
    z0, z1 = 0.0004, H - PEN_RIM - 0.0003
    th = (z1 - z0) / rows
    tiles = {False: [], True: []}   # 横の帯 / 縦の帯
    for f, (axis, sign) in enumerate((("y", -1), ("x", 1), ("y", 1), ("x", -1))):   # 前・右・奥・左
        out, inn = sign * hw, sign * (core - 0.001)
        for c in range(2):
            a0, a1 = -hw + c * hw + gap / 2, -hw + (c + 1) * hw - gap / 2
            for r in range(rows):
                za, zb = z0 + r * th + gap / 2, z0 + (r + 1) * th - gap / 2
                if axis == "y":
                    box, bulge = (a0, a1, min(out, inn), max(out, inn)), (0, 0.0005, 0)
                else:
                    box, bulge = (min(out, inn), max(out, inn), a0, a1), (0.0005, 0, 0)
                tiles[(c + r + f) % 2 == 0].append((*box, za, zb, band, 0.0012, bulge))
    o, i, zr = hw + 0.0003, core - 0.0032, H - PEN_RIM
    tiles[False] += [(-o, o, -o, -i, zr, H, band, 0.0016, (0, 0.0004, 0)), (-o, o, i, o, zr, H, band, 0.0016, (0, 0.0004, 0)),   # 上の縁 (帯で巻く)
                     (-o, -i, -i, i, zr, H, band, 0.0016, (0.0004, 0, 0)), (i, o, -i, i, zr, H, band, 0.0016, (0.0004, 0, 0))]
    for vertical, items in tiles.items():
        obj = soft_boxes_object(f"desk2_pen_stand_weave_{'v' if vertical else 'h'}", items, parent=item, cuts=5)
        _band_uvs(obj, vertical)
    # 中身 (ペン立てのローカル座標。-Y = 座る人の側)
    _scissors("desk2_scissors", (-0.008, 0.012, H + 0.011), -7.0, 35.0, item)
    _pen("desk2_pen_black1", (0.016, -0.012, 0.003), (0.024, -0.020, 0.14), 200, "#1B1B1D", "#2B2B2E", item)
    _pen("desk2_pen_black2", (0.020, 0.016, 0.003), (0.030, 0.026, 0.14), 40, "#1B1B1D", "#2B2B2E", item)
    _pen("desk2_pen_red", (-0.018, -0.016, 0.003), (-0.028, -0.026, 0.14), 140, "#C8232C", "#8E1A20", item)


# ---------------------------------------------------------------- Echo Show 5
def _echo(g):
    e = FURNITURE["echo_show"]
    item = _item(g, "echo_show")
    W, D = e["w"], e["d"]
    pw, ph, pt = ECHO_PANEL
    a = math.radians(ECHO_TILT)
    ex, ey, ez = Vector((1, 0, 0)), Vector((0, math.sin(a), math.cos(a))), Vector((0, -math.cos(a), math.sin(a)))   # 板の 横・上・前
    bottom = Vector((0, -D / 2, 0.002))                         # 板の前の面の下の縁
    back_center = bottom + ey * (ph / 2) - ez * pt
    M = Matrix.Translation(back_center) @ Matrix((ex, ey, ez)).transposed().to_4x4()   # 板の座標 (X 横・Y 上・Z 前、原点 = 裏の面の中心)
    glass = make_material("echo_glass", "#0A0A0C", roughness=0.15, specular=0.6)
    rounded_rect_lathe("desk2_echo_panel", pw, ph, 0.010, _edge_profile(pt, 0.001, 0.0015), [glass], parent=item, matrix=M)
    screen = make_material("echo_screen", "#FFFFFF", roughness=0.15, emission=ECHO_GLOW, texture="screen_echo.png", emission_texture=True)
    sw, sh = ECHO_SCREEN
    image_quad("desk2_echo_screen", sw, sh, screen,
               M @ Matrix.Translation((0, -sh / 2, pt + 0.0002)) @ Matrix.Rotation(math.radians(-90), 4, 'X'), parent=item)
    lens = make_material("echo_camera", "#1C2026", roughness=0.1, specular=0.7)
    rounded_rect_lathe("desk2_echo_camera", 0.0024, 0.0024, 0.0012, [(None, 0, 0), (0, 0, 0), (0, 0.0003, 0), (None, 0.0003, 0)],
                       [lens], parent=item, matrix=M @ Matrix.Translation((0.0595, 0.0355, pt - 0.0001)))
    _echo_body(item)
    _echo_cable(item)


def _echo_body(item):
    """布張りの後ろの部分: 横から見た形 (前は板の裏に沿う直線、後ろは丸い曲線) を左右へ伸ばし、両端を丸める"""
    back = [(36.6, 0.5), (36.9, 7.0), (35.6, 19.0), (32.2, 32.0), (25.8, 47.5), (16.5, 62.5), (5.5, 74.0), (-5.0, 80.0), (-13.0, 82.0)]
    pts = [(-30.2 + (36.6 + 30.2) * k / 8, 0.5) for k in range(8)]        # 底 (前から後ろへ)
    for i in range(len(back) - 1):                                        # 後ろの曲線 (点を通るなめらかな線)
        p0, p1, p2 = back[max(i - 1, 0)], back[i], back[i + 1]
        p3 = back[min(i + 2, len(back) - 1)]
        for k in range(3):
            s = k / 3
            pts.append(tuple(0.5 * (2 * b + (c - a_) * s + (2 * a_ - 5 * b + 4 * c - d) * s * s + (3 * b - a_ - 3 * c + d) * s ** 3)
                             for a_, b, c, d in zip(p0, p1, p2, p3)))
    pts += [(-13.0 + (-30.2 + 13.0) * k / 6, 82.0 + (0.5 - 82.0) * k / 6) for k in range(6)]   # 前 (板の裏に沿って下へ)
    prof = [(y * 0.001, z * 0.001) for y, z in pts]
    n = len(prof)
    cy = sum(p[0] for p in prof) / n
    cz = sum(p[1] for p in prof) / n

    def inset(d):
        out = []
        for i, (y, z) in enumerate(prof):   # 両隣の辺の内向きの法線の平均の向きへ d だけ寄せる
            (y0, z0), (y1, z1) = prof[i - 1], prof[(i + 1) % n]
            ny, nz = -(z1 - z0), (y1 - y0)
            ln = math.hypot(ny, nz) or 1.0
            ny, nz = ny / ln, nz / ln
            if (cy - y) * ny + (cz - z) * nz < 0:
                ny, nz = -ny, -nz
            out.append((y + ny * d, max(0.0005, z + nz * d)))
        return out
    hw, r = 0.073, 0.007
    stations = [(-(hw - r + r * math.sin(math.pi / 2 * k / 6)), r * (1 - math.cos(math.pi / 2 * k / 6))) for k in range(6, -1, -1)]
    stations += [(-x, d) for x, d in reversed(stations)]
    verts, faces = [], []
    for x, d in stations:
        verts += [(x, y, z) for y, z in inset(d)]
    for k in range(len(stations) - 1):
        a, b = k * n, (k + 1) * n
        for i in range(n):
            j = (i + 1) % n
            faces.append((a + i, a + j, b + j, b + i))
    for k, sign in ((0, -1), (len(stations) - 1, 1)):   # 両端のふた
        ring = verts[k * n:(k + 1) * n]
        c = len(verts)
        verts.append((stations[k][0], sum(v[1] for v in ring) / n, sum(v[2] for v in ring) / n))
        for i in range(n):
            j = (i + 1) % n
            faces.append((c, k * n + j, k * n + i) if sign < 0 else (c, k * n + i, k * n + j))
    fabric = fabric_material("echo_fabric", "cotton", (54, 54, 58))
    obj = mesh_object("desk2_echo_body", verts, faces, [fabric], parent=item)
    for p in obj.data.polygons:
        p.use_smooth = True
    obj.data.set_sharp_from_angle(angle=math.radians(50))


def _echo_cable(item):
    """電源の線: 後ろの下から出て、机の奥の端から下へ"""
    e = FURNITURE["echo_show"]
    a = math.radians(rotation_deg(e))
    w = lambda lx, ly, z: (e["x"] + lx * math.cos(a) - ly * math.sin(a), e["y"] + lx * math.sin(a) + ly * math.cos(a), e["z0"] + z)
    desk_back = FURNITURE["desk2"]["y"] - FURNITURE["desk2"]["d"] / 2
    p0, p1 = w(0.040, 0.034, 0.0065), w(0.040, 0.046, 0.0022)
    pts = [p0, p1, (p1[0] + 0.004, (p1[1] + desk_back) / 2, e["z0"] + 0.0022), (p1[0] + 0.006, desk_back + 0.002, e["z0"] + 0.0022),
           (p1[0] + 0.006, desk_back - 0.002, e["z0"] - 0.002), (p1[0] + 0.006, desk_back - 0.004, e["z0"] - 0.15)]
    g = world_group("desk2_echo_cable_group", item)
    tubes_object("desk2_echo_cable", [bezier(pts[0], pts[1], pts[2], 4)[:-1] + pts[2:]], 0.0018,
                 make_material("echo_cable", "#1E1E20", roughness=0.6), parent=g, sides=8)


# ---------------------------------------------------------------- 紙のゴミ箱 (2026-10-27)
def _paper():
    mats = bpy.data.materials
    return mats["paper_trash"] if "paper_trash" in mats else picture_material("paper_trash", "paper_trash.jpg", roughness=0.9, specular=0.25)


def _atlas_uv(rect, size, u, v):
    """画像の中の長方形 rect (画素) の (u, v) (0〜1。v = 上) の UV"""
    px0, py0, px1, py1 = rect
    return (px0 + u * (px1 - px0)) / size[0], 1 - (py1 - v * (py1 - py0)) / size[1]


def _trash_box(g):
    """新聞紙で折った卓上のゴミ箱 (上の開いた立方体。参考の動画の畳める形)。紙の壁は上の縁ほど少し外や内へたわむ。
    折り目と三角の折り返しは画像 (paper_trash.jpg の out*・in*・bottom) に描いてある。壁 (高さ < 1辺) には正方形の枠の下から高さの分を貼る
    (45° の折り目は底の角から始まる)。
    上の縁は、壁の外と内から急な2面で山にする (平らな縁や 45° の面は底と同じ島に入り、細すぎて底の端の暗い光を拾って黒い線に見えたため。
    急な面なら壁の島に入る)"""
    e = FURNITURE["trash_box"]
    item = _item(g, "trash_box")
    s, h, t, tb = e["w"], e["h"], TRASH_WALL, TRASH_FLOOR
    a = s / 2
    rects, size = trash_atlas()
    rng = random.Random(27)
    verts, index, faces, uvs, floor = [], {}, [], [], []

    def face(pts, uv):   # 同じ位置の頂点は共有する (たわんだ壁をなめらかに塗るため。UV は面の角ごと)
        ids = []
        for p in pts:
            key = tuple(round(c, 7) for c in p)
            if key not in index:
                index[key] = len(verts)
                verts.append(p)
            ids.append(index[key])
        faces.append(tuple(ids))
        uvs.append(uv)

    nu, nv = 6, 5
    hw = h - 1.5 * t                               # 壁の面の上端 (その上は縁の山。山の面は水平から 72°)
    zo = lambda v: v * hw / s                      # 外の面の高さの割合 → 画像の縦の位置 (枠の下の端からの高さ / 1辺)
    zv = lambda v: (tb + v * (hw - tb)) / s        # 内の面 (底の厚みの分だけ上から始まる)
    for i, ((cx, cy), (ex, ey)) in enumerate((((-a, -a), (1, 0)), ((a, -a), (0, 1)), ((a, a), (-1, 0)), ((-a, a), (0, -1)))):   # 前・右・奥・左
        nx, ny = ey, -ex                                              # 壁の外向き
        bow = rng.uniform(0.5, 1.1) * 0.001 * rng.choice((-1, 1))      # 上の縁の真ん中のたわみ (外 = 正)

        def pt(u, v, inner):   # 壁の外の面 (u = 外から見て左から右、v = 下から上) の点。inner なら内の面
            w = bow * math.sin(math.pi * u) * math.sin(math.pi * v / 2) ** 1.5
            uu, z = (t + u * (s - 2 * t), tb + v * (hw - tb)) if inner else (u * s, v * hw)
            w -= t if inner else 0
            return (cx + ex * uu + nx * w, cy + ey * uu + ny * w, z)

        def ridge(u):   # 縁の山の頂 (外と内の面の上端の真ん中、高さ h)
            p, q = pt(u, 1, False), pt(u, 1, True)
            return ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, h)

        for iu in range(nu):
            u0, u1 = iu / nu, (iu + 1) / nu
            for iv in range(nv):
                v0, v1 = iv / nv, (iv + 1) / nv
                face([pt(u0, v0, False), pt(u1, v0, False), pt(u1, v1, False), pt(u0, v1, False)],
                     [_atlas_uv(rects[f"out{i}"], size, u, zo(v)) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))])
                face([pt(u1, v0, True), pt(u0, v0, True), pt(u0, v1, True), pt(u1, v1, True)],      # 内の面 (内から見て左右が逆)
                     [_atlas_uv(rects[f"in{i}"], size, 1 - u, zv(v)) for u, v in ((u1, v0), (u0, v0), (u0, v1), (u1, v1))])
            face([pt(u0, 1, False), pt(u1, 1, False), ridge(u1), ridge(u0)],                           # 上の縁の外の 45°
                 [_atlas_uv(rects[f"out{i}"], size, u, v) for u, v in ((u0, zo(1)), (u1, zo(1)), (u1, h / s), (u0, h / s))])
            face([ridge(u0), ridge(u1), pt(u1, 1, True), pt(u0, 1, True)],                              # 上の縁の内の 45°
                 [_atlas_uv(rects[f"in{i}"], size, 1 - u, v) for u, v in ((u0, h / s), (u1, h / s), (u1, zv(1)), (u0, zv(1)))])
            floor.append(pt(u0, 0, True))
    face([(-a, -a, 0.0), (-a, a, 0.0), (a, a, 0.0), (a, -a, 0.0)],                                            # 外の底
         [_atlas_uv(rects["plain"], size, u, v) for u, v in ((0, 0), (0, 1), (1, 1), (1, 0))])
    face(floor, [_atlas_uv(rects["bottom"], size, (x + a) / s, (y + a) / s) for x, y, _ in floor])    # 内の底 (上から見て反時計回り)
    obj = mesh_object("desk2_trash_box_body", verts, faces, [_paper()], parent=item)
    layer = obj.data.uv_layers.new(name="UVMap")
    for p, uv in zip(obj.data.polygons, uvs):
        for li, co in zip(p.loop_indices, uv):
            layer.data[li].uv = co
        p.use_smooth = True
    obj.data.set_sharp_from_angle(angle=math.radians(40))


# ---------------------------------------------------------------- サブの台の小物入れの中身 (2026-10-27)
def _box_contents():
    """サブモニターの台の小物入れの中身 (ユーザー指定): 左 = 綿棒を詰めた透明な円筒のケース / 右 = 畳んだ紙のゴミ箱のストック"""
    items = add_empty("monitor_boxes_items")
    items.parent = bpy.data.objects["monitor_boxes"]   # 台のローカル座標 (正面 = -Y、X = 正面から見て右)
    cases, t = box_cases()
    _swab_case(items, cases["left"], t)
    _trash_stock(items, cases["right"], t)


def _swab_case(items, case, t):
    """透明な円筒のケース (本体とかぶせるふた) に、綿棒を立ててぎっしり詰める。小物入れの奥の板に寄せて置く。
    綿棒は細かくてライトマップの島が作れないので、小物入れの底のケースの手前の光を借り (lightmap_proxy)、
    面ごとの陰 (束の奥ほど暗い・明かりの方を向く面ほど明るい) は明るさの段階の画像 shade_ramp.png の位置 (UV) で付ける
    (1色だと束が1つの灰色の円柱に見えるため)"""
    x0, x1, y0, y1, _ = case
    R, H = SWAB_CASE
    cx, cy = (x0 + x1) / 2 - 0.0035, y1 - t - 0.002 - R
    clear = make_material("swab_case_clear", "#E8EEF2", roughness=0.08, alpha=0.15)   # 名前に clear → ビューアで明るい薄い膜
    m = Matrix.Translation((cx, cy, t))
    lathe_object("monitor_boxes_swab_case", [(0, 0, 0), (R, 0, 0), (R, H, 0), (R - 0.001, H, 0), (R - 0.001, 0.0012, 0), (0, 0.0012, 0)],
                 [clear], parent=items, segments=40, matrix=m)
    lathe_object("monitor_boxes_swab_lid", [(0, H + 0.0033, 0), (R + 0.0002, H + 0.0033, 0), (R + 0.0002, H - 0.0055, 0),
                                            (R + 0.0012, H - 0.0055, 0), (R + 0.0012, H + 0.0045, 0), (0, H + 0.0045, 0)],
                 [clear], parent=items, segments=40, matrix=m)
    cotton = make_material("swab_cotton", "#FBFBF8", roughness=1.0, specular=0.2, texture="shade_ramp.png")
    stick = make_material("swab_stick", "#F1F0EA", roughness=0.7, texture="shade_ramp.png")
    rng = random.Random(5)
    lh, rt = SWAB_TIP
    pitch, rmax = 0.005, R - 0.001 - rt - 0.001
    spots = [((i + 0.5 * (j % 2)) * pitch, j * pitch * 0.866) for j in range(-8, 9) for i in range(-8, 9)]
    verts, faces, mats = [], [], []

    def ring(c, d, e1, e2, r, n, phase=0.0):
        out = []
        for k in range(n):
            a = 2 * math.pi * k / n + phase
            out.append(len(verts))
            verts.append(tuple(c + (e1 * math.cos(a) + e2 * math.sin(a)) * r))
        return out

    for x, y in spots:
        if math.hypot(x, y) > rmax:
            continue
        d = Vector((rng.uniform(-0.008, 0.008), rng.uniform(-0.008, 0.008), 1)).normalized()   # わずかに傾く
        e1 = d.cross(Vector((0, 1, 0))).normalized()
        e2 = d.cross(e1)
        base = Vector((cx + x, cy + y, t + 0.0013))
        a, b = ring(base + d * 0.004, d, e1, e2, 0.0009, 4, math.pi / 4), ring(base + d * (SWAB_LEN - 0.004), d, e1, e2, 0.0009, 4, math.pi / 4)
        for k in range(4):   # 軸 (紙の細い棒)
            faces.append((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
            mats.append(1)
        ends = [SWAB_LEN - lh] + ([lh] if math.hypot(x, y) > rmax - 0.006 else [])   # 先の綿 (下は外側の列だけ。内側の下は見えない)
        for zc in ends:
            c = base + d * zc
            bot, top = len(verts), len(verts) + 1
            verts += [tuple(c - d * lh), tuple(c + d * lh)]
            rings = [ring(c + d * (f * lh), d, e1, e2, rt * math.sqrt(1 - f * f), 6) for f in (-0.6, 0.0, 0.6)]
            for k in range(6):
                k1 = (k + 1) % 6
                faces.append((bot, rings[0][k1], rings[0][k]))
                faces.append((top, rings[2][k], rings[2][k1]))
                for r0, r1 in zip(rings, rings[1:]):
                    faces.append((r0[k], r0[k1], r1[k1], r1[k]))
                mats += [0] * 4
    obj = mesh_object("monitor_boxes_swabs", verts, faces, [cotton, stick], face_mats=mats, parent=items)
    e = FURNITURE["monitor_boxes"]
    inv = Matrix.Rotation(math.radians(-rotation_deg(e)), 3, 'Z')   # 部屋の座標 → 台のローカル座標
    origin = Vector((e["x"], e["y"], e["z0"]))
    eye = inv @ (Vector(VIEW["eye"]) - origin)
    lamp = inv @ (Vector((CEILING_LIGHT["x"], CEILING_LIGHT["y"], ROOM_H)) - origin)
    front = Vector((eye.x - cx, eye.y - cy)).normalized()   # 束の中心から目の方 (水平)
    layer = obj.data.uv_layers.new(name="UVMap")
    for p in obj.data.polygons:
        p.use_smooth = True
        c = p.center
        back = rmax - Vector((c.x - cx, c.y - cy)).dot(front)   # 目の側の端の綿棒からの奥行き (m)
        light = max(0.0, p.normal.dot((lamp - c).normalized()))
        shade = (0.3 + 0.7 * math.exp(-max(0.0, back) / 0.008)) * (0.55 + 0.45 * light)
        for li in p.loop_indices:
            layer.data[li].uv = (shade, 0.5)
    obj["lightmap_proxy"] = "monitor_boxes_body"
    obj["lightmap_proxy_at"] = (cx, cy - R - 0.006, t)   # 小物入れの底の、ケースのすぐ手前


def _trash_stock(items, case, t):
    """畳んだ紙のゴミ箱 (底の1辺の正方形の薄い板。表に斜めの折り返し) を、縁を口 (手前) へ向けて立てて並べる
    (ユーザー指定「水平方向に 90° 回転させた状態でまとめてストック。残りのゴミ箱の数が数えられる状態」)。
    真ん中の仕切りの側へ寄せて少しもたれさせ、表は外 (右の壁の方) へ向ける。板の1辺 (9cm) は小物入れの奥行 (内のり 8.2cm) より長いので、
    奥の板に突き当てて、口から 1cm ほどはみ出す (台のふたの縁より下なので当たらない)"""
    x0, x1, y0, y1, _ = case
    s = FURNITURE["trash_box"]["w"]
    rects, size = trash_atlas()
    mat = _paper()
    rng = random.Random(9)
    tilt = [math.radians(2.5 + rng.uniform(-0.6, 0.6)) for _ in STOCK]   # 仕切りの方へもたれる角度
    yaw = [math.radians(rng.uniform(-0.6, 0.6)) for _ in STOCK]          # 上から見たねじれ
    a = tilt[0]
    x = x0 + t + 0.0004 + STOCK_T / 2 * math.cos(a) + s * math.sin(a)   # 仕切りの側の1枚目の位置: 上の縁が仕切りに触れる
    for k, paper in enumerate(STOCK):   # 仕切りの側から外へ
        if k:   # 1つ仕切りの側の板 (k-1) との間: 高さ 0〜s のどこでも 0.4mm 以上あける
            f, b = tilt[k], tilt[k - 1]
            x += (STOCK_T / 2 * (1 / math.cos(f) + 1 / math.cos(b)) + 0.0004 + s * max(0.0, math.tan(f) - math.tan(b))
                  + s / 2 * (abs(math.sin(yaw[k])) + abs(math.sin(yaw[k - 1]))))
        faces = {"front": rects[f"fold_{paper}"], "back": rects[f"fold_{paper}"], "top": rects[f"edge_h_{paper}"],
                 "bottom": rects[f"edge_h_{paper}"], "left": rects[f"edge_v_{paper}"], "right": rects[f"edge_v_{paper}"], "plain": rects["plain"]}
        box = (-s / 2, s / 2, -STOCK_T / 2, STOCK_T / 2, 0, s)
        obj = boxes_object(f"monitor_boxes_trash_stock{k + 1}", [(*box, mat)], parent=items, bevel=0.0004)
        atlas_box_uvs(obj, box, faces, size)
        y = y1 - t - 0.0004 - s / 2 - rng.uniform(0.0, 0.003)   # 奥の板に突き当てる (はみ出しは少しずつ不揃い)
        # 板のローカル: 表 = -Y・縁 (left) = -X → Z まわりに 90° 回すと、表が +X (外)・縁が -Y (口) を向く。その後 仕切り (-X) の方へもたれる
        obj.matrix_basis = (Matrix.Translation((x, y, t + 0.0002)) @ Matrix.Rotation(-tilt[k], 4, 'Y') @
                            Matrix.Rotation(math.radians(90) + yaw[k], 4, 'Z'))


def build_desk_items():
    g = world_group("desk2_items", bpy.data.objects["desk2"])
    for name in BOOKS:
        _book(g, name)
    _coaster(g)
    _pen_stand(g)
    _echo(g)
    _trash_box(g)
    _box_contents()
    return g
