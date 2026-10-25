"""夜の照明 (ライトマップの焼き付け用)。

光源は2つ:
  - シーリングライトの乳白カバー (build_room.py の room_ceiling_light。発光する面がそのまま光源になる)
  - 出窓の外からの弱い青白い光 (街灯と夜空の明かりのつもり)
東の掃き出し窓はカーテンを閉めているので、外の光は入れない。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from room_spec import *


def setup_night_lights():
    """プレビュー照明 (views.setup_preview_lights) を消して、夜の照明にする。"""
    for obj in [o for o in bpy.data.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(obj)
    setup_world(color=hex_color("#0B1626"), strength=0.3)   # 夜空。出窓のガラス越しにわずかに入る

    b = NORTH_BAY
    bx = (b["x0"] + b["x1"]) / 2
    bpy.ops.object.light_add(type='AREA', location=(bx, ROOM_D + b["depth"] + 0.5, (b["sill_z"] + b["head_z"]) / 2 + 0.3))
    outside = bpy.context.object
    outside.name = "night_outside"
    outside.data.shape = 'RECTANGLE'
    outside.data.size, outside.data.size_y = b["x1"] - b["x0"] + 0.4, 1.0
    outside.data.energy = 4
    outside.data.color = hex_color("#9DB4E0")
    look_at(outside, (bx, ROOM_D - 1.5, 0.3))   # 斜め上から室内へ (面光源は -Z 方向へ光る)
