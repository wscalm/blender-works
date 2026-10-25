"""ローテーブル。ウォールナットの木目の天板 + 黒い角脚。ラグの中心に、長辺をソファーと平行に置く。

脚は短辺ごとに「ロ」の字の枠: 脚2本を、天板の下と床の2か所で横棒がつなぐ。
位置・大きさは layout.py (table)。ローカル座標: 原点 = 足元の中心 / 正面 (ソファー側) = -Y / 長辺は X
構成: Empty `table` の下に、天板 `table_top` と脚の枠 `table_legs`。
天板の上の小物 (写真 reference/IMG_1100): Empty `table_items` (部屋の座標のまま) の下に、南の端のティッシュの箱 `table_tissue` (白に紺の帯。
長い辺を東西に、東の縁寄り) と飛び出たティッシュ `table_tissue_paper`・その上に斜めに置いたテレビのリモコン `table_remote`、
西の縁 (ソファー側) のウェットティッシュのケース `table_wipes`、真ん中より少し北の東の縁に立てた黄色いタイマー `table_timer` (表示は西 = ソファー向き)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props import *
from layout import FURNITURE

TOP_T = 0.025          # 天板の厚み
LEG = 0.025            # 角脚・横棒の太さ (正方形)
INSET_END = 0.05       # 短辺の縁から枠の外面まで
INSET_SIDE = 0.02      # 長辺の縁から脚の外面まで
LEG_COLOR = "#1C1C1E"  # 黒 (デスクの脚と同じ色)


def build_table():
    e = FURNITURE["table"]
    hx, hy, top = e["w"] / 2, e["d"] / 2, e["h"]
    root = add_empty("table", (e["x"], e["y"], e["z0"]), FACING_DEG[e["facing"]])
    boxes_object("table_top", [(-hx, hx, -hy, hy, top - TOP_T, top, wood_material("table_top", "walnut"))], parent=root)

    black = make_material("table_leg", LEG_COLOR, roughness=0.5)
    z_under = top - TOP_T            # 天板の下面
    oy, iy = hy - INSET_SIDE, hy - INSET_SIDE - LEG   # 脚の外面・内面 (Y)
    legs = []
    for sx in (-1, 1):   # 短辺 (左右の端) ごとに「ロ」の字の枠
        x0, x1 = sx * (hx - INSET_END - LEG), sx * (hx - INSET_END)
        for sy in (-1, 1):
            legs.append((x0, x1, sy * iy, sy * oy, 0, z_under, black))                 # 脚 (床から天板の下まで)
        legs.append((x0, x1, -iy, iy, 0, LEG, black))                                  # 床の横棒
        legs.append((x0, x1, -iy, iy, z_under - LEG, z_under, black))                  # 天板の下の横棒
    boxes_object("table_legs", legs, parent=root)
    _items(root, e["z0"] + top)
    return root


def _items(root, z):
    """天板 (上面の高さ z) の上の小物。部屋の座標で置く (テーブルは X 2.975〜3.325 / Y 2.075〜2.925)"""
    g = world_group("table_items", root)
    # ティッシュの箱 (24 x 11.5 x 8.5cm): 白い箱の下に紺の帯、上面の縁に水色の線と取り出し口のフィルム。
    # 印刷は textures/tissue_box.jpg (tools/make_prints.py) を面ごとに貼る (画像の中の面の並びは make_prints の TISSUE_ATLAS と同じ)
    x0, x1, y0, y1, h = 3.06, 3.30, 2.10, 2.215, 0.085
    box = boxes_object("table_tissue", [(x0, x1, y0, y1, z, z + h, picture_material("table_tissue", "tissue_box.jpg", roughness=0.7))],
                       parent=g, bevel=0.003)
    front, side = (0, 0, 384, 136), (0, 144, 184, 280)
    atlas_box_uvs(box, (x0, x1, y0, y1, z, z + h),
                  dict(front=front, back=front, left=side, right=side, top=(0, 288, 384, 472), plain=(192, 144, 384, 280)), (512, 512))
    cx, cy, top = (x0 + x1) / 2, (y0 + y1) / 2, z + h
    paper = make_material("table_tissue_paper", "#FBFBFA", roughness=1.0, specular=0.2)
    soft_boxes_object("table_tissue_paper", [   # 取り出し口から飛び出たティッシュ (くしゃっとした塊)
        (cx - 0.055, cx + 0.05, cy - 0.032, cy + 0.03, top - 0.01, top + 0.028, paper, 0.012, (0.006, 0.006, 0.01)),
    ], parent=g, cuts=10, wrinkle=0.007, wrinkle_size=0.045, seed=41)
    # テレビのリモコン (黒、19 x 4.8 x 1.8cm): ティッシュの箱の上に斜めに乗る
    remote = make_material("table_remote", "#18181A", roughness=0.45)
    keys = make_material("table_remote_keys", "#55585C", roughness=0.4)
    m = place(cx + 0.005, cy + 0.004, top + 0.004, yaw=28)
    solids_object("table_remote", [rot_box(-0.095, 0.095, -0.024, 0.024, 0, 0.018, remote, m, 0.006),
                                   rot_box(-0.06, 0.07, -0.016, 0.016, 0.018, 0.0195, keys, m, 0.0008)], parent=g)
    # ウェットティッシュのケース (白、12 x 19 x 5.5cm。長い辺を南北に): 上面に水色のふた
    wipe = make_material("table_wipes", "#F1F2F0", roughness=0.35)
    lid = make_material("table_wipes_lid", "#A8C8E0", roughness=0.35)
    soft_boxes_object("table_wipes", [
        (2.99, 3.11, 2.25, 2.44, z, z + 0.055, wipe, 0.012, (0.002, 0.002, 0.003)),
        (3.015, 3.085, 2.30, 2.39, z + 0.052, z + 0.0615, lid, 0.004, (0.0, 0.0, 0.001)),
    ], parent=g, cuts=8)
    # 黄色いタイマー (7.5cm 角、厚み 3cm)。東の縁に立て、表示 (濃い灰色) は西 = ソファーの方
    yellow = make_material("table_timer", "#F2C21B", roughness=0.35)
    lcd = make_material("table_timer_lcd", "#3A3D3A", roughness=0.2)
    soft_boxes_object("table_timer", [(3.25, 3.28, 2.56, 2.635, z, z + 0.075, yellow, 0.008, (0.0, 0.0, 0.0))], parent=g, cuts=6)
    boxes_object("table_timer_lcd", [(3.2485, 3.252, 2.5755, 2.6195, z + 0.012, z + 0.057, lcd, 0.001)], parent=g)
    return g
