"""デスク2の上のモニター2台と、サブモニターの台の白い箱。

メインモニター 24型 (西寄り = PC の側): 机に直に置く。高さを変えられるスタンド (太い柱) を伸ばして、画面を目線の高さ近くにする。
サブモニター 20型 (もとはテレビ。東隣): 高さが合わないので、白い箱を2つ並べた上に乗せて画面の上端をメインに揃える。
座るのはメインの前なので、サブは箱ごと座る人の方へ斜めに向ける (layout.py の yaw)。
メインの画面は点いていて、白い画面 (表計算・グラフの画面。textures/screen_main.png、tools/make_prints.py が描いた物) を映す (写真 reference/IMG_1099)。
画面の画像は自分で光る (emission。ライトマップを使わない。焼き付けでは机やキーボードを照らす弱い光源になる)。サブは消えている (写真)。
位置・大きさは layout.py (monitor_main, monitor_boxes, monitor_sub)。
ローカル座標: 原点 = 足元の中心 / 正面 (画面) = -Y / X = 正面から見て右
構成: Empty `monitor_main` の下に `monitor_main_body` (枠・背面・柱・台座) と `monitor_main_screen` (sub も同じ)。メインだけ `monitor_main_image` (光る画面)。
Empty `monitor_boxes` の下に `monitor_boxes_body`。箱はクリック対象に未登録
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props import *
from layout import FURNITURE, rotation_deg

BASE_T = 0.015        # 台座の厚み
BLACK = "#18181A"     # モニターの枠 (テレビと同じ黒)
SCREEN = "#0B0C0F"    # 消えている画面
SCREEN_GLOW = 0.45    # 点いている画面の明るさ (emission の強さ。ビューアでは 色 x この値。1 未満なので bloom でにじまない)

# 形の寸法。w (画面の枠の幅)・h (台座の底から枠の上端まで)・d (台座の奥行) は layout.py。
# panel_y = 画面の前面の位置 (台座の中心から。layout.py の _MAIN_Y / _SUB_FRONT と合わせる)。neck_up = 首 (柱) が画面を支える所より上へ出る長さ
MONITORS = {
    # 24型 (画面 53 x 30cm)。細い枠。高さを変えられるスタンド: 太い柱を一番上まで伸ばしている (画面の下端が机から 0.19)
    "monitor_main": dict(panel_h=0.32, panel_d=0.018, panel_y=0.0, bezel=0.008, bezel_bottom=0.02,
                         back=(0.36, 0.20, 0.03), neck_w=0.07, neck_d=0.035, neck_up=0.05, base_w=0.24),
    # 20型のテレビ (画面 44 x 25cm)。枠が太く、下の枠にスピーカー。厚みもある。首は短い (画面の下端が台座から 0.07)
    "monitor_sub": dict(panel_h=0.30, panel_d=0.035, panel_y=-0.02, bezel=0.014, bezel_bottom=0.035,
                        back=(0.30, 0.17, 0.025), neck_w=0.07, neck_d=0.025, neck_up=0.0, base_w=0.22),
}


def _monitor(name, body, screen, image=None):
    e, m = FURNITURE[name], MONITORS[name]
    hx, hy, top = e["w"] / 2, e["d"] / 2, e["h"]
    root = add_empty(name, (e["x"], e["y"], e["z0"]), rotation_deg(e))

    z_panel = top - m["panel_h"]                        # 枠の下端
    y0, y1 = m["panel_y"], m["panel_y"] + m["panel_d"]  # 枠の前面・背面
    bw, bh, bd = m["back"]                              # 背面のふくらみ (幅・高さ・厚み)
    z_mid = z_panel + m["panel_h"] * 0.45
    boxes_object(f"{name}_body", [
        (-hx, hx, y0, y1, z_panel, top, body),                                        # 枠
        (-bw / 2, bw / 2, y1, y1 + bd, z_mid - bh / 2, z_mid + bh / 2, body),         # 背面のふくらみ
        (-m["neck_w"] / 2, m["neck_w"] / 2, y1 + bd, y1 + bd + m["neck_d"], BASE_T, z_mid + m["neck_up"], body),   # 首 (柱)
        (-m["base_w"] / 2, m["base_w"] / 2, -hy, hy, 0, BASE_T, body),                # 台座
    ], parent=root)
    b = m["bezel"]
    boxes_object(f"{name}_screen", [   # 枠の前に 2mm だけ出した黒い面
        (-hx + b, hx - b, y0 - 0.002, y0, z_panel + m["bezel_bottom"], top - b, screen),
    ], parent=root)
    if image:   # 点いている画面: 黒い面の 0.5mm 前に画像を1枚
        z0 = z_panel + m["bezel_bottom"]
        image_quad(f"{name}_image", 2 * (hx - b) - 0.002, top - b - z0 - 0.002,
                   make_material(f"{name}_image", "#FFFFFF", roughness=0.2, emission=SCREEN_GLOW, texture=image, emission_texture=True),
                   Matrix.Translation((0, y0 - 0.0025, z0 + 0.001)), parent=root)
    return root


def _boxes():
    """サブモニターの下の白い箱2つ (中身は不明)。高さは同じで、大きさと白さが少し違う。間に 5mm のすき間"""
    e = FURNITURE["monitor_boxes"]
    hx, top = e["w"] / 2, e["h"]
    root = add_empty("monitor_boxes", (e["x"], e["y"], e["z0"]), rotation_deg(e))
    a = make_material("monitor_box_a", "#F4F4F0", roughness=0.8)
    b = make_material("monitor_box_b", "#EAE8E2", roughness=0.8)
    items = []
    for x0, x1, y0, y1, mat in ((hx - 0.12, hx, -0.085, 0.085, a),       # 正面から見て右の箱 (幅 12 x 奥行 17cm)
                                (-hx, -hx + 0.115, -0.085, 0.075, b)):   # 左の箱 (幅 11.5 x 奥行 16cm。少し手前にずれている)
        lid = 0.035   # かぶせるふた (箱より 1.5mm ずつ大きい。下の縁に影の線ができる)
        items += [(x0 + 0.0015, x1 - 0.0015, y0 + 0.0015, y1 - 0.0015, 0, top - lid + 0.002, mat),
                  (x0, x1, y0, y1, top - lid, top, mat)]
    boxes_object("monitor_boxes_body", items, parent=root)
    return root


def build_monitors():
    body = make_material("monitor_body", BLACK, roughness=0.5)
    screen = make_material("monitor_screen", SCREEN, roughness=0.15)
    _boxes()
    return _monitor("monitor_main", body, screen, image="screen_main.png"), _monitor("monitor_sub", body, screen)
