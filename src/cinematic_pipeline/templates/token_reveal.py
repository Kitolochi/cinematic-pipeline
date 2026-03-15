"""Token / Logo 3D Reveal template.

3D text or logo floating in space with slow rotation, god rays behind,
particle aura, and camera slow push-in. Classic crypto reveal shot.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cinematic_pipeline.core.scene import Scene
from cinematic_pipeline.core.objects import Mesh, PrimitiveType, Empty
from cinematic_pipeline.core.camera import Camera, CameraPreset
from cinematic_pipeline.core.light import Light, LightType, three_point_rig
from cinematic_pipeline.core.material import Material
from cinematic_pipeline.core.animation import Keyframe
from cinematic_pipeline.vfx.particles import ambient_dust, holographic_dust
from cinematic_pipeline.vfx.volumetrics import VolumetricFog, GodRays
from cinematic_pipeline.vfx.compositing import cinematic_post, sci_fi_glow


@dataclass
class TokenRevealConfig:
    """Configuration for the token reveal shot."""

    # Content
    token_text: str = "TOKEN"
    token_size: float = 1.0
    token_depth: float = 0.3  # Extrusion depth

    # Materials
    token_color: tuple[float, float, float] = (0.9, 0.75, 0.3)  # Gold
    token_metallic: float = 0.95
    token_roughness: float = 0.15
    token_emission: float = 0.5

    # Animation
    rotation_speed: float = 45.0  # Degrees per duration
    camera_push_distance: float = 1.5

    # VFX
    god_rays: bool = True
    god_ray_energy: float = 800
    particles: bool = True
    particle_style: str = "holographic"  # "holographic" or "dust"
    fog_density: float = 0.01
    post_preset: str = "cinematic"  # "cinematic" or "sci_fi"

    # Scene
    duration_seconds: float = 5.0
    fps: int = 30
    render_engine: str = "CYCLES"
    render_samples: int = 128


def token_reveal(config: TokenRevealConfig | None = None) -> Scene:
    """Build a complete token reveal scene.

    Returns a Scene ready to render. For 3D text, use Blender MCP
    to convert text to mesh before rendering.
    """
    cfg = config or TokenRevealConfig()
    frame_end = int(cfg.duration_seconds * cfg.fps)

    scene = Scene(
        name="Token_Reveal",
        fps=cfg.fps,
        frame_start=1,
        frame_end=frame_end,
        render_engine=cfg.render_engine,
        render_samples=cfg.render_samples,
        world_color=(0.003, 0.003, 0.008),
    )

    # --- Token material ---
    tr, tg, tb = cfg.token_color
    token_mat = Material(
        name="Token_Material",
        base_color=(tr, tg, tb, 1.0),
        metallic=cfg.token_metallic,
        roughness=cfg.token_roughness,
        emission_color=(tr, tg, tb),
        emission_strength=cfg.token_emission,
    )

    # --- Token placeholder (sphere as stand-in; MCP replaces with 3D text) ---
    scene.add(Mesh(
        name="Token",
        primitive=PrimitiveType.TORUS,
        size=cfg.token_size,
        location=(0, 0, 0),
        material_name="Token_Material",
        keyframes=[
            Keyframe(frame=1, property="rotation_euler", value=(0, 0, 0)),
            Keyframe(frame=frame_end, property="rotation_euler",
                     value=(0, cfg.rotation_speed, 0)),
        ],
    ))

    # --- Reflective floor ---
    floor_mat = Material(
        name="Floor",
        base_color=(0.01, 0.01, 0.015, 1.0),
        metallic=0.9,
        roughness=0.05,
    )
    scene.add(Mesh(
        name="Floor",
        primitive=PrimitiveType.PLANE,
        size=30.0,
        location=(0, 0, -1.5),
        material_name="Floor",
    ))

    # --- Camera: slow dolly in ---
    scene.add(Camera(
        name="Main_Camera",
        location=(0, -6, 0.5),
        focal_length=65,
        dof_enabled=True,
        dof_focus_target="Token",
        dof_aperture=2.0,
        preset=CameraPreset.DOLLY_IN,
        preset_params={"distance": cfg.camera_push_distance},
        track_target="Token",
    ))

    # --- Lighting ---
    # Key light from above-right
    scene.add(Light(
        name="Key_Light",
        light_type=LightType.AREA,
        location=(3, -2, 4),
        rotation=(55, 0, 45),
        energy=400,
        size=1.5,
    ))

    # Rim light from behind
    scene.add(Light(
        name="Rim_Light",
        light_type=LightType.AREA,
        location=(-2, 3, 2),
        rotation=(20, 0, 200),
        energy=250,
        color=cfg.token_color,
        size=0.8,
    ))

    # Fill light (subtle)
    scene.add(Light(
        name="Fill_Light",
        light_type=LightType.AREA,
        location=(-3, -1, 1),
        rotation=(20, 0, -30),
        energy=80,
        size=2.0,
    ))

    return scene


def token_reveal_vfx(config: TokenRevealConfig | None = None) -> dict:
    """Get VFX components for the token reveal.

    Returns dict with keys: materials, volumetrics, particles, post.
    Each value is a list of objects with to_blender_script() methods.
    """
    cfg = config or TokenRevealConfig()
    tr, tg, tb = cfg.token_color

    result = {
        "materials": [
            Material(
                name="Token_Material",
                base_color=(tr, tg, tb, 1.0),
                metallic=cfg.token_metallic,
                roughness=cfg.token_roughness,
                emission_color=(tr, tg, tb),
                emission_strength=cfg.token_emission,
            ),
            Material(
                name="Floor",
                base_color=(0.01, 0.01, 0.015, 1.0),
                metallic=0.9,
                roughness=0.05,
            ),
        ],
        "volumetrics": [],
        "particles": [],
        "post": [],
    }

    if cfg.fog_density > 0:
        result["volumetrics"].append(
            VolumetricFog(density=cfg.fog_density, anisotropy=0.3)
        )

    if cfg.god_rays:
        result["volumetrics"].append(
            GodRays(
                light_location=(0, 5, 3),
                target_location=(0, 0, 0),
                energy=cfg.god_ray_energy,
                color=cfg.token_color,
            )
        )

    if cfg.particles:
        if cfg.particle_style == "holographic":
            result["particles"].append(holographic_dust(location=(0, 0, 0)))
        else:
            result["particles"].append(ambient_dust(location=(0, 0, 0)))

    if cfg.post_preset == "sci_fi":
        result["post"].append(sci_fi_glow())
    else:
        result["post"].append(cinematic_post())

    return result


def token_reveal_mcp_script(config: TokenRevealConfig | None = None) -> str:
    """Generate a Blender Python script for MCP execution.

    Creates 3D text (not just a placeholder torus) with proper
    extrusion, bevel, and metallic material.
    """
    cfg = config or TokenRevealConfig()
    tr, tg, tb = cfg.token_color

    return f"""
import bpy
import math

# --- 3D Text Token ---
bpy.ops.object.text_add(location=(0, 0, 0))
text_obj = bpy.context.active_object
text_obj.name = "Token_Text"
text_obj.data.body = {cfg.token_text!r}
text_obj.data.extrude = {cfg.token_depth}
text_obj.data.bevel_depth = 0.02
text_obj.data.bevel_resolution = 3
text_obj.data.align_x = 'CENTER'
text_obj.data.align_y = 'CENTER'

# Convert to mesh for proper rendering
bpy.ops.object.convert(target='MESH')

# Center origin
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
text_obj.location = (0, 0, 0)

# Scale to target size
dims = text_obj.dimensions
largest = max(dims)
if largest > 0:
    scale_factor = {cfg.token_size * 2} / largest
    text_obj.scale *= scale_factor
    bpy.ops.object.transform_apply(scale=True)

# Token material
mat = bpy.data.materials.new("Token_Material")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs['Base Color'].default_value = ({tr}, {tg}, {tb}, 1.0)
bsdf.inputs['Metallic'].default_value = {cfg.token_metallic}
bsdf.inputs['Roughness'].default_value = {cfg.token_roughness}
bsdf.inputs['Emission Color'].default_value = ({tr}, {tg}, {tb}, 1.0)
bsdf.inputs['Emission Strength'].default_value = {cfg.token_emission}
text_obj.data.materials.append(mat)

# Slow rotation
text_obj.rotation_euler = (0, 0, 0)
text_obj.keyframe_insert(data_path='rotation_euler', frame=1)
text_obj.rotation_euler = (0, math.radians({cfg.rotation_speed}), 0)
text_obj.keyframe_insert(data_path='rotation_euler', frame={int(cfg.duration_seconds * cfg.fps)})

# Smooth interpolation
_act = text_obj.animation_data.action
_cbag = _act.layers[0].strips[0].channelbags[0]
for fc in _cbag.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = 'BEZIER'
        kp.easing = 'EASE_IN_OUT'

print(f"Token text '{{text_obj.data.materials[0].name}}' created: {{text_obj.dimensions}}")
"""
