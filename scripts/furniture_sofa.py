"""2人掛けソファー (青みがかったグレーの布張り、丸い木の脚)。

位置・大きさは layout.py。ローカル座標: 原点 = 足元の中心 / 正面 (座って向く側) = -Y / 背面 = +Y / 幅は X
構成: Empty `sofa` の下に、本体 `sofa_body` (土台・肘掛け・背板) と `sofa_cushions` (座面 2 + 背 2) と `sofa_legs`、
`sofa_pillow_stripe` `sofa_pillow_gray` (背もたれに立て掛けたクッション。props.pillow_object。写真 reference/IMG_1100: 後ろから見て左 = 北の席に細いボーダー、右 = 南の席にグレー)
布張りの部分は角を少しだけ丸めた箱 (soft_boxes_object。「もう少し角ばっていた」(ユーザー指定) ので丸みは 1.2〜2.5cm) にして、ヘリンボーンの布のテクスチャを貼る
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from layout import BED_TOP, FURNITURE, SOFA_SEAT
from props import Matrix, pillow_object

BODY = "#717D8D"       # 本体の布 (青みがかったグレー)
CUSHION = "#8692A2"    # クッション・肘掛けの天板 (本体より少し明るい)
LEG = "#BF9A6B"        # 脚の木。床の木 (#96744F〜#A78862) をもう少し明るくした色

LEG_Z = 0.15           # 脚の高さ = 本体の底の高さ
SEAT_Z = 0.27          # 座面クッションの下面
SEAT_TOP = SOFA_SEAT   # 座面の高さ (サイドテーブルの高さと揃える)
SIDES = 16             # 脚の断面の角数 (なめらかに表示する)
FABRIC = dict(texture="sofa_fabric_1k.jpg", texture_size=0.27)   # tools/make_textures.py (平均の色 = CUSHION)
FABRIC_MEAN = (133, 145, 160)


def _leg(cx, cy, splay_x, splay_y, r_top=0.032, r_bottom=0.022):
    """脚1本。上 (本体の底) の中心が (cx, cy)、床では splay 分だけ外へ開いた先細りの八角柱。(verts, faces)"""
    verts = []
    for z, r, dx, dy in ((0.0, r_bottom, splay_x, splay_y), (LEG_Z, r_top, 0.0, 0.0)):
        for i in range(SIDES):
            a = 2 * math.pi * (i + 0.5) / SIDES
            verts.append((cx + dx + r * math.cos(a), cy + dy + r * math.sin(a), z))
    faces = [(i, (i + 1) % SIDES, SIDES + (i + 1) % SIDES, SIDES + i) for i in range(SIDES)]
    return verts, faces   # 上下の面は本体と床で隠れるので作らない


def _pillow(name, mat, x, yaw, roll, seed, root, stripes=False):
    """背もたれに立て掛けたクッション (42 x 42cm。縁が薄く真ん中が厚い、角のとがった形。props.pillow_object)。x = 置く席の中心 (ローカル X)。
    下の縁は座面に少し沈み、上の方が背クッションに寄りかかる (後ろへ 14°)。背クッションに当たる裏側は少しつぶれる。
    縞はクッションの横向き (布の画像 0.5m に縞 10 本)"""
    m = (Matrix.Translation((x, 0.085, SEAT_TOP + 0.20)) @ Matrix.Rotation(math.radians(yaw), 4, 'Z')
         @ Matrix.Rotation(math.radians(-14), 4, 'X') @ Matrix.Rotation(math.radians(roll), 4, 'Y')
         @ Matrix.Rotation(math.radians(90), 4, 'X'))   # クッションの面 (上から見た形) を立てる: 表 = -Y、縦 = Z
    return pillow_object(name, 0.42, 0.42, 0.13, [mat], m, parent=root, flat_bottom=0.35, wrinkle=0.004, seed=seed,
                         uv_scale=2.0 if stripes else 1.0)


def build_sofa():
    e = FURNITURE["sofa"]
    hx, hy = e["w"] / 2, e["d"] / 2
    root = add_empty("sofa", (e["x"], e["y"], e["z0"]), FACING_DEG[e["facing"]])

    body = make_material("sofa_body", tint(FABRIC_MEAN, BODY), roughness=1.0, specular=0.3, **FABRIC)
    cushion = make_material("sofa_cushion", "#FFFFFF", roughness=1.0, specular=0.3, **FABRIC)
    leg = wood_material("sofa_leg", "honey_soft", roughness=0.5, target=LEG)

    arm = 0.12                  # 肘掛けの厚み
    back_t = 0.10               # 背板の厚み
    iw = hx - arm               # 肘掛けの内側 (座面の半幅)
    arm_top = BED_TOP           # 肘掛けの上面 = ベッドの上面 = スツールの高さ。飾りなしの平らな箱 (上面はふくらませない)
    soft_boxes_object("sofa_body", [
        (-hx, hx, -hy, hy, LEG_Z, SEAT_Z, body, 0.012, (0.0, 0.0, 0.0)),                     # 土台
        (-hx, -iw, -hy, hy, LEG_Z, arm_top, body, 0.015, (0.002, 0.002, 0.0)),               # 肘掛け 左右
        (iw, hx, -hy, hy, LEG_Z, arm_top, body, 0.015, (0.002, 0.002, 0.0)),
        (-iw, iw, hy - back_t, hy, LEG_Z, 0.64, body, 0.015, (0.0, 0.003, 0.0)),             # 背板
    ], parent=root, cuts=10)

    gap = 0.005                 # 左右のクッションの継ぎ目
    seat_back = hy - back_t     # 座面クッションの奥の端
    puff = 0.006                # 座面の中央のふくらみ (頂上が SEAT_TOP になる)
    items = []
    for x0, x1 in ((-iw, -gap), (gap, iw)):
        # 座面: 手前へ 2cm はみ出す
        items.append((x0, x1, -hy - 0.02, seat_back, SEAT_Z, SEAT_TOP - puff, cushion, 0.02, (0.002, 0.003, puff)))
        # 背: 厚み 0.17 のまま、上へ行くほど後ろへ傾く (背板に寄りかかる)。下端は座面に少し沈める
        t, lean, top = 0.17, 0.075, e["h"]
        items.append((x0, x1, seat_back - t, seat_back, SEAT_TOP - 0.03, top, cushion, 0.025, (0.002, 0.008, 0.0), lean))
    soft_boxes_object("sofa_cushions", items, parent=root, cuts=12)

    # 丸い脚 4 本。四隅から少し内側に付け、床へ向かって外へ少し開く
    verts, faces = [], []
    for sx in (-1, 1):
        for sy in (-1, 1):
            v, f = _leg(sx * (hx - 0.11), sy * (hy - 0.10), sx * 0.03, sy * 0.03)
            faces += [tuple(len(verts) + i for i in poly) for poly in f]
            verts += v
    legs = mesh_object("sofa_legs", verts, faces, [leg], parent=root)
    for poly in legs.data.polygons:
        poly.use_smooth = True

    # クッション: 北の席 (ローカル +X) に白地にグレーの細いボーダー、南の席にライトグレー
    stripe = make_material("sofa_pillow_stripe", "#FFFFFF", roughness=1.0, specular=0.3, texture="stripe_fabric.jpg", texture_size=1.0)
    gray = fabric_material("sofa_pillow_gray", "cotton", (158, 161, 164))
    _pillow("sofa_pillow_stripe", stripe, iw / 2 + 0.01, -6, 4, 31, root, stripes=True)
    _pillow("sofa_pillow_gray", gray, -iw / 2 - 0.02, 8, -3, 32, root)
    return root
