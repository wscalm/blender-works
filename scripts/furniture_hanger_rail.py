"""南壁のフックのレール (写真 reference/IMG_1099)。突っ張り棚の西の柱の隣から、デスクの幅 (1.2m。ユーザー指定「デスク幅と同じ」) の
明るい灰色のレールを付け、白い丸いつまみを6つ並べる (間隔は写真から 0.166)。写真のとおり、東 (正面から見て左) のつまみから
  S字フック (キーホルダー付き) / 白いトートバッグ / 空の S字フック / 黒いトートバッグ / (空) / こげ茶のハンガーに掛けたワイシャツ
を吊るす。トートバッグは持ち手をつまみに直に掛ける。バッグは縫い合わせた2枚の布の形 (props.pillow_object)、シャツは角の丸い箱を曲げて作った (布のしわは小さな波)。
位置・大きさは layout.py (hanger_rail)。ローカル座標: 原点 = レールの下端の中心 / 正面 = -Y (部屋の側) / 正面から見て右 = +X (西) / 背面 = 南壁
構成: Empty `hanger_rail` の下に `hanger_rail_body` (レール)、`hanger_rail_knob_*`、`hanger_rail_hooks` (S字フック)、`hanger_rail_keys*`、
`hanger_rail_tote_white_*` `hanger_rail_tote_black_*` `hanger_rail_shirt_*`。クリック対象には未登録
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props import *
from layout import FURNITURE

KNOBS = [-0.31 + 0.166 * k for k in range(6)]   # つまみの位置 (ローカル X。東端の 0.29 には無い = 写真)
KNOB_Y, KNOB_Z = -0.022, 0.025                  # つまみの軸 (レールの前から出る) の中心
STEM_R = 0.006
def _knob_profile():
    """つまみの断面: 短い軸 (半径 6mm、長さ 2cm) の先に球 (半径 13mm)。lathe_object の Z 軸 = 壁から出る向き"""
    prof = [(0, 0, 0), (STEM_R, 0, 0), (STEM_R, 0.0195, 0)]
    for k in range(1, 13):
        th = 0.48 + (math.pi - 0.48) * k / 12
        prof.append((0.013 * math.sin(th) if k < 12 else 0, 0.031 - 0.013 * math.cos(th), 0))
    return prof


def _s_hook(sx):
    """S字フック (正面から見た面内の折れ線)。上の曲がりがつまみの軸に乗り、下の曲がりの底 (戻り値の2つ目) に物を下げる"""
    sz = KNOB_Z + STEM_R + 0.0025 - 0.011   # 上の曲がりの中心 (針金の内側が軸の上に乗る高さ)
    top = [(sx + 0.011 * math.cos(math.radians(a)), KNOB_Y, sz + 0.011 * math.sin(math.radians(a)))
           for a in (-20 + 230 * k / 12 for k in range(13))]   # 右から軸の上を越えて左下へ
    mid_x = top[-1][0] + 0.004
    cx, cz, r = mid_x + 0.0155, sz - 0.045, 0.0155
    bottom = [(cx + r * math.cos(math.radians(a)), KNOB_Y, cz + r * math.sin(math.radians(a)))
              for a in (180 + 240 * k / 13 for k in range(14))]   # 左から底を通って右上へ
    return top + bottom, (cx, KNOB_Y, cz - r)


def _tote(name, mat, knob_x, cx, w, h, drop, seed, handle_w=0.025, gather=0.12, t=0.03, fold=0.008, swing=0.0):
    """持ち手をつまみに直に掛けたトートバッグ: 2枚の布を縫い合わせた平たい袋 (props.pillow_object。縁は縫い目で薄く、
    背面は壁に当たって平ら) + 前後の持ち手。cx = 袋の中心の X、drop = つまみから袋の口までの高さ、t = 袋の真ん中の厚み。
    口は持ち手に引かれてすぼまり、持ち手の付け根の間がたるむ。前の面は縦のひだで波打つ (下ほど大きい)。
    swing = 袋の底が横へずれる量 (斜めに下がる)"""
    yc = 0.009 - 0.002 - t / 2            # 袋の中心 (背面が壁の 2mm 手前)
    z = KNOB_Z - drop                     # 袋の口
    bag = pillow_object(f"{name}_bag", w, h, t, [mat], Matrix.Translation((cx, yc, z - h / 2)) @ Matrix.Rotation(math.radians(90), 4, 'X'),
                        n=24, flat_bottom=0.7, wrinkle=0.005, seed=seed)
    ripple = folds(seed, fold, k=(14.0, 30.0), n=5)
    ax = (cx - w / 4 * (1 - gather), cx + w / 4 * (1 - gather))   # 持ち手の付け根

    def shape(p):
        px, py, pz = p
        u = max(0.0, min(1.0, (pz - (z - h)) / h))   # 0 = 底, 1 = 口
        nx = cx + (px - cx) * (1 - gather * u ** 2) + swing * (1 - u) ** 2
        q = min(1.0, min(abs(nx - ax[0]), abs(nx - ax[1])) / (w / 4))
        sag = 0.022 * q * q * smoothstep((u - 0.75) / 0.25)        # 口: 付け根で上がり、間と端が下がる
        front = max(0.0, min(1.0, (yc + t / 2 - py) / t))          # 前の面ほど大きく波打つ (背面は壁に当たったまま)
        return (nx, py - ripple(px, pz) * (0.35 + 0.65 * (1 - u)) * front, pz - sag)
    deform(bag, shape)
    top = (knob_x, KNOB_Y, KNOB_Z + STEM_R + 0.0015)   # 持ち手がつまみの軸の上に乗る点
    verts, faces = [], []
    for side in (-1, 1):   # 前後の面の持ち手。口の左右の付け根から、つまみの1点へ集まる
        for a_x in ax:
            a = (a_x, yc + side * t * 0.3, z - 0.025)
            m = (knob_x + (a_x - cx) * 0.4, yc + side * t * 0.25, (z + top[2]) / 2)
            v, f = strap_mesh(bezier(a, m, top, 10), handle_w, 0.003, face_hint=(0, 1, 0))
            faces += [tuple(len(verts) + i for i in q) for q in f]
            verts += v
    handles = mesh_object(f"{name}_handles", verts, faces, [mat])
    for p in handles.data.polygons:
        p.use_smooth = True
    return bag, handles


def _flap(quad, y0, y1, mat, bevel=0.0015):
    """正面 (-Y) から見て反時計回りの4点 [(x, z), ...] (左下・右下・右上・左上) の板を、y0〜y1 の厚みで作る (solids_object に渡す形)"""
    (ax, az), (bx, bz), (cx, cz), (dx, dz) = quad
    return ([(ax, y0, az), (bx, y0, bz), (bx, y1, bz), (ax, y1, az),
             (dx, y0, dz), (cx, y0, cz), (cx, y1, cz), (dx, y1, dz)], mat, bevel)


def _shirt(name, mat, hanger_mat, knob_x, root):
    """こげ茶のハンガーに掛けたワイシャツ。ハンガーの首 (肩の線の頂点) はつまみの 6cm 下。
    身頃 (前立て・ボタン・胸ポケット付き) は肩がハンガーに沿って下がり、裾は脇が上がった曲線。袖は脇に垂れて袖口へ細くなる"""
    x, y, z = knob_x, KNOB_Y - 0.02, KNOB_Z - 0.06
    sw, length, d = 0.215, 0.78, 0.04            # 肩幅の半分・丈・厚み
    slope = 0.09                                 # 肩の下がり
    front = y - d / 2
    button = make_material(f"{name}_button", "#F6F5F1", roughness=0.25)
    body = soft_boxes_object(f"{name}_body", [(x - sw, x + sw, y - d / 2, y + d / 2, z - length, z + 0.01, mat, 0.02, (0.003, 0.005, 0.0))],
                             cuts=24)
    trims = soft_boxes_object(f"{name}_trims", [
        (x - 0.015, x + 0.015, front - 0.003, front + 0.004, z - length + 0.004, z - 0.03, mat, 0.0015, (0, 0, 0)),   # 前立て
        (x + 0.04, x + 0.15, front - 0.0025, front + 0.004, z - 0.31, z - 0.18, mat, 0.002, (0, 0, 0)),              # 胸ポケット (着る人の左)
    ], cuts=10)
    buttons = soft_boxes_object(f"{name}_buttons", [(x - 0.005, x + 0.005, front - 0.0055, front - 0.002, bz - 0.005, bz + 0.005, button, 0.0018, (0, 0, 0))
                                                    for bz in (z - 0.09 - 0.11 * k for k in range(6))], cuts=3)
    ripple = folds(12, 0.016, k=(12.0, 28.0), tilt=0.2, n=6)   # 肩から下へ垂れるひだ (裾ほど大きい)

    def shape(p):   # 身頃・前立て・ボタンを同じように曲げる (前立てなどが身頃の表面に乗ったまま)
        px, py, pz = p
        dx = px - x
        u = min(1.0, abs(dx) / sw)
        tz = max(0.0, min(1.0, (pz - (z - length)) / length))   # 0 = 裾, 1 = 首
        pz2 = pz - slope * u ** 1.2 * smoothstep((pz - (z - 0.2)) / 0.21)          # 肩
        pz2 += 0.06 * u * u * smoothstep(((z - length + 0.12) - pz) / 0.12)       # 裾の曲線 (脇が上がる)
        taper = 1 - 0.06 * max(0.0, (z - 0.2) - pz) / (length - 0.2)           # 脇の下から裾へ少し細く
        thick = 0.55 + 0.45 * tz                                                 # 裾の方は前後が寄って薄い
        return (x + dx * taper, y + (py - y) * thick + ripple(px, pz) * (1 - tz) ** 0.5, pz2)
    for o in (body, trims, buttons):
        deform(o, shape)
    sleeves = []
    top_z = z - slope + 0.008
    for sx in (-1, 1):   # 袖: 肩の先から脇に沿って垂れる (身頃の前面に半分出る)
        c = x + sx * (sw - 0.035)
        sleeves.append((c - 0.05, c + 0.05, front - 0.016, front + 0.014, top_z - 0.6, top_z, mat, 0.022, (0.003, 0.006, 0.0)))
    sl = soft_boxes_object(f"{name}_sleeves", sleeves, cuts=14)
    sripple = folds(13, 0.01, k=(30.0, 55.0), tilt=0.6)

    def sleeve_shape(p):
        px, py, pz = p
        sx = 1 if px > x else -1
        c = x + sx * (sw - 0.035)
        t = max(0.0, min(1.0, (top_z - pz) / 0.6))   # 0 = 肩, 1 = 袖口
        return (c - sx * 0.022 * t + (px - c) * (1 - 0.3 * t), py + sripple(px, pz) * t, pz)
    deform(sl, sleeve_shape)
    # 襟: 首の後ろを回る台襟と左右の側 + 前に開いた2枚の襟先 (先は下の外へ向く)
    fy, by = front - 0.006, y + d / 2 - 0.016
    collar = [rot_box(-0.07, 0.07, 0, 0.012, -0.012, 0.028, mat, Matrix.Translation((x, by, z)), bevel=0.004)]
    for sx in (-1, 1):
        collar.append(rot_box(-0.004, 0.004, fy - by, 0, -0.012, 0.026, mat, Matrix.Translation((x + sx * 0.068, by, z)), bevel=0.003))
    tip, out, top_out, top_in = (0.042, -0.038), (0.075, -0.002), (0.064, 0.024), (0.004, 0.027)
    right = [tip, out, top_out, top_in]
    left = [(-a, b) for a, b in (out, tip, top_in, top_out)]
    collar += [_flap([(x + a, z + b) for a, b in q], fy, fy + 0.0035, mat) for q in (right, left)]
    for o in (body, trims, buttons, sl, solids_object(f"{name}_collar", collar, bevel=0.0015)):
        o.parent = root
    # ハンガー (こげ茶の樹脂。肩の線に沿った三角形の枠はシャツの中で、フックと首だけ見える)
    hz = KNOB_Z + STEM_R + 0.0035 - 0.011
    hook = [(x + 0.011 * math.cos(math.radians(a)), KNOB_Y, hz + 0.011 * math.sin(math.radians(a))) for a in range(-30, 201, 20)]
    hook += [(x - 0.008, KNOB_Y, hz - 0.02), (x, y, z + 0.01)]
    end_z = z - slope * (0.19 / sw) ** 1.2 - 0.008
    frame = [(x - 0.19, y, end_z), (x, y, z - 0.004), (x + 0.19, y, end_z)]
    tubes_object(f"{name}_hanger_hook", [hook], 0.0028, hanger_mat, parent=root, sides=8, light_from="hanger_rail_body")
    tubes_object(f"{name}_hanger", [frame, [frame[2], frame[0]]], 0.006, hanger_mat, parent=root, sides=8)


def _keychain(name, x, z, root):
    """S字フックに下げたキーホルダー (写真: 青い玉と黄色い人形)。金属の輪 + 2つの飾り"""
    metal = make_material(f"{name}_ring", "#BFC2C5", roughness=0.3, metallic=0.8)
    blue = make_material(f"{name}_blue", "#2F5FB3", roughness=0.3)
    yellow = make_material(f"{name}_yellow", "#E6BE2A", roughness=0.35)
    ring = [(x, KNOB_Y + 0.011 * math.cos(2 * math.pi * k / 16), z - 0.011 + 0.011 * math.sin(2 * math.pi * k / 16)) for k in range(17)]
    tubes_object(f"{name}_ring", [ring, [(x - 0.004, KNOB_Y, z - 0.021), (x - 0.008, KNOB_Y, z - 0.034)],
                                  [(x + 0.003, KNOB_Y, z - 0.021), (x + 0.009, KNOB_Y, z - 0.03)]],
                 0.0011, metal, parent=root, sides=6, closed=False, light_from="hanger_rail_body")
    ball = [(0, -0.012, 0)] + [(0.012 * math.sin(math.pi * k / 10), -0.012 * math.cos(math.pi * k / 10), 0) for k in range(1, 10)] + [(0, 0.012, 0)]
    lathe_object(f"{name}_blue", ball, [blue], parent=root, segments=14, location=(x - 0.009, KNOB_Y, z - 0.046))
    doll = [(0, 0, 0), (0.008, 0.002, 0), (0.009, 0.014, 0), (0.006, 0.02, 0), (0.0085, 0.026, 0), (0.007, 0.034, 0), (0, 0.036, 0)]
    lathe_object(f"{name}_yellow", doll, [yellow], parent=root, segments=12, location=(x + 0.01, KNOB_Y - 0.003, z - 0.066))


def build_hanger_rail():
    e = FURNITURE["hanger_rail"]
    hx, hy, h = e["w"] / 2, e["d"] / 2, e["h"]
    root = add_empty("hanger_rail", (e["x"], e["y"], e["z0"]), FACING_DEG[e["facing"]])
    rail = make_material("hanger_rail", "#D5CDC2", roughness=0.5)
    white = make_material("hanger_rail_knob", "#F3F2EF", roughness=0.35)
    wire = make_material("hanger_rail_wire", "#EEEEEC", roughness=0.35)
    boxes_object("hanger_rail_body", [(-hx, hx, -hy, hy, 0, h, rail, 0.003)], parent=root)
    for i, x in enumerate(KNOBS):
        lathe_object(f"hanger_rail_knob_{i}", _knob_profile(), [white], parent=root, segments=16,
                     matrix=Matrix.Translation((x, -hy, KNOB_Z)) @ Matrix.Rotation(math.radians(90), 4, 'X'))

    # 1番目: S字フックとキーホルダー / 3番目: 空の S字フック
    s1, hang = _s_hook(KNOBS[0])
    s3, _ = _s_hook(KNOBS[2])
    tubes_object("hanger_rail_hooks", [s1, s3], 0.0025, wire, parent=root, sides=6, light_from="hanger_rail_body")
    _keychain("hanger_rail_keys", hang[0], hang[2], root)
    # 2番目: 白いトートバッグ (生成りのキャンバス)。袋は少し東へずれて下がる
    for o in _tote("hanger_rail_tote_white", fabric_material("hanger_rail_tote_white", "canvas", (233, 226, 212)),
                   KNOBS[1], KNOBS[1] - 0.04, 0.27, 0.40, 0.20, seed=21, gather=0.38, t=0.035, fold=0.02, swing=-0.03):
        o.parent = root
    # 4番目: 黒いトートバッグ (持ち手が短い。写真では中に物が入ってふくらんでいる)。袋の西端はシャツの袖の手前で止める
    black = fabric_material("hanger_rail_tote_black", "canvas", (30, 30, 33), roughness=0.85)
    for o in _tote("hanger_rail_tote_black", black, KNOBS[3], KNOBS[3] - 0.03, 0.26, 0.34, 0.15, seed=22,
                   handle_w=0.02, gather=0.25, t=0.075, fold=0.01):
        o.parent = root
    # 6番目: ワイシャツ
    _shirt("hanger_rail_shirt", fabric_material("hanger_rail_shirt", "cotton", (240, 240, 238)),
           make_material("hanger_rail_hanger", "#3B2B24", roughness=0.45), KNOBS[5], root)
    return root
