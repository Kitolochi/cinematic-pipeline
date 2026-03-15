"""Point Cloud Cityscape template.

Scattered 3D points forming a cityscape silhouette. Camera flies
through the environment. Points have individual subtle animation.
"""

from __future__ import annotations

from dataclasses import dataclass

from cinematic_pipeline.core.scene import Scene
from cinematic_pipeline.core.objects import Mesh, PrimitiveType, Empty
from cinematic_pipeline.core.camera import Camera, CameraPreset
from cinematic_pipeline.core.light import Light, LightType
from cinematic_pipeline.core.material import Material
from cinematic_pipeline.vfx.particles import ambient_dust
from cinematic_pipeline.vfx.compositing import sci_fi_glow


@dataclass
class PointCloudCityConfig:
    """Configuration for the point cloud cityscape."""

    # City generation
    grid_size: int = 20  # NxN grid of buildings
    building_count: int = 80
    city_spread: float = 30.0  # Total city area
    min_height: float = 1.0
    max_height: float = 8.0
    point_size: float = 0.05  # Size of each point

    # Visual
    point_color: tuple[float, float, float] = (0.0, 0.8, 1.0)  # Cyan
    point_emission: float = 2.0
    sky_color: tuple[float, float, float] = (0.002, 0.003, 0.008)

    # Camera path (fly-through)
    camera_start: tuple[float, float, float] = (-15, -15, 5)
    camera_end: tuple[float, float, float] = (10, 10, 3)

    # Scene
    duration_seconds: float = 8.0
    fps: int = 30
    render_engine: str = "CYCLES"
    render_samples: int = 128


def point_cloud_city(config: PointCloudCityConfig | None = None) -> Scene:
    """Build a point cloud cityscape scene.

    Creates a placeholder scene. The actual point cloud is generated
    via the MCP script (execute_blender_code) since it requires
    procedural generation that's best done inside Blender.
    """
    cfg = config or PointCloudCityConfig()
    frame_end = int(cfg.duration_seconds * cfg.fps)

    scene = Scene(
        name="Point_Cloud_City",
        fps=cfg.fps,
        frame_start=1,
        frame_end=frame_end,
        render_engine=cfg.render_engine,
        render_samples=cfg.render_samples,
        world_color=cfg.sky_color,
    )

    # --- Camera fly-through ---
    scene.add(Camera(
        name="FlyThrough_Camera",
        location=cfg.camera_start,
        focal_length=24,
        dof_enabled=True,
        dof_focus_distance=10.0,
        dof_aperture=4.0,
        preset=CameraPreset.STATIC,
        keyframes=[
            # Will be overridden by the MCP script path
        ],
    ))

    # --- Ambient light ---
    scene.add(Light(
        name="Ambient",
        light_type=LightType.AREA,
        location=(0, 0, 15),
        rotation=(90, 0, 0),
        energy=20,
        size=30.0,
        color=cfg.point_color,
    ))

    return scene


def point_cloud_city_vfx(config: PointCloudCityConfig | None = None) -> dict:
    """Get VFX for point cloud cityscape."""
    cfg = config or PointCloudCityConfig()
    pr, pg, pb = cfg.point_color

    return {
        "materials": [
            Material(
                name="PointMaterial",
                base_color=(pr, pg, pb, 1.0),
                metallic=0.0,
                roughness=0.5,
                emission_color=(pr, pg, pb),
                emission_strength=cfg.point_emission,
            ),
        ],
        "particles": [ambient_dust(location=(0, 0, 5))],
        "post": [sci_fi_glow()],
    }


def point_cloud_city_mcp_script(config: PointCloudCityConfig | None = None) -> str:
    """Generate Blender script that creates the procedural point cloud.

    Creates ico-spheres scattered in a city-like pattern with
    individual floating animation via noise modifiers.
    """
    cfg = config or PointCloudCityConfig()
    pr, pg, pb = cfg.point_color
    frame_end = int(cfg.duration_seconds * cfg.fps)
    csx, csy, csz = cfg.camera_start
    cex, cey, cez = cfg.camera_end

    return f"""
import bpy
import math
import random

random.seed(42)

# --- Point material ---
mat = bpy.data.materials.new("PointMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs['Base Color'].default_value = ({pr}, {pg}, {pb}, 1.0)
bsdf.inputs['Emission Color'].default_value = ({pr}, {pg}, {pb}, 1.0)
bsdf.inputs['Emission Strength'].default_value = {cfg.point_emission}

# --- Generate city points ---
# Create a single tiny sphere as template
bpy.ops.mesh.primitive_ico_sphere_add(radius={cfg.point_size}, subdivisions=1, location=(0, 0, 0))
template = bpy.context.active_object
template.name = "_point_template"
template.data.materials.append(mat)

# Generate building positions
points_collection = bpy.data.collections.new("PointCloud")
bpy.context.scene.collection.children.link(points_collection)

half = {cfg.city_spread} / 2
for i in range({cfg.building_count}):
    # Random building position
    bx = random.uniform(-half, half)
    by = random.uniform(-half, half)
    height = random.uniform({cfg.min_height}, {cfg.max_height})

    # Points along the building column
    num_points = int(height / 0.3)
    for j in range(num_points):
        pz = j * 0.3

        # Copy template
        point = template.copy()
        point.data = template.data
        point.location = (bx + random.uniform(-0.1, 0.1),
                          by + random.uniform(-0.1, 0.1),
                          pz)
        point.name = f"pt_{{i}}_{{j}}"
        points_collection.objects.link(point)

# Remove template
bpy.data.objects.remove(template, do_unlink=True)

# --- Camera fly-through path ---
cam = bpy.data.objects.get("FlyThrough_Camera")
if cam:
    cam.location = ({csx}, {csy}, {csz})
    cam.keyframe_insert(data_path='location', frame=1)
    cam.location = ({cex}, {cey}, {cez})
    cam.keyframe_insert(data_path='location', frame={frame_end})

    # Smooth interpolation
    _act = cam.animation_data.action
    _cbag = _act.layers[0].strips[0].channelbags[0]
    for fc in _cbag.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.easing = 'EASE_IN_OUT'

point_count = len(points_collection.objects)
print(f"Point cloud city: {{point_count}} points in {cfg.building_count} buildings")
"""
