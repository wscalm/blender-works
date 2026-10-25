"""確認用のプレビュー照明とカメラ視点。ここで置くライトとカメラは .glb には書き出されない。"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from room_spec import *

# 壁に付く物は壁と一緒に隠す (断面図のように、手前の壁を消して中を見せるため)
WALL_GROUPS = {
    "north": ["room_wall_north", "room_bay_window", "box_tea", "box_water"],
    "south": ["room_wall_south", "tension_shelf", "hanger_rail"],
    "east": ["room_wall_east", "room_window_east", "aircon", "curtain", "clock"],
    "west": ["room_wall_west", "room_door_west", "room_closet_door", "room_intercom"],
}
CEILING = ["room_ceiling", "room_bay_roof", "room_ceiling_light"]   # 上から見るときに隠す (出窓の屋根とシーリングライトも)


def setup_preview_lights():
    setup_world(color=hex_color("#D5E2F0"), strength=0.8)   # 窓の外の空 + 環境光
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    sun = bpy.context.object
    sun.data.energy = 1.4
    sun.rotation_euler = (math.radians(45), 0, math.radians(35))
    # 天井灯の代わり。下向きの面光源にして、天井そのものが白飛びしないようにする
    bpy.ops.object.light_add(type='AREA', location=(ROOM_W / 2, ROOM_D / 2, ROOM_H - 0.1))
    lamp = bpy.context.object
    lamp.data.energy = 90
    lamp.data.size = 1.5
    lamp.data.color = (1.0, 0.96, 0.9)


def render_standard_views(prefix=""):
    cx, cy = ROOM_W / 2, ROOM_D / 2
    hide = lambda *groups: [n for g in groups for n in WALL_GROUPS[g]] + CEILING

    # 真上から (天井を消す)。上=北、右=東
    # (出窓が北へ出ている分、中心を北へずらして範囲を広げる)
    ty = (ROOM_D + NORTH_BAY["depth"] - WALL_T) / 2
    render_view(f"{prefix}top.png", (cx, ty, 8), (cx, ty, 0), ortho_scale=6.3, hide=CEILING)
    # 南西の上空から (南壁・西壁・天井を消す) → 北壁・東壁・窓・エアコンが見える
    render_view(f"{prefix}iso_sw.png", (-1.9, -2.6, 5.0), (cx, cy, 0.7), lens=32,
                hide=hide("south", "west"))
    # 北東の上空から (北壁・東壁・天井を消す) → 南壁・西壁・ドア・収納が見える
    render_view(f"{prefix}iso_ne.png", (ROOM_W + 1.9, ROOM_D + 2.6, 5.0), (cx, cy, 0.7), lens=32,
                hide=hide("north", "east"))
    # 南東の上空から (南壁・東壁・天井を消す) → 東向きの家具の正面と、北壁・西壁が見える
    render_view(f"{prefix}iso_se.png", (ROOM_W + 1.9, -2.6, 5.0), (cx, cy, 0.7), lens=32,
                hide=hide("south", "east"))
    # 部屋の隅に立った目線 (天井あり)。実際のサイトで見る景色に近い
    render_view(f"{prefix}eye_sw.png", (0.3, 0.3, 1.55), (3.6, 2.7, 1.0), lens=15)
    render_view(f"{prefix}eye_ne.png", (ROOM_W - 0.3, ROOM_D - 0.3, 1.55), (0.9, 0.9, 1.0), lens=15)
    # 南側から北壁 (出窓) を見る
    render_view(f"{prefix}eye_s.png", (2.6, 0.4, 1.5), (1.0, ROOM_D, 1.1), lens=22)
    # 部屋の外 (北側) から出窓を見る。突き出し方とコの字のガラスの確認用
    bx = (NORTH_BAY["x0"] + NORTH_BAY["x1"]) / 2
    render_view(f"{prefix}outside_bay.png", (bx + 1.2, ROOM_D + 2.6, 2.4), (bx, ROOM_D + 0.3, 1.3), lens=30)
