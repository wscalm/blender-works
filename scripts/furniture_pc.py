"""デスクトップPC (ケース = In Win 301 白、IW-CF07B 301-White) とプリンター (ブラザー PRIVIO DCP-J1800N 白)。どちらもデスク1の天板の上。

ケースの形は製品写真 (pcper.com のレビュー) から: 白い鋼板の箱。正面の右寄りに電源ボタン、縦長の水色に光る IN WIN のロゴ、
イヤホン・マイクの口と USB 2つ。正面から見て左の側面は全面が色の濃い強化ガラス (上下に黒い帯)。底に黒い脚 (前後に横長の板2枚)。
ガラスは中が見えない濃い色の板として作る (中の部品は作らない)。
位置・大きさは layout.py (pc, printer)。ローカル座標: 原点 = 足元の中心 / 正面 = -Y / X = 正面から見て右
構成: Empty `pc` の下に `pc_case` (本体・脚・ボタン類・光るロゴ) と `pc_glass` (ガラスの側面)。
ケースの上 (写真 reference/IMG_1099): Empty `pc_top_items` (部屋の座標のまま) の下に、黒い薄型の機器 `pc_top_device` とテレビのリモコン `pc_top_remote`。
Empty `printer` の下に `printer_body` (幅 400 x 奥行 343 x 高さ 172mm)。プリンターはクリック対象には未登録
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props import *
from layout import FURNITURE

FOOT_H = 0.015     # 脚の高さ
BODY_W = 0.19      # 本体の幅 (脚は layout の幅 0.208 で、本体より左右に少し張り出す)
GLASS_T = 0.004    # 側面のガラスの厚み
COL_X = 0.06       # 正面のボタン・ロゴ・USB の列の中心 (正面から見て右寄り)


def build_pc():
    e = FURNITURE["pc"]
    hx, hy, top = e["w"] / 2, e["d"] / 2, e["h"]
    bx, by = BODY_W / 2, hy - 0.005
    root = add_empty("pc", (e["x"], e["y"], e["z0"]), FACING_DEG[e["facing"]])
    white = make_material("pc_white", "#F1F1EF", roughness=0.45)
    black = make_material("pc_black", "#141416", roughness=0.4)
    port = make_material("pc_port", "#2D5FA8", roughness=0.4)          # USB 3.0 の口 (青)
    logo = make_material("pc_logo", "#8CCBF0", emission=2.0)            # 白モデルはロゴが水色に光る
    glass = make_material("pc_glass", "#20252B", roughness=0.08)        # 色の濃い強化ガラス

    def front(x0, x1, z_from_top0, z_from_top1, mat, t=0.002):
        """正面に t だけ出した部品。高さは天面からの距離で指定する"""
        return (COL_X + x0, COL_X + x1, -by - t, -by, top - z_from_top1, top - z_from_top0, mat)

    case = [(-bx, bx, -by, by, FOOT_H, top, white)]                                # 本体
    for y0, y1 in ((-hy, -hy + 0.05), (hy - 0.05, hy)):                            # 脚 (前後の黒い板)
        case.append((-hx, hx, y0, y1, 0, FOOT_H, black))
    case += [
        front(-0.0085, 0.0085, 0.012, 0.029, black),                               # 電源ボタン
        front(-0.0095, 0.0095, 0.056, 0.136, logo, t=0.0015),                      # IN WIN のロゴ
        front(-0.004, 0.004, 0.143, 0.151, black, t=0.001),                        # イヤホン・マイクの口
        front(-0.004, 0.004, 0.159, 0.167, black, t=0.001),
        front(-0.003, 0.003, 0.176, 0.190, port, t=0.001),                         # USB 3.0 x2 (縦向き)
        front(-0.003, 0.003, 0.196, 0.210, port, t=0.001),
    ]
    boxes_object("pc_case", case, parent=root)

    # 正面から見て左の側面 (-X) の全面ガラス。上下の帯は黒く塗られている
    gx0, gx1, gy = -bx - GLASS_T, -bx, by - 0.003
    z0, z1 = FOOT_H + 0.003, top - 0.003
    boxes_object("pc_glass", [
        (gx0, gx1, -gy, gy, z0, z0 + 0.030, black),
        (gx0, gx1, -gy, gy, z0 + 0.030, z1 - 0.035, glass),
        (gx0, gx1, -gy, gy, z1 - 0.035, z1, black),
    ], parent=root)

    # ケースの上: 黒い薄型の機器 (幅はケースと同じ、高さ 5cm) と、その上に斜めに置いたリモコン
    g = world_group("pc_top_items", root)
    z = e["z0"] + top
    x0, x1, y0, y1 = e["x"] - hx + 0.003, e["x"] + hx, e["y"] - hy + 0.06, e["y"] + hy - 0.005
    device = make_material("pc_top_device", "#121214", roughness=0.3)
    boxes_object("pc_top_device", [(x0, x1, y0, y1, z, z + 0.05, device),
                                   (x0 + 0.01, x1 - 0.01, y1 - 0.001, y1 + 0.0015, z + 0.012, z + 0.018, make_material("pc_top_device_line", "#5A5D62", roughness=0.3), 0.0005)],
                 parent=g, bevel=0.003)
    remote = make_material("pc_top_remote", "#1A1A1C", roughness=0.45)
    keys = make_material("pc_top_remote_keys", "#4E5156", roughness=0.4)
    m = place((x0 + x1) / 2 + 0.005, y0 + 0.17, z + 0.05, yaw=-8)
    solids_object("pc_top_remote", [rot_box(-0.025, 0.025, -0.095, 0.095, 0, 0.02, remote, m, 0.006),
                                    rot_box(-0.017, 0.017, -0.07, 0.06, 0.02, 0.0215, keys, m, 0.0008)], parent=g)
    return root


def build_printer():
    """ブラザー DCP-J1800N (白の A4 インクジェット複合機)。形は製品写真 (pc.watch.impress.co.jp) から:
    下から 用紙カセット → 紙の出口 → 操作パネル (左寄りの画面。少し奥へ引っ込んだ帯) → スキャナー → 天板 (左半分は ADF のふた)"""
    e = FURNITURE["printer"]
    hx, hy, top = e["w"] / 2, e["d"] / 2, e["h"]
    root = add_empty("printer", (e["x"], e["y"], e["z0"]), FACING_DEG[e["facing"]])
    white = make_material("printer_white", "#EDEDEA", roughness=0.5)
    light = make_material("printer_light", "#F5F5F3", roughness=0.4)   # 天板と ADF のふた (少し明るい)
    gray = make_material("printer_gray", "#D2D2CF", roughness=0.5)     # 用紙カセットの前面
    dark = make_material("printer_dark", "#2A2C30", roughness=0.3)     # 操作パネルの画面・紙の出口

    z_panel0, z_panel1 = 0.080, 0.128       # 操作パネルの帯 (前面が 8mm 奥へ引っ込む)
    z_lid = top - 0.012                     # 天板 (スキャナーのふた) の下面
    py = -hy + 0.008                        # 操作パネルの帯の前面
    button = make_material("printer_button", "#D8D9D8", roughness=0.35)
    boxes_object("printer_body", [
        (-hx, hx, -hy, hy, 0, z_panel0, white, 0.007),                             # 本体の下 (用紙カセット・紙の出口)
        (-hx, hx, py, hy, z_panel0, z_panel1, white, 0.005),                       # 操作パネルの帯
        (-hx, hx, -hy, hy, z_panel1, z_lid, white, 0.007),                         # スキャナー
        (-hx + 0.004, hx - 0.004, -hy + 0.004, hy - 0.004, z_lid, top - 0.004, light, 0.006),   # 天板
        (-hx + 0.012, -0.01, -hy + 0.03, hy - 0.012, top - 0.004, top, light, 0.003),     # ADF のふた (正面から見て左半分)
        (-0.085, -0.03, py - 0.002, py, z_panel0 + 0.004, z_panel1 - 0.005, dark, 0.002),  # 操作パネルの画面 (消えている)
        (-0.15, 0.15, -hy - 0.002, -hy, 0.036, 0.062, dark, 0.002),                # 紙の出口
        (-0.13, 0.13, -hy - 0.02, -hy - 0.001, 0.037, 0.041, gray, 0.0015),        # 紙の出口から出た受け皿
        (-0.17, 0.17, -hy - 0.002, -hy, 0.006, 0.030, gray, 0.002),                # 用紙カセット
        (-0.03, 0.03, -hy - 0.003, -hy - 0.001, 0.012, 0.02, dark, 0.002),         # カセットの指を掛けるくぼみ
        (0.02, 0.07, -hy - 0.0008, -hy, z_panel1 + 0.012, z_panel1 + 0.017, gray, 0.0003),   # 社名の代わりの帯
        (-0.17, -0.13, py - 0.0008, py, z_panel0 + 0.014, z_panel0 + 0.032, gray, 0.0003),    # 左の印刷の印
        (0.155, 0.172, py - 0.001, py, z_panel0 + 0.014, z_panel0 + 0.024, dark, 0.0005),     # カードを差す口
        *[(-0.019, -0.011, py - 0.0016, py, z - 0.004, z + 0.004, button, 0.0015)   # 画面の右のボタン 3つ
          for z in (z_panel0 + 0.011, z_panel0 + 0.024, z_panel0 + 0.037)],
        (0.095, 0.105, py - 0.0016, py, z_panel0 + 0.019, z_panel0 + 0.029, button, 0.0015),  # 電源ボタン
    ], parent=root)
    return root
