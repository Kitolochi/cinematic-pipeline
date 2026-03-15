"""Quick single-frame test render — verifies pipeline end-to-end."""
import bpy
import math
import os

# Clear
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Scene settings
scene = bpy.context.scene
scene.render.fps = 30
scene.frame_start = 1
scene.frame_end = 1
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

# Use Eevee for speed
scene.render.engine = 'BLENDER_EEVEE'

# Dark world
world = bpy.data.worlds.get('World') or bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
bg.inputs['Color'].default_value = (0.005, 0.005, 0.01, 1.0)

# Material — dark metallic
mat = bpy.data.materials.new('Metallic_Dark')
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value = (0.02, 0.02, 0.03, 1.0)
bsdf.inputs['Metallic'].default_value = 0.9
bsdf.inputs['Roughness'].default_value = 0.2

# Floor
bpy.ops.mesh.primitive_plane_add(size=20.0)
floor = bpy.context.active_object
floor.name = 'Floor'
floor.location = (0, 0, -1)
floor_mat = bpy.data.materials.new('Floor')
floor_mat.use_nodes = True
floor_bsdf = floor_mat.node_tree.nodes.get('Principled BSDF')
floor_bsdf.inputs['Base Color'].default_value = (0.05, 0.05, 0.06, 1.0)
floor_bsdf.inputs['Roughness'].default_value = 0.9
floor.data.materials.append(floor_mat)

# Hero cube
bpy.ops.mesh.primitive_cube_add(size=1.5)
cube = bpy.context.active_object
cube.name = 'Hero_Cube'
cube.rotation_euler = (math.radians(15), math.radians(15), math.radians(30))
cube.data.materials.append(mat)

# Camera
cam_data = bpy.data.cameras.new('Camera')
cam_data.lens = 50
cam_data.dof.use_dof = True
cam_data.dof.focus_object = cube
cam_data.dof.aperture_fstop = 2.8
cam_obj = bpy.data.objects.new('Camera', cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (4, -4, 3)
track = cam_obj.constraints.new(type='TRACK_TO')
track.target = cube
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'
scene.camera = cam_obj

# Key light
key_data = bpy.data.lights.new('Key_Light', type='AREA')
key_data.energy = 200
key_data.color = (1.0, 0.95, 0.9)
key_data.shadow_soft_size = 1.0
key_obj = bpy.data.objects.new('Key_Light', key_data)
bpy.context.collection.objects.link(key_obj)
key_obj.location = (3, -3, 4)
key_obj.rotation_euler = (math.radians(55), 0, math.radians(45))

# Rim light
rim_data = bpy.data.lights.new('Rim_Light', type='AREA')
rim_data.energy = 120
rim_data.color = (0.8, 0.9, 1.0)
rim_data.shadow_soft_size = 0.5
rim_obj = bpy.data.objects.new('Rim_Light', rim_data)
bpy.context.collection.objects.link(rim_obj)
rim_obj.location = (-1, 3, 3)
rim_obj.rotation_euler = (math.radians(30), 0, math.radians(180))

# Render
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output', 'quick_test')
os.makedirs(output_path, exist_ok=True)
scene.render.filepath = os.path.join(output_path, 'test_frame')
scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
print(f"\nRendered to: {scene.render.filepath}.png")
print("SUCCESS — Pipeline works!")
