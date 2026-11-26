"""部屋の外殻 + 全家具を組み立て、確認用レンダリング → 夜の照明の焼き付け → .blend / .glb を書き出す。

    ./run_blender.sh scripts/build_all.py                 # 本番 (焼き付け 256 サンプル、4096px)
    ./run_blender.sh scripts/build_all.py --samples 32 --size 2048 --no-render   # 速いがざらつく (形の確認用)

家具を増やしたら build_scene() に足す (closeup.py も build_scene() を使う)。
確認用レンダリング (renders/*.png) は昼のプレビュー照明、glb と焼き付け画像 (models/room_lightmap.webp・room_glossmap.webp) は夜の照明。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from build_room import build_shell
from furniture_bed import build_bed
from furniture_bookshelf import build_bookshelf
from furniture_boxes import build_boxes
from furniture_clock import build_clock
from furniture_curtain import build_curtain
from furniture_desk import build_desks
from furniture_desk_items import build_desk_items
from furniture_hanger_rail import build_hanger_rail
from furniture_keyboard import build_keyboard_mouse
from furniture_monitor import build_monitors
from furniture_pc import build_pc, build_printer
from furniture_rug import build_rug
from furniture_side_table import build_side_table
from furniture_sofa import build_sofa
from furniture_stool import build_stool
from furniture_table import build_table
from furniture_tension_shelf import build_tension_shelf
from furniture_tv import build_tv
from furniture_tv_stand import build_tv_stand
from bake import bake_lightmap
from lighting import setup_night_lights
from views import render_standard_views, setup_preview_lights


def build_scene():
    """空のシーンに、外殻・全家具・プレビュー照明を作る。"""
    reset_scene()
    build_shell()
    build_curtain()
    build_boxes()
    build_bed()
    build_sofa()
    build_stool()
    build_side_table()
    build_rug()
    build_table()
    build_desks()
    build_bookshelf()
    build_tension_shelf()
    build_hanger_rail()
    build_tv_stand()
    build_tv()
    build_pc()
    build_printer()
    build_monitors()
    build_keyboard_mouse()
    build_desk_items()
    build_clock()
    # (家具は今後ここに追加していく)
    add_box_uvs([o for o in bpy.context.scene.objects if o.type == 'MESH'])   # テクスチャ (木目) 用の UV
    setup_preview_lights()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=256, help="焼き付けのサンプル数 (OIDN でノイズを取るので 256 で足りる)")
    ap.add_argument("--size", type=int, default=4096, help="ライトマップの画像の一辺 (px)")
    ap.add_argument("--no-render", action="store_true", help="確認用レンダリングを省く")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

    build_scene()
    if not args.no_render:
        render_standard_views()
    setup_night_lights()
    bake_lightmap(size=args.size, samples=args.samples)
    save_blend("room.blend")
    export_glb("room.glb")
