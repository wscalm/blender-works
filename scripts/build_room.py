"""居室の外殻 (床・壁・天井・窓・ドア・収納扉・エアコン (専用のコンセントと壁のリモコン)・シーリングライト・インターホン) を作る。寸法は room_spec.py。

色と仕上げは物件情報の写真 (https://unilife.co.jp/view/10170、同じ建物の別の部屋) に合わせた:
ツヤのあるはちみつ色のフローリング / 白いエンボスのビニールクロス / はちみつ色の木目のドア (縦長のすりガラス2本・真鍮色のレバー) と
収納の折れ戸 (少し濃い木目・真鍮色のつまみ) / 濃い木目の巾木 / 濃いグレーのアルミサッシ / ドアの横のベージュのインターホン。
床・壁・天井は箱どうしが継ぎ目なく続くので面取りしない (bevel=0)。
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from room_spec import *

BB_H = 0.06      # 巾木の高さ
BB_T = 0.012     # 巾木の出
CASING_W = 0.05  # ドア・収納・窓のまわりの額縁 (枠の室内側の見付)
CASING_T = 0.015 # 額縁の出 (巾木より少し出る)


def make_materials():
    return dict(
        wall=make_material("wall", "#FFFFFF", roughness=0.9, specular=0.3, texture="wall_vinyl_1k.jpg", texture_size=1.0),
        ceiling=make_material("ceiling", "#F6F4F0", roughness=0.95, specular=0.3, texture="wall_vinyl_1k.jpg", texture_size=1.0),
        baseboard=wood_material("baseboard", "honey_soft", roughness=0.4, target=(126, 86, 45)),
        # フローリング: 板の幅は約 11cm (画像の板 約 19cm を縮める)。ニスのツヤで天井の明かりと窓が映る
        floor=make_material("floor", "#FFFFFF", roughness=0.22, texture="floor_honey_2k.jpg", texture_size=1.15),
        frame=make_material("window_sash", "#4A3F37", roughness=0.35),      # 濃いブロンズ (こげ茶) のアルミサッシ (写真 reference/IMG_1100)
        glass=make_material("glass", "#BFE0F2", roughness=0.05, alpha=0.28),
        glass_frosted=make_material("window_glass_frosted", "#E4E8EA", roughness=0.3, alpha=0.75),   # 掃き出し窓の下半分の型板ガラス (写真)
        dark=make_material("dark_gray", "#5A6066", roughness=0.4),
        # ドア・収納・枠は木目を薄くした画像 (ユーザー指定: 木目がはっきり見えるのはテーブルと床だけ)
        door=wood_material("door_wood", "honey_soft", roughness=0.45),
        trim=wood_material("door_trim", "honey_soft", roughness=0.45, target=(190, 146, 94)),   # ドア・収納・窓の枠と額縁
        closet=wood_material("closet_door", "honey_soft", roughness=0.45, target=(176, 138, 88)),
        frosted=make_material("door_glass_frosted", "#BFC4C2", roughness=0.2),  # ドアのすりガラス (向こうは暗い廊下)
        brass=make_material("brass", "#C9A55E", roughness=0.3, metallic=0.8),   # レバー・つまみ
        shelf=wood_material("bay_shelf", "honey_soft", roughness=0.4),
        intercom=make_material("intercom", "#D9CCA6", roughness=0.5),
        aircon=make_material("aircon_white", "#F4F4F2", roughness=0.5),
        aircon_vent=make_material("aircon_vent", "#7B838A", roughness=0.5),
        led=make_material("aircon_led", "#58D68D", emission=3.0),
        aircon_window=make_material("aircon_window", "#3A3F44", roughness=0.2),   # 表示部の小さな窓 (色の濃い樹脂)
        aircon_logo=make_material("aircon_logo", "#8E9296", roughness=0.4),
        aircon_badge=make_material("aircon_badge", "#B9BDC2", roughness=0.3, metallic=0.6),
        outlet=make_material("outlet", "#E8E3D6", roughness=0.45),   # コンセントの板 (アイボリー)
        # シーリングライトの乳白カバー。夜の照明はこれ1つ (焼き付けではこの面が光源になる)。色は room_spec.CEILING_LIGHT (白色)
        diffuser=make_material("ceiling_light_diffuser", "#FFFFFF", emission=CEILING_LIGHT["strength"],
                               emission_color=CEILING_LIGHT["color"]),
    )


def build_floor(m):
    """フローリング: 1枚の板にテクスチャを貼る。板は部屋の長い方 (東西) に沿う (add_box_uvs が V を長い方にする)"""
    return boxes_object("room_floor", [(0, ROOM_W, 0, ROOM_D, -0.03, 0, m["floor"])], bevel=0)


def build_ceiling(m):
    t = WALL_T
    return boxes_object("room_ceiling", [(-t, ROOM_W + t, -t, ROOM_D + t, ROOM_H, ROOM_H + 0.1, m["ceiling"])], bevel=0)


def _baseboard(x0, x1, y0, y1, m):
    """巾木 (壁の中の箱で、これだけ角を面取りする)"""
    return (x0, x1, y0, y1, 0, BB_H, m["baseboard"], 0.002)


def _casing_west(y0, y1, z1, m):
    """西壁の開口 (Y y0〜y1, 高さ 0〜z1) のまわりの額縁。枠の見付を覆い、壁へ少しかかる"""
    a, b = y0 - (CASING_W - 0.04), y1 + (CASING_W - 0.04)
    return [
        (0, CASING_T, a, a + CASING_W, 0, z1 + 0.01, m["trim"]),
        (0, CASING_T, b - CASING_W, b, 0, z1 + 0.01, m["trim"]),
        (0, CASING_T, a, b, z1 - 0.04, z1 + 0.01, m["trim"]),
    ]


SHELF_T = 0.04   # 出窓の天板の厚み


def build_wall_north(m):
    """北壁。出窓の開口 (x0〜x1, 天板の下面〜head_z) を抜く。腰壁と巾木は開口の下にも残る。"""
    t, b = WALL_T, NORTH_BAY
    y0, y1 = ROOM_D, ROOM_D + t
    return boxes_object("room_wall_north", [
        (-t, b["x0"], y0, y1, 0, ROOM_H, m["wall"]),                          # 開口の西
        (b["x1"], ROOM_W + t, y0, y1, 0, ROOM_H, m["wall"]),                  # 開口の東
        (b["x0"], b["x1"], y0, y1, 0, b["sill_z"] - SHELF_T, m["wall"]),      # 窓の下 (腰壁)
        (b["x0"], b["x1"], y0, y1, b["head_z"], ROOM_H, m["wall"]),           # 窓の上
        _baseboard(0, ROOM_W, ROOM_D - BB_T, ROOM_D, m),
    ], bevel=0)


def build_wall_south(m):
    t = WALL_T
    return boxes_object("room_wall_south", [
        (-t, ROOM_W + t, -t, 0, 0, ROOM_H, m["wall"]),
        _baseboard(0, ROOM_W, 0, BB_T, m),
    ], bevel=0)


def build_wall_east(m):
    w, x0, x1 = EAST_WINDOW, ROOM_W, ROOM_W + WALL_T
    boxes = []
    for ya, yb in ((0, w["y0"]), (w["y1"], ROOM_D)):
        boxes.append((x0, x1, ya, yb, 0, ROOM_H, m["wall"]))
        boxes.append(_baseboard(x0 - BB_T, x0, ya, yb, m))
    boxes.append((x0, x1, w["y0"], w["y1"], w["z1"], ROOM_H, m["wall"]))   # 窓の上
    return boxes_object("room_wall_east", boxes, bevel=0)


def build_wall_west(m):
    d, c, x0, x1 = WEST_DOOR, WEST_CLOSET, -WALL_T, 0
    boxes = []
    # 壁が全高で残る区間: 南端〜ドア / ドア〜収納 / 収納〜北端
    for ya, yb in ((0, d["y0"]), (d["y1"], c["y0"]), (c["y1"], ROOM_D)):
        boxes.append((x0, x1, ya, yb, 0, ROOM_H, m["wall"]))
        boxes.append(_baseboard(0, BB_T, ya, yb, m))
    boxes.append((x0, x1, d["y0"], d["y1"], d["z1"], ROOM_H, m["wall"]))   # ドアの上
    boxes.append((x0, x1, c["y0"], c["y1"], c["z1"], ROOM_H, m["wall"]))   # 収納の上
    return boxes_object("room_wall_west", boxes, bevel=0)


def build_window_east(m):
    """掃き出し窓: 枠 + 引き違いの2枚 (ガラス + 框 + 横桟) + クレセント錠 + 室内側の木の額縁 (左右と上)。
    写真 (reference/IMG_1100): 横桟は高さの半分くらい (0.93m)。その下は型板ガラス (すりガラス)、上は透明"""
    w = EAST_WINDOW
    y0, y1, z0, z1 = w["y0"], w["y1"], w["z0"], w["z1"]
    xa, xb = ROOM_W, ROOM_W + WALL_T
    f = 0.04      # 枠の見付
    s = 0.035     # 框の見付
    boxes = [
        (xa, xb, y0, y1, z0, z0 + f, m["frame"]),               # 下枠 (敷居)
        (xa, xb, y0, y1, z1 - f, z1, m["frame"]),               # 上枠
        (xa, xb, y0, y0 + f, z0 + f, z1 - f, m["frame"]),       # 南の縦枠
        (xa, xb, y1 - f, y1, z0 + f, z1 - f, m["frame"]),       # 北の縦枠
    ]
    iy0, iy1, iz0, iz1 = y0 + f, y1 - f, z0 + f, z1 - f
    mid, lap = (iy0 + iy1) / 2, 0.03   # 2枚は中央で重なる
    # (南の障子は外側のレール、北の障子は室内側のレール)
    zr = z0 + 0.52 * (z1 - z0)         # 横桟 (写真の窓は高さの半分くらい)
    for ya, yb, xs0, xs1 in ((iy0, mid + lap, xa + 0.07, xa + 0.10),
                             (mid - lap, iy1, xa + 0.02, xa + 0.05)):
        gx = (xs0 + xs1) / 2
        boxes += [
            (xs0, xs1, ya, ya + s, iz0, iz1, m["frame"]),               # 縦框
            (xs0, xs1, yb - s, yb, iz0, iz1, m["frame"]),
            (xs0, xs1, ya, yb, iz0, iz0 + 0.05, m["frame"]),            # 下框
            (xs0, xs1, ya, yb, iz1 - s, iz1, m["frame"]),               # 上框
            (xs0 + 0.005, xs1 - 0.005, ya + s, yb - s, zr - 0.015, zr + 0.015, m["frame"]),   # 横桟
            (gx - 0.003, gx + 0.003, ya + s, yb - s, iz0 + 0.05, zr - 0.015, m["glass_frosted"]),   # ガラス (下 = 型板・上 = 透明)
            (gx - 0.003, gx + 0.003, ya + s, yb - s, zr + 0.015, iz1 - s, m["glass"]),
        ]
    boxes.append((xa + 0.005, xa + 0.02, mid - 0.02, mid + 0.04, 0.98, 1.08, m["dark"]))  # クレセント錠
    c0, c1 = xa - CASING_T, xa                                          # 額縁 (室内側へ CASING_T 出る)
    boxes += [
        (c0, c1, y0 - 0.01, y0 - 0.01 + CASING_W, 0, z1 + 0.01, m["trim"]),
        (c0, c1, y1 + 0.01 - CASING_W, y1 + 0.01, 0, z1 + 0.01, m["trim"]),
        (c0, c1, y0 - 0.01, y1 + 0.01, z1 - 0.04, z1 + 0.01, m["trim"]),
    ]
    return boxes_object("room_window_east", boxes)


def build_door_west(m):
    """キッチン側のドア (閉じた状態)。蝶番は北、レバーハンドルは南側。

    写真のドア: はちみつ色の木目の扉に、縦長のすりガラスが2本 (下 0.3m〜上 1.8m)。真鍮色のレバーハンドル。
    すりガラスは不透明の明るいグレーの板として扉の表面に貼り、細い木の押縁で囲む。
    """
    d = WEST_DOOR
    y0, y1, z1 = d["y0"], d["y1"], d["z1"]
    x0, x1 = -WALL_T, 0
    f = 0.04
    ly0, ly1 = y0 + f, y1 - f                                     # 扉の幅
    face = -0.01                                                  # 扉の室内側の面
    boxes = [
        (x0, x1, y0, y0 + f, 0, z1, m["trim"]),                   # 縦枠
        (x0, x1, y1 - f, y1, 0, z1, m["trim"]),
        (x0, x1, y0 + f, y1 - f, z1 - f, z1, m["trim"]),          # 上枠
        (-0.05, face, ly0, ly1, 0, z1 - f, m["door"]),            # 扉
        *_casing_west(y0, y1, z1, m),
    ]
    sw, gz0, gz1, bead = 0.10, 0.30, 1.80, 0.012                  # すりガラスの幅・高さ / 押縁の見付
    for t in (0.36, 0.64):                                        # 扉の幅の 36% と 64% の位置
        c = ly0 + (ly1 - ly0) * t
        g0, g1 = c - sw / 2, c + sw / 2
        boxes += [
            (face, face + 0.002, g0, g1, gz0, gz1, m["frosted"]),
            (face, face + 0.006, g0 - bead, g0, gz0 - bead, gz1 + bead, m["door"]),   # 押縁 (左右・上下)
            (face, face + 0.006, g1, g1 + bead, gz0 - bead, gz1 + bead, m["door"]),
            (face, face + 0.006, g0, g1, gz0 - bead, gz0, m["door"]),
            (face, face + 0.006, g0, g1, gz1, gz1 + bead, m["door"]),
        ]
    hy = ly0 + 0.06                                               # レバーの軸 (戸先から 6cm)
    boxes += [
        (face, face + 0.008, hy - 0.022, hy + 0.022, 0.968, 1.012, m["brass"]),         # 座
        (face + 0.008, face + 0.045, hy - 0.009, hy + 0.009, 0.981, 0.999, m["brass"]),  # 軸
        (face + 0.035, face + 0.052, hy - 0.01, hy + 0.12, 0.979, 1.001, m["brass"]),    # レバー (蝶番の側へ)
        (face, face + 0.004, hy - 0.012, hy + 0.012, 0.86, 0.90, m["brass"]),           # 鍵の座
    ]
    return boxes_object("room_door_west", boxes)


def build_closet_door(m):
    """収納の折れ戸 (閉じた状態、4枚 = 2枚ずつ折れる組が2つ)。写真の収納: ドアより少し濃い木目、真鍮色の小さな丸いつまみ。"""
    c = WEST_CLOSET
    y0, y1, z1 = c["y0"], c["y1"], c["z1"]
    x0, x1 = -WALL_T, 0
    f = 0.04
    boxes = [
        (x0, x1, y0, y0 + f, 0, z1, m["trim"]),
        (x0, x1, y1 - f, y1, 0, z1, m["trim"]),
        (x0, x1, y0 + f, y1 - f, z1 - f, z1, m["trim"]),
        *_casing_west(y0, y1, z1, m),
    ]
    inner0, inner1 = y0 + f, y1 - f
    pw = (inner1 - inner0) / 4
    for i in range(4):
        boxes.append((-0.04, -0.008, inner0 + i * pw + 0.003, inner0 + (i + 1) * pw - 0.003,
                      0.01, z1 - f - 0.003, m["closet"]))
    mid = (inner0 + inner1) / 2
    for yc in (mid - 0.045, mid + 0.045):                             # つまみ (中央の2枚の、合わせ目の近く)
        boxes.append((-0.008, 0.014, yc - 0.011, yc + 0.011, 0.989, 1.011, m["brass"], 0.007))
    return boxes_object("room_closet_door", boxes)


def build_aircon(m):
    """エアコン (写真 reference/IMG_1100: 白い本体の前面は、大きな前面パネルと、その下の閉じた風向きの板。
    右端 (南) は表示部の縦の帯 (小さな窓に緑のランプ)、前面パネルの左下 (北) に社名の代わりの灰色の帯、右上に小さな銀の印)。
    Empty `aircon` の下に、角の丸い本体と前面の部品 `aircon_body` と、細部 `aircon_parts`"""
    a = AIRCON
    y0, y1 = a["y_center"] - a["width"] / 2, a["y_center"] + a["width"] / 2
    z0, z1 = a["z0"], a["z0"] + a["height"]
    xf = ROOM_W - a["depth"]   # 前面
    yd = y0 + 0.075            # 表示部の帯 (南の端) と前面パネルの境
    zl = z0 + 0.10             # 前面パネルの下端 (この下に風向きの板)
    root = add_empty("aircon")
    w = m["aircon"]
    soft_boxes_object("aircon_body", [
        (xf + 0.012, ROOM_W + 0.03, y0, y1, z0, z1, w, 0.03, (0.0, 0.0, 0.004)),                          # 本体 (背面は壁の中へ)
        (xf, xf + 0.03, yd + 0.003, y1 - 0.012, zl + 0.004, z1 - 0.014, w, 0.01, (0.004, 0.0, 0.0)),        # 前面パネル
        (xf + 0.004, xf + 0.03, y0 + 0.012, yd - 0.003, z0 + 0.03, z1 - 0.014, w, 0.01, (0.0, 0.0, 0.0)),   # 表示部の帯
        (xf + 0.006, xf + 0.03, yd + 0.003, y1 - 0.02, z0 + 0.026, zl - 0.003, w, 0.012, (0.005, 0.0, 0.0)),  # 風向きの板 (閉じている)
    ], parent=root, cuts=8)
    boxes_object("aircon_parts", [
        (xf + 0.004, xf + 0.014, yd + 0.004, y1 - 0.024, zl - 0.006, zl + 0.006, m["aircon_vent"]),         # 前面パネルと風向きの板のすき間
        (xf + 0.035, xf + 0.075, yd + 0.01, y1 - 0.03, z0 - 0.001, z0 + 0.003, m["aircon_vent"]),           # 下の吹き出し口
        (xf + 0.003, xf + 0.005, y0 + 0.026, y0 + 0.062, zl + 0.004, zl + 0.03, m["aircon_window"], 0.001),  # 表示部の小さな窓
        (xf + 0.0022, xf + 0.003, y0 + 0.05, y0 + 0.056, zl + 0.012, zl + 0.018, m["led"], 0.0002),         # 表示ランプ
        (xf - 0.0012, xf + 0.001, y1 - 0.095, y1 - 0.045, zl + 0.012, zl + 0.019, m["aircon_logo"], 0.0003),  # 社名の代わりの帯
        (xf - 0.0016, xf + 0.001, y0 + 0.10, y0 + 0.125, zl + 0.085, zl + 0.093, m["aircon_badge"], 0.0003),  # 小さな銀の印
    ], parent=root)
    return root


def build_aircon_outlet(m):
    """エアコン専用のコンセント (写真: 本体の北の端の真下。アイボリーの板の下の口にプラグが刺さり、白い線が本体の下へ上がる)"""
    from props import bezier, tubes_object
    yc, zc, x = 3.335, 1.87, ROOM_W
    p = m["outlet"]
    plate = boxes_object("room_outlet_aircon", [
        (x - 0.008, x, yc - 0.035, yc + 0.035, zc - 0.06, zc + 0.06, p),                      # 板
        (x - 0.011, x - 0.007, yc - 0.022, yc + 0.022, zc - 0.045, zc + 0.045, p, 0.002),      # 差し込み口の枠
        (x - 0.0115, x - 0.0105, yc - 0.0075, yc - 0.0055, zc + 0.012, zc + 0.026, m["dark"], 0.0003),   # 上の口の穴
        (x - 0.0115, x - 0.0105, yc + 0.0055, yc + 0.0075, zc + 0.012, zc + 0.026, m["dark"], 0.0003),
        (x - 0.034, x - 0.011, yc - 0.016, yc + 0.016, zc - 0.04, zc - 0.006, m["aircon"], 0.004),     # 下の口に刺したプラグ
    ])
    a = AIRCON
    cord = bezier((x - 0.03, yc, zc - 0.02), (x - 0.07, yc + 0.004, zc - 0.03), (x - 0.06, yc + 0.012, zc + 0.04), n=10)
    cord.append((x - 0.06, yc + 0.014, a["z0"] + 0.01))
    tubes_object("room_outlet_aircon_cord", [cord], 0.0035, m["aircon"], light_from="room_outlet_aircon")
    return plate


def build_aircon_remote(m):
    """エアコンのリモコン (写真: テレビの上の東の壁。白い壁掛けのホルダーに入れてある)"""
    yc, z0, x = 2.90, 1.43, ROOM_W
    return boxes_object("room_aircon_remote", [
        (x - 0.022, x, yc - 0.03, yc + 0.03, z0, z0 + 0.075, m["aircon"], 0.003),                 # ホルダー (下の方だけ)
        (x - 0.017, x - 0.004, yc - 0.026, yc + 0.026, z0 + 0.01, z0 + 0.15, m["aircon"], 0.004),  # リモコン
        (x - 0.0175, x - 0.017, yc - 0.018, yc + 0.018, z0 + 0.105, z0 + 0.135, m["aircon_window"], 0.0003),   # 表示
    ])


def build_bay_window(m):
    """出窓 (腰高窓): 天板 + 枠 + ガラスがコの字 (前面と左右の側面)。北壁の外へ突き出す。

    壁の外面 (Y=ROOM_D+WALL_T) から前面 (Y=ROOM_D+depth) までが出っ張り。
    天板は室内側へ 2cm 出る。屋根は上から見るときに隠せるよう別オブジェクト (room_bay_roof)。
    """
    b = NORTH_BAY
    x0, x1, sill, head = b["x0"], b["x1"], b["sill_z"], b["head_z"]
    ya, yf = ROOM_D + WALL_T, ROOM_D + b["depth"]   # 壁の外面 / 前面
    f, s = 0.04, 0.05                               # 前面の枠の見付 / 側面の枠の見付
    xl, xr = x0 - s, x1 + s                         # 側面の枠の外側
    gz0, gz1 = sill + 0.05, head - 0.05             # ガラスの高さ
    mid, yg = (x0 + x1) / 2, yf - f / 2             # 前面の中桟の位置 / 前面ガラスの面

    boxes = [(xl, xr, ROOM_D - 0.02, yf, sill - SHELF_T, sill, m["shelf"])]      # 天板 (木目)
    boxes += [  # 前面: 上下の桟 + 中桟 + ガラス2枚
        (x0, x1, yf - f, yf, sill, gz0, m["frame"]),
        (x0, x1, yf - f, yf, gz1, head, m["frame"]),
        (mid - 0.02, mid + 0.02, yf - f, yf, gz0, gz1, m["frame"]),
        (x0, mid - 0.02, yg - 0.003, yg + 0.003, gz0, gz1, m["glass"]),
        (mid + 0.02, x1, yg - 0.003, yg + 0.003, gz0, gz1, m["glass"]),
    ]
    for xa, xb in ((xl, x0), (x1, xr)):             # 左右の側面: 枠 + ガラス
        gx = (xa + xb) / 2
        boxes += [
            (xa, xb, ya, ya + f, sill, head, m["frame"]),                  # 奥の縦枠
            (xa, xb, yf - f, yf, sill, head, m["frame"]),                  # 手前の縦枠
            (xa, xb, ya + f, yf - f, sill, gz0, m["frame"]),               # 下枠
            (xa, xb, ya + f, yf - f, gz1, head, m["frame"]),               # 上枠
            (gx - 0.003, gx + 0.003, ya + f, yf - f, gz0, gz1, m["glass"]),
        ]
    window = boxes_object("room_bay_window", boxes)
    roof = boxes_object("room_bay_roof", [(xl, xr, ya, yf, head, head + 0.04, m["ceiling"])])
    return window, roof


def build_ceiling_light(m):
    """天井の中央の丸いシーリングライト: 乳白のカバー。天井から短い円筒の側面が下り、そこから浅いドーム (楕円の断面) で中央へ閉じる。
    光る面の広さは、前の平たい円盤 (側面 + 下面) とほぼ同じにしてある (明るさを変えないため)"""
    c = CEILING_LIGHT
    sides, rings = 48, 10
    r, side_h = c["radius"], 0.03
    dome_h = c["thickness"] + 0.02 - side_h      # 天井から一番下まで = 前と同じ 0.09
    profile = [(r, ROOM_H), (r, ROOM_H - side_h)]
    for k in range(1, rings + 1):                # ドーム: 角度 0〜90° の楕円
        t = math.pi / 2 * k / rings
        profile.append((r * math.cos(t), ROOM_H - side_h - dome_h * math.sin(t)))
    verts, faces = [], []
    for pr, z in profile[:-1]:
        for i in range(sides):
            a = 2 * math.pi * i / sides
            verts.append((c["x"] + pr * math.cos(a), c["y"] + pr * math.sin(a), z))
    verts.append((c["x"], c["y"], profile[-1][1]))   # 一番下の中心
    n = len(profile) - 1
    for ring in range(n - 1):
        for i in range(sides):
            a, b = ring * sides + i, ring * sides + (i + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    tip = len(verts) - 1
    for i in range(sides):
        a, b = (n - 1) * sides + i, (n - 1) * sides + (i + 1) % sides
        faces.append((a, b, tip))
    obj = mesh_object("room_ceiling_light", verts, faces, [m["diffuser"]])
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def build_intercom(m):
    """ドアの南隣の壁のインターホン (写真: ベージュの縦長の本体に受話器)。高さは床から 1.30〜1.52m。部屋は写真と左右が逆なので南側"""
    yc, z0, z1 = 0.42, 1.30, 1.52
    return boxes_object("room_intercom", [
        (0, 0.03, yc - 0.045, yc + 0.045, z0, z1, m["intercom"]),                 # 本体
        (0.03, 0.05, yc - 0.042, yc + 0.012, z0 + 0.01, z1 - 0.01, m["intercom"]),  # 受話器
        (0.03, 0.033, yc + 0.02, yc + 0.035, z1 - 0.05, z1 - 0.03, m["dark"]),    # ボタン
    ])


def build_shell():
    """外殻をまとめて作り、{名前: オブジェクト} を返す。"""
    m = make_materials()
    objs = [
        build_floor(m), build_ceiling(m),
        build_wall_north(m), build_wall_south(m), build_wall_east(m), build_wall_west(m),
        build_window_east(m), build_door_west(m), build_closet_door(m), build_aircon(m), build_aircon_outlet(m), build_aircon_remote(m),
        *build_bay_window(m), build_ceiling_light(m), build_intercom(m),
    ]
    return {o.name: o for o in objs}
