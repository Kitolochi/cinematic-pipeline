"""Fighter Jet Flyby template.

Jet model flies through frame with afterburner particle trail,
camera tracks alongside with dynamic lag. Volumetric atmosphere.
Requires a jet model (import via MCP from Sketchfab/Poly Haven).
"""

from __future__ import annotations

from dataclasses import dataclass

from cinematic_pipeline.core.scene import Scene
from cinematic_pipeline.core.objects import Mesh, PrimitiveType, Empty
from cinematic_pipeline.core.camera import Camera, CameraPreset
from cinematic_pipeline.core.light import Light, LightType
from cinematic_pipeline.core.material import Material
from cinematic_pipeline.core.animation import Keyframe
from cinematic_pipeline.vfx.particles import particle_trail, sparks
from cinematic_pipeline.vfx.volumetrics import VolumetricFog
from cinematic_pipeline.vfx.compositing import cinematic_post


@dataclass
class FighterJetConfig:
    """Configuration for the fighter jet flyby shot."""

    # Flight path
    start_location: tuple[float, float, float] = (-15, 5, 3)
    end_location: tuple[float, float, float] = (15, -3, 4)
    start_rotation: tuple[float, float, float] = (0, 0, -10)  # Slight bank
    end_rotation: tuple[float, float, float] = (5, 0, 15)  # Roll into turn

    # Model (placeholder -- replace with imported model via MCP)
    model_name: str = "Fighter_Jet"
    model_size: float = 3.0

    # Afterburner
    afterburner_particles: bool = True
    afterburner_color: tuple[float, float, float] = (1.0, 0.5, 0.1)  # Orange
    afterburner_energy: float = 500

    # Atmosphere
    fog_density: float = 0.005
    sky_color: tuple[float, float, float] = (0.02, 0.03, 0.06)

    # Scene
    duration_seconds: float = 5.0
    fps: int = 30
    render_engine: str = "CYCLES"
    render_samples: int = 128


def fighter_jet_flyby(config: FighterJetConfig | None = None) -> Scene:
    """Build a fighter jet flyby scene.

    Uses a cone as placeholder for the jet. Replace with a real model
    via MCP (search_sketchfab_models('fighter jet')).
    """
    cfg = config or FighterJetConfig()
    frame_end = int(cfg.duration_seconds * cfg.fps)

    scene = Scene(
        name="Fighter_Jet_Flyby",
        fps=cfg.fps,
        frame_start=1,
        frame_end=frame_end,
        render_engine=cfg.render_engine,
        render_samples=cfg.render_samples,
        world_color=cfg.sky_color,
    )

    # --- Jet placeholder (cone facing forward) ---
    sx, sy, sz = cfg.start_location
    ex, ey, ez = cfg.end_location
    srx, sry, srz = cfg.start_rotation
    erx, ery, erz = cfg.end_rotation

    scene.add(Mesh(
        name=cfg.model_name,
        primitive=PrimitiveType.CONE,
        size=cfg.model_size,
        location=cfg.start_location,
        material_name="JetBody",
        keyframes=[
            Keyframe(frame=1, property="location", value=cfg.start_location),
            Keyframe(frame=frame_end, property="location", value=cfg.end_location),
            Keyframe(frame=1, property="rotation_euler", value=cfg.start_rotation),
            Keyframe(frame=frame_end, property="rotation_euler", value=cfg.end_rotation),
        ],
    ))

    # --- Camera: tracking alongside with lag ---
    # Camera starts behind and to the side, follows with offset
    cam_sx = sx + 3
    cam_sy = sy - 6
    cam_sz = sz - 0.5
    cam_ex = ex - 5  # Doesn't quite catch up (lag)
    cam_ey = ey - 6
    cam_ez = ez + 0.5

    scene.add(Camera(
        name="Chase_Camera",
        location=(cam_sx, cam_sy, cam_sz),
        focal_length=35,
        dof_enabled=True,
        dof_focus_target=cfg.model_name,
        dof_aperture=5.6,
        preset=CameraPreset.STATIC,
        track_target=cfg.model_name,
        keyframes=[
            Keyframe(frame=1, property="location", value=(cam_sx, cam_sy, cam_sz)),
            Keyframe(frame=frame_end, property="location", value=(cam_ex, cam_ey, cam_ez)),
        ],
    ))

    # --- Lighting ---
    scene.add(Light(
        name="Sun",
        light_type=LightType.SUN,
        energy=5,
        rotation=(45, 0, 30),
    ))

    # Afterburner point light (follows jet)
    if cfg.afterburner_particles:
        scene.add(Light(
            name="Afterburner_Glow",
            light_type=LightType.POINT,
            location=cfg.start_location,
            energy=cfg.afterburner_energy,
            color=cfg.afterburner_color,
            keyframes=[
                Keyframe(frame=1, property="location", value=cfg.start_location),
                Keyframe(frame=frame_end, property="location", value=cfg.end_location),
            ],
        ))

    return scene


def fighter_jet_vfx(config: FighterJetConfig | None = None) -> dict:
    """Get VFX for the fighter jet flyby."""
    cfg = config or FighterJetConfig()
    ar, ag, ab = cfg.afterburner_color

    result = {
        "materials": [
            Material(
                name="JetBody",
                base_color=(0.15, 0.15, 0.17, 1.0),
                metallic=0.8,
                roughness=0.35,
            ),
        ],
        "volumetrics": [],
        "particles": [],
        "post": [cinematic_post()],
    }

    if cfg.fog_density > 0:
        result["volumetrics"].append(
            VolumetricFog(density=cfg.fog_density, anisotropy=0.5)
        )

    if cfg.afterburner_particles:
        result["particles"].append(
            particle_trail(
                start=cfg.start_location,
            )
        )

    return result


def fighter_jet_mcp_instructions() -> str:
    """Instructions for replacing placeholder with real jet model."""
    return """
To replace the cone placeholder with a real fighter jet:

1. Search for a model:
   search_sketchfab_models("fighter jet", downloadable=True)

2. Preview candidates:
   get_sketchfab_model_preview(uid="...")

3. Download and import:
   download_sketchfab_model(uid="...", target_size=3.0)

4. Delete the placeholder cone:
   execute_blender_code("bpy.data.objects.remove(bpy.data.objects['Fighter_Jet'])")

5. Rename imported model:
   execute_blender_code("bpy.context.active_object.name = 'Fighter_Jet'")

The animation keyframes will automatically apply to the renamed object.
"""
