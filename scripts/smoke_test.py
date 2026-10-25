import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

reset_scene()
setup_world()
setup_lights()
add_floor()

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
assign(bpy.context.object, make_material("Red", (0.8, 0.1, 0.1), roughness=0.4))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=(2.5, 1, 0.8))
bpy.ops.object.shade_smooth()
assign(bpy.context.object, make_material("Gold", (1.0, 0.7, 0.2), roughness=0.25, metallic=1.0))

setup_camera(location=(7, -7, 5), target=(1, 0, 0.8))
render("smoke_test.png")
save_blend("smoke_test.blend")
export_glb("smoke_test.glb")
