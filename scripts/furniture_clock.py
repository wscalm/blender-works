"""壁掛けのアナログ時計 (ユーザー指定: カーテンレールと天井の間の真ん中)。東壁の、カーテンの中央の上。
写真 (reference/IMG_1100) に合わせて: 直径 0.36、茶色の枠の内と外の縁に銀の線、白い文字盤 (数字・分の点・温度計と湿度計。
textures/clock_face.jpg、tools/make_prints.py が描いた物)、黒い剣の形の針。

位置・大きさは layout.py (clock)。ローカル座標: 原点 = 下端の中心 / 正面 (文字盤) = -Y / 背面 (+Y) = 壁
構成: Empty `clock` の下に `clock_body` (枠・文字盤・目盛り) と、針 `clock_hour` `clock_minute` `clock_second`。
針は文字盤の中心が原点で、12時の向き (+Z) に作る。ビューアが今の時刻に合わせて、ローカルの Y 軸まわりに回す (Blender の +Y まわりの正の回転 = 正面から見て時計回り)。
クリック対象には未登録
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from layout import FURNITURE, rotation_deg

SIDES = 64
RIM_IN = 0.15        # 枠の内側の半径 = 文字盤の画像の半径 (外側は layout の w / 2)
FACE_Y = -0.005      # 文字盤の面 (枠の前面より 2cm 奥)


def _lathe(profile, mats, zc):
    """(半径, y, 材質の番号) の断面を Y 軸 (文字盤の中心) のまわりに回した面。断面は外側の奥 → 前 → 内側 → 中心 (半径 0) の順"""
    verts, faces, face_mats = [], [], []
    rings = []
    for r, y, _ in profile:
        if r == 0:
            verts.append((0.0, y, zc))
            rings.append(None)
            continue
        rings.append(len(verts))
        for i in range(SIDES):
            a = 2 * math.pi * i / SIDES
            verts.append((r * math.cos(a), y, zc + r * math.sin(a)))
    for k in range(len(profile) - 1):
        a0, b0, mi = rings[k], rings[k + 1], profile[k][2]
        for i in range(SIDES):
            j = (i + 1) % SIDES
            if b0 is None:   # 中心へ閉じる三角形
                faces.append((a0 + i, a0 + j, len(verts) - 1))
            else:            # 法線は外側・正面 (-Y)・中心の向きになる並び
                faces.append((a0 + i, a0 + j, b0 + j, b0 + i))
            face_mats.append(mi)
    return verts, faces, face_mats


def _plate(points, y):
    """文字盤と平行な板 (正面だけ。厚みなし)。points は (x, z) を反時計回り (正面から見て) に"""
    return [(x, y, z) for x, z in points]


def _hand(name, root, zc, mat, outline, y, angle):
    """針。outline = 12時の向きに作った輪郭 [(x, z), ...] (中心が原点、正面から見て反時計回り)。最初の向きは angle (焼き付けのときの時刻)"""
    obj = mesh_object(name, _plate(outline, 0.0), [tuple(range(len(outline)))], [mat], parent=root)
    obj.location = (0, y, zc)
    obj.rotation_euler = (0, angle, 0)
    return obj


def _sword(tail, tip, w_base, w_max, at=0.62):
    """剣の形の針の輪郭: 根元 (tail の側) は細く、tip の at 倍のところで一番広く、先は尖る"""
    return [(-w_base / 2, -tail), (w_base / 2, -tail), (w_max / 2, tip * at), (0.0, tip), (-w_max / 2, tip * at)]


def build_clock():
    e = FURNITURE["clock"]
    r_out, hy = e["w"] / 2, e["d"] / 2
    zc = e["h"] / 2
    root = add_empty("clock", (e["x"], e["y"], e["z0"]), rotation_deg(e))
    rim = wood_material("clock_rim", "walnut_soft", roughness=0.4, target=(142, 118, 102))   # 茶色の枠 (木目は薄く)
    silver = make_material("clock_silver", "#D4D6D8", roughness=0.3, metallic=0.6)
    inner = make_material("clock_inner", "#EDEDEA", roughness=0.6)
    face = make_material("clock_face", "#FFFFFF", roughness=0.6, texture="clock_face.jpg", texture_size=1.0)
    ink = make_material("clock_ink", "#1A1A1C", roughness=0.5)

    # 枠: 外の側面 (茶) → 前の外の縁 (銀) → 前面 (茶) → 内の縁 (銀) → 文字盤までの内側の壁 (白)
    profile = [(r_out, hy, 0), (r_out, -hy + 0.006, 1), (r_out - 0.003, -hy, 0), (RIM_IN + 0.005, -hy, 1),
               (RIM_IN, -hy + 0.003, 2), (RIM_IN, FACE_Y, 2)]
    verts, faces, face_mats = _lathe(profile, None, zc)
    mesh_object("clock_body", verts, faces, [rim, silver, inner], face_mats, parent=root)
    # 文字盤: 画像を1枚 (UV = 中心 0.5、半径 RIM_IN が画像の端)
    verts = [(0.0, FACE_Y, zc)] + [(RIM_IN * math.cos(2 * math.pi * i / SIDES), FACE_Y, zc + RIM_IN * math.sin(2 * math.pi * i / SIDES))
                                   for i in range(SIDES)]
    disk = mesh_object("clock_face", verts, [(0, 1 + i, 1 + (i + 1) % SIDES) for i in range(SIDES)], [face], parent=root)
    uv = disk.data.uv_layers.new(name="UVMap")
    for loop in disk.data.loops:
        x, _, z = verts[loop.vertex_index]
        uv.data[loop.index].uv = (0.5 + x / (2 * RIM_IN), 0.5 + (z - zc) / (2 * RIM_IN))
    cap = [(0.008 * math.cos(2 * math.pi * i / 16), zc + 0.008 * math.sin(2 * math.pi * i / 16)) for i in range(16)]
    mesh_object("clock_cap", _plate(cap, FACE_Y - 0.009), [tuple(range(16))], [ink], parent=root)   # 中心のキャップ

    # 針 (焼き付けのときは 10時8分37秒 の形。ビューアで今の時刻に回る)。3本とも黒
    _hand("clock_hour", root, zc, ink, _sword(0.018, 0.085, 0.006, 0.013), FACE_Y - 0.003, 2 * math.pi * (10 + 8 / 60) / 12)
    _hand("clock_minute", root, zc, ink, _sword(0.022, 0.125, 0.005, 0.009), FACE_Y - 0.005, 2 * math.pi * 8 / 60)
    _hand("clock_second", root, zc, ink, [(-0.0012, -0.035), (0.0012, -0.035), (0.0008, 0.135), (-0.0008, 0.135)],
          FACE_Y - 0.007, 2 * math.pi * 37 / 60)
    return root
