"""GLB の中身 (ノード名・三角形数・材質) を表示する。Web 側で名前によるクリック判定ができるかの確認用。

    python3 tools/inspect_glb.py [models/room.glb]
"""
import json
import os
import struct
import sys

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "room.glb")
with open(path, "rb") as f:
    magic, version, length = struct.unpack("<4sII", f.read(12))
    assert magic == b"glTF", "GLB ではありません"
    chunk_len, chunk_type = struct.unpack("<I4s", f.read(8))
    gltf = json.loads(f.read(chunk_len))

meshes, accessors = gltf.get("meshes", []), gltf["accessors"]


def tris(mesh):
    n = 0
    for prim in mesh["primitives"]:
        n += (accessors[prim["indices"]]["count"] if "indices" in prim else accessors[prim["attributes"]["POSITION"]]["count"]) // 3
    return n


nodes = gltf["nodes"]
total = 0
print(f"{os.path.basename(path)}  {os.path.getsize(path) / 1024:.1f} KB  nodes={len(nodes)} meshes={len(meshes)} materials={len(gltf.get('materials', []))}")


def walk(i, depth):
    global total
    node = nodes[i]
    info = ""
    if "mesh" in node:
        t = tris(meshes[node["mesh"]])
        total += t
        info = f"  [{t} tris]"
    print("  " * depth + "- " + node.get("name", f"node{i}") + info)
    for c in node.get("children", []):
        walk(c, depth + 1)


children = {c for n in nodes for c in n.get("children", [])}
for i in range(len(nodes)):
    if i not in children:
        walk(i, 0)
print(f"合計 {total} tris")
for m in gltf.get("materials", []):
    if m.get("alphaMode", "OPAQUE") != "OPAQUE":
        print(f"半透明: {m['name']} alphaMode={m['alphaMode']}")
