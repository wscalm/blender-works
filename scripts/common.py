"""全モデリングスクリプト共通のヘルパー (Blender 5.2 の bpy 用)。

使い方 (scripts/xxx.py の先頭で):
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from common import *
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Vector

ROOT = os.environ.get("WORKSPACE_WIN", os.getcwd())
TEXTURES = os.path.join(ROOT, "textures")   # テクスチャ画像 (Poly Haven の CC0 素材など)

DARK_BROWN = "#4A3226"   # カーテンと巾木に共通のダークブラウン


def reset_scene():
    """空のシーンから始める。"""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def hex_color(code):
    """'#RRGGBB' (sRGB) を Blender が使うリニア RGB に変換する。"""
    code = code.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(code[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def make_material(name, color, roughness=0.85, metallic=0.0, alpha=1.0, emission=0.0, emission_color=None,
                  texture=None, texture_size=1.0, specular=0.5, double_sided=False, emission_texture=False):
    """マテリアル。color は '#RRGGBB' かリニア RGB のタプル。alpha<1 で半透明 (ガラス用)。

    roughness と specular (0.5 = ふつうの塗装・樹脂・ニスの反射の強さ) はツヤの焼き付け (bake.py の glossmap) に効く。
    ツヤのある物 (床のニス・モニターの画面・ガラス・金属) は roughness を小さくする。
    emission>0 で自ら光る (照明のカバーや表示ランプ)。emission_color を省略すると color で光る。
    texture を渡すと textures/ の画像を UV `UVMap` (1 = 1m。add_box_uvs が作る) に貼る。画像1枚の実寸が texture_size (m)。
    このとき color は画像に掛ける色になる ('#FFFFFF' なら画像のまま。暗くしたいときに使う)。glb では baseColorFactor になる。
    double_sided: 裏からも見える1枚の面 (カーテンのヒダなど) だけ True。それ以外は裏面を描かない (glb の doubleSided)
    emission_texture: texture の画像そのものの色で光る (点いている画面)。glb では emissiveTexture になる
    """
    if isinstance(color, str):
        color = hex_color(color)
    if isinstance(emission_color, str):
        emission_color = hex_color(emission_color)
    mat = bpy.data.materials.new(name)   # (5.x では新しい材質は最初からノード付き)
    mat.use_backface_culling = not double_sided
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Specular IOR Level"].default_value = specular
    if emission > 0:
        bsdf.inputs["Emission Color"].default_value = (*(emission_color or color), 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission
    if texture:
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        uv = nodes.new("ShaderNodeUVMap")
        uv.uv_map = "UVMap"
        mapping = nodes.new("ShaderNodeMapping")   # glb では KHR_texture_transform になる
        mapping.inputs["Scale"].default_value = (1 / texture_size, 1 / texture_size, 1)
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(os.path.join(TEXTURES, texture), check_existing=True)
        mix = nodes.new("ShaderNodeMix")
        mix.data_type, mix.blend_type = 'RGBA', 'MULTIPLY'
        mix.inputs["Factor"].default_value = 1.0
        a, b = [i for i in mix.inputs if i.type == 'RGBA']
        b.default_value = (*color, 1.0)
        links.new(uv.outputs["UV"], mapping.inputs["Vector"])
        links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
        links.new(tex.outputs["Color"], a)
        links.new([o for o in mix.outputs if o.type == 'RGBA'][0], bsdf.inputs["Base Color"])
        if emission_texture:
            links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        mat.surface_render_method = 'BLENDED'
        mat.show_transparent_back = False
    return mat


# 木目の材質。textures/ の Poly Haven (CC0) の突板の画像と、その実寸 (m)、画像に掛ける色。
# 画像の木目は縦 (V) 方向に走る。add_box_uvs が V を板の長い方向に合わせるので、木目は板に沿う
# mean = 画像の平均の色 (sRGB)。wood_material の target で色を合わせるときに使う
WOOD = {
    "walnut": dict(texture="walnut_veneer_diff_1k.jpg", texture_size=1.8, color="#D0C2BA", mean=(138, 105, 81)),   # 生の突板を少し暗くした茶。もっと暗いと夜の照明でほぼ黒に見える
    "oak": dict(texture="oak_veneer_01_diff_1k.jpg", texture_size=1.83, color="#FFFFFF", mean=(161, 126, 87)),     # ナチュラルなオーク
    # 物件のドア・収納・巾木のはちみつ色の木目 (tools/make_textures.py がオークの突板から作る)
    "honey": dict(texture="oak_honey_1k.jpg", texture_size=1.83, color="#FFFFFF", mean=(203, 161, 106)),
    "light": dict(texture="oak_light_1k.jpg", texture_size=1.83, color="#FFFFFF", mean=(229, 198, 147)),   # 明るいナチュラルな木 (スツール)
    # 木目を薄くした版 (色は同じ)。木目がはっきり見えるのはテーブル・デスク・床 (とベッドの枠) だけにする (ユーザー指定)
    "honey_soft": dict(texture="oak_honey_soft_1k.jpg", texture_size=1.83, color="#FFFFFF", mean=(203, 161, 106)),
    "oak_soft": dict(texture="oak_soft_1k.jpg", texture_size=1.83, color="#FFFFFF", mean=(160, 125, 86)),
    "walnut_soft": dict(texture="walnut_soft_1k.jpg", texture_size=1.8, color="#D0C2BA", mean=(137, 104, 80)),
    "light_soft": dict(texture="oak_light_soft_1k.jpg", texture_size=1.83, color="#FFFFFF", mean=(229, 198, 147)),
}


def tint(mean, target):
    """平均の色が mean (sRGB) の画像に掛けて、平均を target (sRGB) にする色 (リニア RGB)。target は mean より暗いこと。
    色は (R, G, B) の 0〜255 か '#RRGGBB'"""
    lin = lambda c: hex_color(c if isinstance(c, str) else "#%02X%02X%02X" % tuple(c))
    return tuple(min(1.0, t / m) for t, m in zip(lin(target), lin(mean)))


def wood_material(name, kind, roughness=0.6, target=None, specular=0.5):
    """木目の材質。target (sRGB の平均の色) を渡すと、画像をその色まで暗くする"""
    w = dict(WOOD[kind])
    mean = w.pop("mean")
    if target:
        w["color"] = tint(mean, target)
    return make_material(name, roughness=roughness, specular=specular, **w)


# 布の材質。textures/ の白っぽい布の画像 (tools/make_textures.py の FABRICS。織り目に、部屋の距離で見える数 cm のむらと糸の筋を足した物) に色を掛ける。
# mean = 画像の平均の色 (sRGB)。texture_size = 画像1枚の実寸 (m)
FABRIC = {
    "cotton": dict(texture="cotton_light_1k.jpg", texture_size=0.53, mean=(241, 239, 234)),   # 綿 (シーツ・枕・マットレス・かごの布・シャツ)
    "canvas": dict(texture="canvas_light_1k.jpg", texture_size=0.54, mean=(237, 233, 223)),   # 帆布 (トートバッグ)
    "towel": dict(texture="towel_quilt_1k.jpg", texture_size=0.734, mean=(230, 230, 228)),   # タオル地にキルティングの縫い目 (敷きパッド)
}


def fabric_material(name, kind, color, roughness=1.0, specular=0.3, **kw):
    """布の材質。color (sRGB の平均の色) は画像の平均より暗いこと"""
    f = dict(FABRIC[kind])
    mean = f.pop("mean")
    return make_material(name, tint(mean, color), roughness=roughness, specular=specular, **f, **kw)


def add_box_uvs(objs, seed=0):
    """テクスチャ用の UV `UVMap` を作る。面の向きに合わせて、ローカル座標の2軸をそのまま UV にする (1 = 1m)。

    つながった部品 (直方体1つなど) ごとに、長い方の軸を V にする (木目が板の長い方向に沿う)。
    部品ごとに貼る位置をずらして、同じ模様が隣に並ばないようにする。家具の子メッシュは家具のローカル座標なので、家具を回しても木目は家具に付いて回る。
    """
    rng = random.Random(seed)
    for obj in objs:
        mesh = obj.data
        if "UVMap" in mesh.uv_layers:
            continue
        layer = mesh.uv_layers.new(name="UVMap")
        root = list(range(len(mesh.vertices)))   # 頂点を共有する面をまとめる (union-find)

        def find(i):
            while root[i] != i:
                root[i] = root[root[i]]
                i = root[i]
            return i
        for poly in mesh.polygons:
            for v in poly.vertices[1:]:
                root[find(v)] = find(poly.vertices[0])
        lo, hi = {}, {}
        for v in mesh.vertices:
            r = find(v.index)
            lo[r] = [min(a, b) for a, b in zip(lo.get(r, v.co), v.co)]
            hi[r] = [max(a, b) for a, b in zip(hi.get(r, v.co), v.co)]
        offset = {r: (rng.random() * 3, rng.random() * 3) for r in lo}

        for poly in mesh.polygons:
            n = max(range(3), key=lambda i: abs(poly.normal[i]))
            u, v = [i for i in range(3) if i != n]
            r = find(poly.vertices[0])
            if hi[r][u] - lo[r][u] > hi[r][v] - lo[r][v]:
                u, v = v, u
            du, dv = offset[r]
            for li in poly.loop_indices:
                co = mesh.vertices[mesh.loops[li].vertex_index].co
                layer.data[li].uv = (co[u] + du, co[v] + dv)


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


BEVEL = 0.004   # 家具の角の丸み (面取りの幅, m)。現実の物は角がわずかに丸く、そこに光が当たって形が見える


def boxes_object(name, boxes, parent=None, bevel=BEVEL, segments=2):
    """軸に平行な直方体の集まりを、1つのメッシュオブジェクトにして返す。

    boxes: [(x0, x1, y0, y1, z0, z1, material), ...]  (単位 m。min/max の順は問わない)
    材質ごとにスロットを作る。面は全てフラットシェード。
    bevel: 各直方体の12本の辺を面取りする幅 (薄い板は自動で細くする)。壁・床・天井など、箱どうしが継ぎ目なく続く物は 0 にする。
      8つ目の値を付けた直方体 (x0, ..., material, bevel) は、その箱だけ面取りの幅を変える (壁の中の巾木だけ面取りする、など)
    """
    solids = []
    for box in boxes:
        x0, x1, y0, y1, z0, z1, mat = box[:7]
        x0, x1 = sorted((x0, x1))
        y0, y1 = sorted((y0, y1))
        z0, z1 = sorted((z0, z1))
        solids.append(([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], mat, *box[7:]))
    return solids_object(name, solids, parent, bevel, segments)


def solids_object(name, solids, parent=None, bevel=BEVEL, segments=2):
    """6面体の集まりを、1つのメッシュオブジェクトにして返す。boxes_object の傾いた版 (傾いた背もたれのクッションなど)。

    solids: [(8点, material), ...]。8点は boxes_object の直方体と同じ並び:
      下の面 (x0,y0) (x1,y0) (x1,y1) (x0,y1) → 上の面 (同じ並び)。下の面と上の面は、上から見て同じ回り方にすること。
      3つ目の値 (8点, material, bevel) で、その6面体だけ面取りの幅を変えられる
    """
    verts, faces, face_mats, slots = [], [], [], []
    for pts, mat, *_ in solids:
        if mat not in slots:
            slots.append(mat)
        mi = slots.index(mat)
        v = len(verts)
        verts += pts
        # 下, 上, 南(-Y), 東(+X), 北(+Y), 西(-X) の順。法線は全て外向き
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                  (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            faces.append(tuple(v + i for i in f))
            face_mats.append(mi)

    obj = mesh_object(name, verts, faces, slots, face_mats, parent)
    widths = []
    for pts, _, *own in solids:
        ext = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
        widths.append(min(own[0] if own else bevel, 0.3 * min(ext)))
    if max(widths, default=0) > 0:
        _bevel_solids(obj.data, widths, segments)
    return obj


def _bevel_solids(mesh, widths, segments):
    """solids_object が作ったメッシュ (6面体が8頂点ずつ並ぶ) の、各6面体の辺を面取りする。細すぎる物 (0.8mm 未満) はそのまま"""
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    groups = [[bm.verts[8 * i + k] for k in range(8)] for i in range(len(widths))]
    for verts, w in zip(groups, widths):   # 先に頂点を集めておく (面取りすると番号がずれる)
        if w < 0.0008:
            continue
        edges = list({e for v in verts for e in v.link_edges})
        bmesh.ops.bevel(bm, geom=verts + edges, offset=w, offset_type='OFFSET', segments=segments, profile=0.5,
                        affect='EDGES', clamp_overlap=True)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def soft_boxes_object(name, items, parent=None, cuts=10, wrinkle=0.0, wrinkle_size=0.3, seed=0):
    """角の丸い、ふくらんだ箱 (クッション・枕・マットレス・エアコンの本体など) の集まりを1つのメッシュにする。なめらかに表示する。

    items: [(x0, x1, y0, y1, z0, z1, material, radius, bulge), ...]
      radius = 角の丸みの半径 (m)。bulge = (x, y, z) 各面の中央が外へふくらむ量 (m)。z だけ大きくすると座布団・枕の形
      10個目の値 lean を付けると、上へ行くほど +Y へずらす (上面で lean m。後ろへもたれる背クッション)
    箱の面を cuts x cuts の格子に分け、角に近いほど細かくして丸める。
    wrinkle > 0 で、表面を最大 wrinkle (m) だけ波打たせる (布団・布のしわ)。wrinkle_size = 波の長さ (m)。底面は動かさない。
      波の長さの 1/4 より格子が細かくなるよう cuts を増やすこと
    """
    bm = bmesh.new()
    slots = []
    rng = random.Random(seed)
    for x0, x1, y0, y1, z0, z1, mat, radius, bulge, *opt in items:
        lean = opt[0] if opt else 0.0
        k = 2 * math.pi / wrinkle_size
        waves = [(k * rng.uniform(0.6, 1.3), k * rng.uniform(0.6, 1.3), rng.uniform(0, 6.3), rng.uniform(-1, 1)) for _ in range(4)]
        if mat not in slots:
            slots.append(mat)
        mi = slots.index(mat)
        c = Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        h = Vector((abs(x1 - x0) / 2, abs(y1 - y0) / 2, abs(z1 - z0) / 2))
        r = min(radius, 0.98 * min(h))
        piece = bmesh.new()
        bmesh.ops.create_cube(piece, size=2.0)
        bmesh.ops.subdivide_edges(piece, edges=piece.edges[:], cuts=cuts - 1, use_grid_fill=True)
        q = 0.4   # 格子の線のうち、丸める範囲 (端から r) に割り当てる割合
        for v in piece.verts:
            p = Vector(v.co)
            for i in range(3):   # [-1, 1] の格子を、端の r の範囲に線が集まるように実寸へ写す
                a = min(abs(p[i]), 1.0)
                inner = h[i] - r
                p[i] = math.copysign(a / (1 - q) * inner if a < 1 - q else inner + (a - (1 - q)) / q * r, p[i])
            core = Vector([max(-(h[i] - r), min(h[i] - r, p[i])) for i in range(3)])
            d = p - core
            if d.length > 1e-9:   # 角のまわりは、内側の箱から半径 r の位置へ押し出す (= 丸い角)
                p = core + d.normalized() * r
            n = [min(1.0, abs(p[i]) / h[i]) for i in range(3)]
            for i in range(3):    # 面の中央をふくらませる (端では 0)
                j, k = [a for a in range(3) if a != i]
                p[i] += math.copysign(bulge[i] * n[i] ** 8 * (1 - n[j] ** 2) * (1 - n[k] ** 2), p[i])
            if wrinkle > 0 and p.z > -h.z + 0.01:   # しわ: 向きの違う波を足し、外向き (中心からの向き) に押す
                w = sum(math.sin(fx * (c.x + p.x) + s * fy * (c.y + p.y) + ph) for fx, fy, ph, s in waves) / 4
                p += p.normalized() * wrinkle * w * min(1.0, (p.z + h.z) / 0.05)
            p.y += lean * (p.z + h.z) / (2 * h.z)
            v.co = c + p
        for f in piece.faces:
            f.smooth = True
            f.material_index = mi
        mesh_tmp = bpy.data.meshes.new("_soft_tmp")
        piece.to_mesh(mesh_tmp)
        bm.from_mesh(mesh_tmp)
        bpy.data.meshes.remove(mesh_tmp)
        piece.free()
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for mat in slots:
        mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def mesh_object(name, verts, faces, materials, face_mats=None, parent=None):
    """頂点と面から1つのメッシュオブジェクトを作る (曲面やヒダなど、直方体で表せない形用)。

    faces は頂点番号のタプル。法線は反時計回りに見える側が表。face_mats は面ごとの materials の番号 (省略で全て 0)。
    """
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    for mat in materials:
        mesh.materials.append(mat)
    if face_mats is not None:
        for poly, mi in zip(mesh.polygons, face_mats):
            poly.material_index = mi
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


# 家具の「正面」はローカルの -Y 向き (Blender の標準)。回転 0 で南向き、Z 軸まわりに反時計回りに増える。
# 家具のローカル座標: 原点 = 足元の中心 / 正面 = -Y / X = 正面から見て右 / 背面 = +Y
from layout import FACING_DEG   # {"south": 0, "east": 90, "north": 180, "west": 270}


def add_empty(name, location=(0, 0, 0), rotation_z_deg=0.0):
    """家具の親になる Empty。Web 側のクリック判定は、この名前で行う。"""
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = 'PLAIN_AXES'
    obj.location = location
    obj.rotation_euler = (0, 0, math.radians(rotation_z_deg))
    bpy.context.scene.collection.objects.link(obj)
    return obj


def setup_world(color=(0.05, 0.05, 0.06), strength=1.0):
    """環境光。これがないと影側が真っ黒になる。"""
    world = bpy.data.worlds.new("World")
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*color, 1.0)
    bg.inputs["Strength"].default_value = strength
    bpy.context.scene.world = world


def setup_lights():
    """キーライト + フィルライトの3点照明風。"""
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 8))
    key = bpy.context.object
    key.data.energy = 3.0
    key.rotation_euler = (math.radians(50), 0, math.radians(35))
    bpy.ops.object.light_add(type='AREA', location=(-5, -3, 4))
    fill = bpy.context.object
    fill.data.energy = 150
    fill.data.size = 4
    fill.rotation_euler = (math.radians(65), 0, math.radians(-55))


def look_at(obj, target):
    direction = Vector(target) - obj.location
    if direction.xy.length < 1e-6:
        # 真上/真下を向く場合は up 軸が定まらないので、東=右・北=上になる向きに固定する
        obj.rotation_euler = (0, 0, 0) if direction.z < 0 else (math.pi, 0, 0)
    else:
        obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def setup_camera(location=(6, -6, 4), target=(0, 0, 1), lens=50):
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.object
    cam.data.lens = lens
    look_at(cam, target)
    bpy.context.scene.camera = cam
    return cam


def add_floor(size=20, color=(0.6, 0.6, 0.6)):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = "Floor"
    assign(floor, make_material("Floor", color, roughness=0.9))
    return floor


def render(filename, width=800, height=600, samples=64):
    """renders/<filename> へ PNG を書き出す。"""
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = samples
    scene.view_settings.view_transform = 'Standard'   # 指定した色のまま出す (Filmic だと褪せる)
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.filepath = os.path.join(ROOT, "renders", filename)
    bpy.ops.render.render(write_still=True)
    print("RENDERED:", scene.render.filepath)


def render_view(filename, location, target, lens=35, ortho_scale=None, hide=(),
                width=1000, height=750):
    """カメラを一時的に置いて1枚レンダリングする。hide のオブジェクトはその間だけ非表示。"""
    hidden = [o for n in hide if n in bpy.data.objects
              for o in (bpy.data.objects[n], *bpy.data.objects[n].children_recursive)]
    for obj in hidden:   # 家具は親 Empty の名前で、子のパーツごと隠す
        obj.hide_render = True

    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.object
    cam.data.clip_start = 0.05
    if ortho_scale:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = ortho_scale
    else:
        cam.data.lens = lens
    look_at(cam, target)
    bpy.context.scene.camera = cam
    render(filename, width, height)

    bpy.data.objects.remove(cam)
    for obj in hidden:
        obj.hide_render = False


def save_blend(filename):
    """models/<filename> へ .blend を保存。"""
    path = os.path.join(ROOT, "models", filename)
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("SAVED:", path)


def export_glb(filename):
    """models/<filename> へ glTF バイナリを書き出し。

    メッシュと Empty だけを出す。プレビュー用のライト・カメラは Web 側には不要なので除外する。
    シーンのカスタムプロパティ (ライトマップの明るさ lightmap_intensity など) は extras として出る (three.js では gltf.scene.userData)。
    """
    path = os.path.join(ROOT, "models", filename)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type in {'MESH', 'EMPTY'}:
            obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_extras=True)
    print("EXPORTED:", path)
