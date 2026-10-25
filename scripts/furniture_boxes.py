"""出窓の天板に置いた、箱買いの段ボール箱 2箱 (ユーザー指定の商品)。
お茶 = 伊藤園 ラベルレス お～いお茶 緑茶 460ml x 30本 (Smart Bottle BOX) / 水 = い・ろ・は・す ラベルレス 560ml x 24本 (ラベルレスの箱は 560ml)。

大きさは商品の外寸 (layout.py)。少しずつ斜めに置いている (yaw)。実物の箱はテープではなく糊で閉じてあるので、テープは貼らない。
ローカル座標: 原点 = 箱の底面の中心 / 正面 = -Y
構成: Empty `box_tea` / `box_water` の下に `<名前>_body` (段ボール。印刷は textures/box_tea.jpg・box_water.jpg
(tools/make_boxes.py が商品の写真に合わせて描いた物) を面ごとに貼る。面の並びは layout.box_atlas)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props import *
from layout import BOX_IMAGE, FURNITURE, box_atlas, rotation_deg


def build_box(name):
    e = FURNITURE[name]
    w, d, h = e["w"], e["d"], e["h"]
    root = add_empty(name, (e["x"], e["y"], e["z0"]), rotation_deg(e))
    bounds = (-w / 2, w / 2, -d / 2, d / 2, 0, h)
    body = boxes_object(f"{name}_body", [(*bounds, picture_material(f"{name}_cardboard", f"{name}.jpg", roughness=0.9, specular=0.3))],
                        parent=root, bevel=0.003)
    atlas_box_uvs(body, bounds, box_atlas(name), BOX_IMAGE)
    return root


def build_boxes():
    return build_box("box_tea"), build_box("box_water")
