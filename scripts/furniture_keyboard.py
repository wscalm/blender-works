"""キーボードとマウス (仮。ユーザーにはまだ聞いていない。黒のフルサイズのキーボードと、ふつうの黒いマウス)。デスク2の上、メインモニターの前。

位置・大きさは layout.py (keyboard, mouse)。ローカル座標: 原点 = 底面の中心 / 正面 (座る人の側) = -Y / X = 正面から見て右
構成: Empty `keyboard` の下に `keyboard_body` (本体 + キー)。Empty `mouse` の下に `mouse_body` (角の丸い、ふくらんだ箱)。
どちらもクリック対象には未登録
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from layout import FURNITURE, rotation_deg

PITCH = 0.0185    # キーの間隔 (1 キー分 = 1u)。全部で 23u 並ぶ
KEY = 0.015       # キーの天面の大きさ
WIDTH_U = 23
CASE_H = 0.016    # 本体の高さ (キーはこの上に出る)
KEY_H = 0.008

# キーの並び。手前の行から。数字 = キーの幅 (u)、負の数 = すき間 (u)。メイン 15u / 矢印など 3u / テンキー 4u
MAIN = [
    [1.5, 1, 1.5, 7, 1.5, 1, 1.5],                        # Ctrl・Alt・スペース
    [2.25] + [1] * 10 + [2.75],                           # Shift
    [1.75] + [1] * 11 + [2.25],                           # CapsLock・Enter
    [1.5] + [1] * 12 + [1.5],                             # Tab
    [1] * 13 + [2],                                       # 数字・BackSpace
    None,                                                 # (ファンクションキーの前のすき間)
    [1, -1, 1, 1, 1, 1, -0.5, 1, 1, 1, 1, -0.5, 1, 1, 1, 1],   # Esc・F1〜F12
]
NAV = [[1, 1, 1], [-1, 1, -1], [], [1, 1, 1], [1, 1, 1], None, [1, 1, 1]]      # 矢印・Insert など
NUMPAD = [[2, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1], None, []]


def build_keyboard():
    e = FURNITURE["keyboard"]
    hx, hy = e["w"] / 2, e["d"] / 2
    root = add_empty("keyboard", (e["x"], e["y"], e["z0"]), rotation_deg(e))
    case = make_material("keyboard_case", "#151517", roughness=0.5)
    key = make_material("keyboard_key", "#26272A", roughness=0.6)
    boxes = [(-hx, hx, -hy, hy, 0, CASE_H, case)]
    left = -WIDTH_U * PITCH / 2                    # キーの並びは本体の左右の中央
    blocks = ((MAIN, 0.0), (NAV, 15.5), (NUMPAD, 19.0))
    y = -hy + 0.008 + PITCH / 2                     # 手前の行の中心
    rows_y = []
    for row in MAIN:
        rows_y.append(y)
        y += PITCH if row is not None else PITCH * 0.5
    for rows, offset in blocks:
        for row, yc in zip(rows, rows_y):
            if not row:
                continue
            u = offset
            for w in row:
                if w > 0:
                    x0 = left + u * PITCH + (PITCH - KEY) / 2
                    x1 = x0 + w * PITCH - (PITCH - KEY)
                    boxes.append((x0, x1, yc - KEY / 2, yc + KEY / 2, CASE_H, CASE_H + KEY_H, key, 0.0015))
                u += abs(w)
    boxes_object("keyboard_body", boxes, parent=root)
    return root


def build_mouse():
    e = FURNITURE["mouse"]
    hx, hy, top = e["w"] / 2, e["d"] / 2, e["h"]
    root = add_empty("mouse", (e["x"], e["y"], e["z0"]), rotation_deg(e))
    body = make_material("mouse_body", "#1B1B1E", roughness=0.4)
    soft_boxes_object("mouse_body", [
        (-hx, hx, -hy, hy, 0, top - 0.012, body, 0.024, (0.004, 0.006, 0.012)),
    ], parent=root, cuts=10)
    return root


def build_keyboard_mouse():
    return build_keyboard(), build_mouse()
