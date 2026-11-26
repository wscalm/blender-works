"""照明を焼き付ける。Cycles を GPU で使う。焼く画像は2枚 (どちらも全メッシュで1枚の画像を分け合う):

  lightmap  (models/room_lightmap.webp) 拡散光 (直接光 + 間接光)。見た目 = 材質の色 × この値
  glossmap  (models/room_glossmap.webp) ツヤ・映り込み (光沢の反射)。見た目にそのまま足す。
            カメラは目の位置から動かない (首振りだけ) ので、反射も「目の位置から見た向き」で焼いておける (view_from = ACTIVE_CAMERA)

各メッシュの UV は2つ:
  UVMap    (glTF の TEXCOORD_0) テクスチャ (木目など) 用。実寸の箱投影 (1 = 1m)。build_scene の common.add_box_uvs が作る
  lightmap (glTF の TEXCOORD_1) 焼き付け用の展開。ここで作る (Smart UV Project で島に分け、目からの距離で大きさを変えて棚に詰める)

焼いた値 B は「照度 / π」。見た目の明るさ = 材質の色 × B (three.js の lightMap と同じ式)。
画像は 8bit。B を K で割って sRGB で符号化してある。K は scene["lightmap_intensity"] / scene["glossmap_intensity"] に入れ、
glb の extras (gltf.scene.userData) で Web 側へ渡す。
"""
import math
import os
import sys
import time

import numpy as np
from mathutils import geometry

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from layout import VIEW
from room_spec import *

LIGHTMAP_FILE = "room_lightmap.webp"
GLOSSMAP_FILE = "room_glossmap.webp"

# 目からの距離 d (m) に応じたライトマップの細かさの倍率 = D_REF / d (W_MIN〜W_MAX に収める)。
# 目の前の机の上は細かく、遠くの壁や天井は粗くする (画面上の大きさに合わせる)
D_REF, W_MIN, W_MAX = 1.2, 0.35, 2.5


def bake_targets():
    """焼き付けるメッシュ。カスタムプロパティ bake_skip の付いた物 (キーの光る字など、面のすぐ上に重ねた板) は除く
    (焼き付けの間は隠す。影を落とさないように)"""
    return [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.get("bake_skip")]


PAD = 3   # 島と島の間のすき間 (px)。焼き付けの margin で、島の端の色をここへ伸ばす


def _visible_from_room(center):
    """面の中心が部屋の内側 (壁の厚みの中と出窓の中を含む) にあるか。壁の外面・床の裏・天井の上は False。"""
    x, y, z = center
    b, e = NORTH_BAY, 0.01
    in_room = (-WALL_T + e < x < ROOM_W + WALL_T - e and -WALL_T + e < y < ROOM_D + WALL_T - e
               and -e < z < ROOM_H + 0.05)
    in_bay = (b["x0"] - 0.06 < x < b["x1"] + 0.06 and ROOM_D - e < y < ROOM_D + b["depth"] + e
              and b["sill_z"] - 0.05 < z < b["head_z"] + 0.05)
    return in_room or in_bay


def _lit_by_lightmap(mat):
    """焼いた光を使う材質か。ガラス (半透明) と発光する物 (照明のカバー・表示ランプ) は Web 側で光らせるので使わない。"""
    bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat else None
    if bsdf is None:
        return True
    return bsdf.inputs["Alpha"].default_value >= 1.0 and bsdf.inputs["Emission Strength"].default_value <= 0.0


def add_lightmap_uvs(objs, size):
    """全メッシュに lightmap の UV を作る (テクスチャ用の UVMap は build_scene の add_box_uvs が先に作ってある)。

    1. 部屋の中から見えて焼いた光を使う面だけを、Smart UV Project で島に分けて展開する (面取りの面は隣の大きな面と同じ島になる)
    2. 島ごとに、実寸 × 目からの距離の倍率 の大きさの長方形を、全メッシュで1枚の画像に棚詰めする
    見えない面と焼いた光を使わない面は、画像の隅の1点に潰す。
    細すぎて島が1px に満たない物 (針金など。カスタムプロパティ lightmap_proxy = 近くの物の名前) は島を作らず、
    全体をその近くの物の1点 (_proxy_uv) に潰して、そこの光を借りる。借りる点は、物の中心に一番近い点
    (カスタムプロパティ lightmap_proxy_at = 物のローカル座標の点 があれば、その点に一番近い点。物の中心が暗い奥にある綿棒の束など)。
    布 (カーテン・毛布) のように自分で重ならない展開を持つ物 (カスタムプロパティ lightmap_uv = その UV の名前) は、
    Smart UV Project の代わりにその展開をそのまま島にする (曲面を細かい島に分けると、島の境目が焼き付けの継ぎ目に見えるため)。その UV は最後に消す
    """
    bpy.context.view_layer.update()   # 親 (家具の Empty) の回転を matrix_world に反映させる
    eye = Vector(VIEW["eye"])
    use = {}
    for obj in objs:
        obj.data.uv_layers.new(name="lightmap")
        obj.data.uv_layers.active = obj.data.uv_layers["lightmap"]
        mw, slots = obj.matrix_world, obj.material_slots
        use[obj.name] = [not obj.get("lightmap_proxy") and _visible_from_room(mw @ p.center) and
                         _lit_by_lightmap(slots[p.material_index].material if slots else None)
                         for p in obj.data.polygons]

    bpy.ops.object.select_all(action='DESELECT')
    for obj in objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        for v in bm.verts:
            v.select = False
        for e in bm.edges:
            e.select = False
        for f in bm.faces:
            f.select = use[obj.name][f.index]
        bm.select_flush_mode()
        bmesh.update_edit_mesh(obj.data)
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in objs:   # 自分の展開を持つ物は、その展開で上書きする
        if obj.get("lightmap_uv"):
            src, dst = obj.data.uv_layers[obj["lightmap_uv"]].data, obj.data.uv_layers["lightmap"].data
            for i in range(len(dst)):
                dst[i].uv = src[i].uv

    # 島を集める: 辺を共有し、その辺の両端の UV が一致する面どうしを同じ島にする
    islands = []   # (obj, [面番号], uv の範囲 (u0, v0, u1, v1), m/UV, 目からの距離の倍率)
    for obj in objs:
        mesh, mw = obj.data, obj.matrix_world
        uv = mesh.uv_layers["lightmap"].data
        ok = use[obj.name]
        root = list(range(len(mesh.polygons)))

        def find(i):
            while root[i] != i:
                root[i] = root[root[i]]
                i = root[i]
            return i
        edge_loops = {}
        for p in mesh.polygons:
            if not ok[p.index]:
                continue
            n = p.loop_total
            for k in range(n):
                la, lb = p.loop_start + k, p.loop_start + (k + 1) % n
                va, vb = mesh.loops[la].vertex_index, mesh.loops[lb].vertex_index
                key = (min(va, vb), max(va, vb))
                uv_by_vert = {va: tuple(uv[la].uv), vb: tuple(uv[lb].uv)}
                other = edge_loops.get(key)
                if other is None:
                    edge_loops[key] = (p.index, uv_by_vert)
                    continue
                q, quv = other
                if all((Vector(uv_by_vert[v]) - Vector(quv[v])).length < 1e-6 for v in key):
                    root[find(p.index)] = find(q)
        groups = {}
        for p in mesh.polygons:
            if ok[p.index]:
                groups.setdefault(find(p.index), []).append(p.index)
        for faces in groups.values():
            area_w = area_uv = 0.0
            us, vs, dists, center = [], [], [], Vector()
            for fi in faces:
                p = mesh.polygons[fi]
                a = p.area
                area_w += a
                center += (mw @ p.center) * a
                pts = [uv[li].uv for li in range(p.loop_start, p.loop_start + p.loop_total)]
                area_uv += abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y
                                   for i in range(len(pts)))) / 2
                us += [t.x for t in pts]
                vs += [t.y for t in pts]
                dists += [((mw @ mesh.vertices[v].co) - eye).length for v in p.vertices]
            if area_w <= 0 or area_uv <= 1e-12:
                continue
            d = max(0.3, 0.5 * (min(dists) + ((center / area_w) - eye).length))
            islands.append((obj, faces, (min(us), min(vs), max(us), max(vs)), math.sqrt(area_w / area_uv),
                            max(W_MIN, min(W_MAX, D_REF / d))))

    # 島の長方形 (実寸 × 倍率) を棚詰めする。入りきらなければ全体の細かさを下げてやり直す
    dims = [((u1 - u0) * s * w, (v1 - v0) * s * w) for _, _, (u0, v0, u1, v1), s, w in islands]
    area = sum(a * b for a, b in dims)
    density = math.sqrt(0.62 * size * size / area)   # px/m (倍率 1 の所)
    while True:
        placed, ok = _shelf_pack(dims, density, size)
        if ok:
            break
        density *= 0.97
    weights = [w for *_, w in islands]
    print(f"LIGHTMAP UV: {len(islands)} islands, {density:.0f} px/m at x1 "
          f"({density * min(weights):.0f}〜{density * max(weights):.0f} px/m)")

    placed_faces = set()
    for (obj, faces, (u0, v0, u1, v1), s, w), (x0, y0, wp, hp, rot) in zip(islands, placed):
        uv = obj.data.uv_layers["lightmap"].data
        k = s * w * density   # px / UV
        for fi in faces:
            p = obj.data.polygons[fi]
            for li in range(p.loop_start, p.loop_start + p.loop_total):
                a, b = (uv[li].uv.x - u0) * k, (uv[li].uv.y - v0) * k
                if rot:
                    a, b = b, a
                uv[li].uv = ((x0 + PAD + a) / size, (y0 + PAD + b) / size)
            placed_faces.add((obj.name, fi))
    for obj in objs:   # 見えない面・焼いた光を使わない面は隅の1点へ。光を借りる物は借りる先の1点へ
        uv = obj.data.uv_layers["lightmap"].data
        src = bpy.data.objects.get(obj.get("lightmap_proxy", ""))
        point = _proxy_uv(obj, src, placed_faces, eye) if src else None
        for p in obj.data.polygons:
            if (obj.name, p.index) not in placed_faces:
                for li in range(p.loop_start, p.loop_start + p.loop_total):
                    uv[li].uv = point or (0.5 / size, 0.5 / size)
        obj.data.uv_layers.active = obj.data.uv_layers["UVMap"]   # 書き出しと表示は UVMap を先頭 (TEXCOORD_0) にする
        obj.data.uv_layers["UVMap"].active_render = True
    for obj in objs:   # 島の元にした展開は glb に出さない
        if obj.get("lightmap_uv"):
            obj.data.uv_layers.remove(obj.data.uv_layers[obj["lightmap_uv"]])


def _proxy_uv(obj, src, placed_faces, eye):
    """細い物 obj に使わせる lightmap の UV: 借りる先 src の焼く面のうち、目の側を向いた面で obj の中心
    (lightmap_proxy_at があればその点) に一番近い点の UV"""
    mw = obj.matrix_world
    if "lightmap_proxy_at" in obj:
        target = mw @ Vector(obj["lightmap_proxy_at"])
    else:
        target = sum((mw @ v.co for v in obj.data.vertices), Vector()) / len(obj.data.vertices)
    sw, mesh = src.matrix_world, src.data
    uv = mesh.uv_layers["lightmap"].data
    normal_mat = sw.to_3x3().inverted_safe().transposed()
    best = None
    for p in mesh.polygons:
        c = sw @ p.center
        if (src.name, p.index) not in placed_faces or (normal_mat @ p.normal).dot(eye - c) <= 0:
            continue
        loops = list(range(p.loop_start, p.loop_start + p.loop_total))
        co = [sw @ mesh.vertices[mesh.loops[li].vertex_index].co for li in loops]
        for k in range(1, len(loops) - 1):   # 扇形に三角形へ分ける
            tri = (co[0], co[k], co[k + 1])
            if geometry.area_tri(*tri) < 1e-10:   # 回転体の軸の所の潰れた三角形 (UV の補間ができない)
                continue
            q = geometry.closest_point_on_tri(target, *tri)
            d = (q - target).length
            if best is None or d < best[0]:
                tri_uv = [Vector((*uv[loops[i]].uv, 0.0)) for i in (0, k, k + 1)]
                best = (d, geometry.barycentric_transform(q, *tri, *tri_uv))
    if best is None:
        print(f"LIGHTMAP PROXY: {src.name} に {obj.name} の借りる面が無い")
        return None
    return (best[1].x, best[1].y)


def _shelf_pack(dims, density, size):
    """長方形 (実寸 m) を高さ順に棚へ詰める。返り値: 長方形ごとの (x0, y0, 幅px, 高さpx, 90°回したか), 全部入ったか"""
    rects = []
    for i, (w, h) in enumerate(dims):
        wp, hp = max(1, math.ceil(w * density)), max(1, math.ceil(h * density))
        rot = hp > wp   # 横長に揃える
        if rot:
            wp, hp = hp, wp
        rects.append((hp + 2 * PAD, wp + 2 * PAD, wp, hp, rot, i))
    rects.sort(reverse=True)
    placed = [None] * len(dims)
    x, y, shelf_h = 4, 0, 4   # 左下の 4px 四方は「使わない面」用に空けておく
    for H, W, wp, hp, rot, i in rects:
        if x + W > size:
            x, y, shelf_h = 0, y + shelf_h, 0
        if W > size or y + H > size:
            return placed, False
        placed[i] = (x, y, wp, hp, rot)
        x += W
        shelf_h = max(shelf_h, H)
    return placed, True


def use_gpu(scene):
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind
        except TypeError:
            continue
        prefs.get_devices()
        gpus = [d for d in prefs.devices if d.type == kind]
        if gpus:
            for d in prefs.devices:
                d.use = d.type == kind
            scene.cycles.device = 'GPU'
            print("BAKE DEVICE:", kind, [d.name for d in gpus])
            return
    print("BAKE DEVICE: CPU")


def denoise(img):
    """焼いた画像のざらつきを OIDN (コンポジターの Denoise ノード) で取り、画素を numpy (N, 4) で返す。

    コンポジターは描画のついでにしか動かないので、Workbench で空描画して結果を EXR に書き出して読む。
    """
    scene = bpy.context.scene
    size = img.size[0]
    ng = bpy.data.node_groups.new("lightmap_denoise", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    src = ng.nodes.new("CompositorNodeImage")
    src.image = img
    dn = ng.nodes.new("CompositorNodeDenoise")
    dn.inputs["HDR"].default_value = True
    out = ng.nodes.new("NodeGroupOutput")
    ng.links.new(src.outputs["Image"], dn.inputs["Image"])
    ng.links.new(dn.outputs["Image"], out.inputs[0])
    scene.compositing_node_group = ng
    scene.render.use_compositing = True

    engine = scene.render.engine
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'OPEN_EXR'
    scene.render.image_settings.color_depth = '32'
    cam = bpy.data.objects.new("denoise_cam", bpy.data.cameras.new("denoise_cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    bpy.ops.render.render()
    path = os.path.join(ROOT, "models", "_lightmap_denoised.exr")
    bpy.data.images["Render Result"].save_render(path)
    result = bpy.data.images.load(path)
    px = np.empty(size * size * 4, np.float32)
    result.pixels.foreach_get(px)

    bpy.data.images.remove(result)
    os.remove(path)
    bpy.data.objects.remove(cam)
    scene.compositing_node_group = None
    scene.render.engine = engine
    return px.reshape(-1, 4)


def _encode(px, percentile):
    """焼いた値 (N, 3) を K で割って 8bit sRGB に符号化する。K は明るい方から (100 - percentile)% の値 (それより明るい所は白飛び)"""
    peak = px.max(axis=1)
    k = float(np.percentile(peak[peak > 0], percentile)) if np.any(peak > 0) else 1.0
    x = np.clip(px / k, 0, 1)
    enc = np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)
    enc += (np.random.default_rng(0).random(enc.shape, np.float32) - 0.5) / 255   # 8bit の段差 (縞) を散らす
    return np.clip(enc, 0, 1), k


def _save(rgb, size, filename, quality=92):
    out = bpy.data.images.new(filename, size, size, alpha=False)
    out.colorspace_settings.name = 'Non-Color'   # 値を変換せずにそのまま書く (符号化は済ませてある)
    px = np.ones((size * size, 4), np.float32)
    px[:, :3] = rgb
    out.pixels.foreach_set(px.ravel())
    out.filepath_raw = os.path.join(ROOT, "models", filename)
    out.file_format = 'WEBP'
    bpy.context.scene.render.image_settings.file_format = 'WEBP'
    bpy.context.scene.render.image_settings.quality = quality
    try:
        out.save(quality=quality)
    except TypeError:   # quality を受け取らない版では、シーンの設定 (上) が使われる
        out.save()
    print(f"SAVED {filename}: {os.path.getsize(out.filepath_raw) / 1e6:.1f} MB")


def bake_lightmap(size=4096, samples=256, gloss_samples=None):
    """拡散光 (lightmap) とツヤ (glossmap) を焼いて models/ に保存し、K を scene のカスタムプロパティに入れる。"""
    scene = bpy.context.scene
    objs = bake_targets()
    add_lightmap_uvs(objs, size)

    diffuse = bpy.data.images.new("room_lightmap_bake", size, size, alpha=False, float_buffer=True)
    gloss = bpy.data.images.new("room_glossmap_bake", size, size, alpha=False, float_buffer=True)
    tex_nodes = []
    for mat in {s.material for o in objs for s in o.material_slots if s.material}:
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        uv = nodes.new("ShaderNodeUVMap")
        uv.uv_map = "lightmap"
        tex = nodes.new("ShaderNodeTexImage")
        links.new(uv.outputs["UV"], tex.inputs["Vector"])
        nodes.active = tex   # 焼き先 = 選択中の画像ノード
        tex_nodes.append(tex)

    scene.render.engine = 'CYCLES'
    use_gpu(scene)
    scene.cycles.use_denoising = False
    scene.cycles.sample_clamp_indirect = 3.0   # 細い枠などに出る明るい点 (跳ね返り光の外れ値) を抑える
    scene.render.bake.margin = PAD
    scene.render.bake.margin_type = 'EXTEND'
    # ツヤは目の位置から見た向きで焼く (カメラの位置だけが効く。向きは関係ない)
    cam = bpy.data.objects.new("bake_eye", bpy.data.cameras.new("bake_eye"))
    cam.location = VIEW["eye"]
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.render.bake.view_from = 'ACTIVE_CAMERA'

    # 物体ごとに焼くと、そのたびにシーン全体を準備し直して遅い (23個で数分)。
    # 全メッシュの複製を1つにまとめた物を焼き、その間は元の物を隠す (重なった面が互いに影を落とさないように)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.duplicate()
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.join()
    proxy = bpy.context.view_layer.objects.active
    proxy.data.uv_layers.active = proxy.data.uv_layers["lightmap"]   # 焼き先はアクティブな UV (画像ノードの UV ではない)
    skipped = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.get("bake_skip")]
    for obj in objs + skipped:
        obj.hide_render = True

    def bake(img, kind, filters, n):
        for tex in tex_nodes:
            tex.image = img
        scene.cycles.samples = n
        scene.render.bake.use_pass_direct = 'DIRECT' in filters
        scene.render.bake.use_pass_indirect = 'INDIRECT' in filters
        scene.render.bake.use_pass_color = 'COLOR' in filters
        t0 = time.time()
        bpy.ops.object.bake(type=kind, pass_filter=filters, use_clear=True)
        print(f"BAKE {kind}: {time.time() - t0:.0f}s ({n} samples, {size}px)")

    bake(diffuse, 'DIFFUSE', {'DIRECT', 'INDIRECT'}, samples)        # 材質の色は焼かない (Web 側で掛ける)
    bake(gloss, 'GLOSSY', {'DIRECT', 'INDIRECT', 'COLOR'}, gloss_samples or samples)   # 反射は色ごと焼く (そのまま足す)
    bpy.data.objects.remove(proxy)
    bpy.data.objects.remove(cam)
    for obj in objs + skipped:
        obj.hide_render = False

    t0 = time.time()
    rgb, k = _encode(denoise(diffuse)[:, :3], 99.7)   # 天井灯のすぐ横などは白飛びさせる
    _save(rgb, size, LIGHTMAP_FILE)
    rgb, kg = _encode(denoise(gloss)[:, :3], 99.9)    # 照明の映り込みのいちばん明るい所だけ白飛びさせる
    _save(rgb, size, GLOSSMAP_FILE)
    print(f"DENOISE + SAVE: {time.time() - t0:.0f}s")
    scene["lightmap_intensity"], scene["lightmap_file"] = k, LIGHTMAP_FILE
    scene["glossmap_intensity"], scene["glossmap_file"] = kg, GLOSSMAP_FILE
    scene["eye"], scene["home_target"] = list(VIEW["eye"]), list(VIEW["target"])
    print(f"BAKED: K={k:.4f} (lightmap)  K={kg:.4f} (glossmap)")
    return k
