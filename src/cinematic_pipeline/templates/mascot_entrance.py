"""Mascot / Character Entrance template.

3D character emerges from particle cloud with dramatic rim lighting.
Camera orbits around character with depth of field.
Requires a character model (import via MCP from Sketchfab).
"""

from __future__ import annotations

from dataclasses import dataclass

from cinematic_pipeline.core.scene import Scene
from cinematic_pipeline.core.objects import Mesh, PrimitiveType, Empty
from cinematic_pipeline.core.camera import Camera, CameraPreset
from cinematic_pipeline.core.light import Light, LightType
from cinematic_pipeline.core.material import Material
from cinematic_pipeline.core.animation import Keyframe
from cinematic_pipeline.vfx.particles import explosion_burst, ambient_dust
from cinematic_pipeline.vfx.volumetrics import VolumetricFog, VolumetricSpotlight
from cinematic_pipeline.vfx.compositing import cinematic_post


@dataclass
class MascotEntranceConfig:
    """Configuration for the mascot entrance shot."""

    # Character
    character_name: str = "Mascot"
    character_size: float = 1.7  # Target height in meters
    entrance_frame: int = 15  # Frame when character becomes visible
    rise_distance: float = 1.5  # How far character rises

    # Camera
    orbit_radius: float = 5.0
    orbit_height: float = 1.5
    orbit_revolutions: float = 0.25  # Quarter orbit

    # Lighting
    rim_color: tuple[float, float, float] = (0.3, 0.5, 1.0)  # Blue rim
    rim_energy: float = 500
    key_energy: float = 300

    # VFX
    entrance_burst: bool = True
    burst_frame: int = 10
    fog_density: float = 0.015
    spotlight: bool = True
    spotlight_energy: float = 800

    # Scene
    duration_seconds: float = 5.0
    fps: int = 30
    render_engine: str = "CYCLES"
    render_samples: int = 128


def mascot_entrance(config: MascotEntranceConfig | None = None) -> Scene:
    """Build a mascot entrance scene.

    Uses Suzanne (monkey) as placeholder. Replace with real model
    via MCP (search_sketchfab_models).
    """
    cfg = config or MascotEntranceConfig()
    frame_end = int(cfg.duration_seconds * cfg.fps)

    scene = Scene(
        name="Mascot_Entrance",
        fps=cfg.fps,
        frame_start=1,
        frame_end=frame_end,
        render_engine=cfg.render_engine,
        render_samples=cfg.render_samples,
        world_color=(0.003, 0.003, 0.008),
    )

    # --- Character placeholder (Suzanne) with rise animation ---
    rise_start_z = -cfg.rise_distance
    rise_end_z = 0.0

    scene.add(Mesh(
        name=cfg.character_name,
        primitive=PrimitiveType.MONKEY,
        size=cfg.character_size,
        location=(0, 0, rise_start_z),
        material_name="CharacterMat",
        keyframes=[
            # Rise from below
            Keyframe(frame=cfg.entrance_frame, property="location",
                     value=(0, 0, rise_start_z)),
            Keyframe(frame=cfg.entrance_frame + 30, property="location",
                     value=(0, 0, rise_end_z)),
            # Subtle idle sway after arrival
            Keyframe(frame=cfg.entrance_frame + 30, property="rotation_euler",
                     value=(0, 0, 0)),
            Keyframe(frame=frame_end, property="rotation_euler",
                     value=(0, 5, 0)),
        ],
    ))

    # --- Floor / pedestal ---
    scene.add(Mesh(
        name="Pedestal",
        primitive=PrimitiveType.CYLINDER,
        size=1.5,
        location=(0, 0, -1.0),
        material_name="PedestalMat",
    ))

    scene.add(Mesh(
        name="Floor",
        primitive=PrimitiveType.PLANE,
        size=30.0,
        location=(0, 0, -1.5),
        material_name="FloorMat",
    ))

    # --- Camera: orbit ---
    scene.add(Camera(
        name="Main_Camera",
        focal_length=50,
        dof_enabled=True,
        dof_focus_target=cfg.character_name,
        dof_aperture=2.8,
        preset=CameraPreset.ORBIT,
        preset_params={
            "radius": cfg.orbit_radius,
            "height": cfg.orbit_height,
            "revolutions": cfg.orbit_revolutions,
        },
        track_target=cfg.character_name,
    ))

    # --- Lighting ---
    rr, rg, rb = cfg.rim_color

    # Key light (warm, from above-front)
    scene.add(Light(
        name="Key_Light",
        light_type=LightType.AREA,
        location=(2, -4, 4),
        rotation=(55, 0, 20),
        energy=cfg.key_energy,
        size=1.5,
    ))

    # Dramatic rim light (colored, from behind)
    scene.add(Light(
        name="Rim_Light",
        light_type=LightType.AREA,
        location=(-1, 4, 3),
        rotation=(30, 0, 180),
        energy=cfg.rim_energy,
        color=cfg.rim_color,
        size=1.0,
    ))

    # Fill (very subtle)
    scene.add(Light(
        name="Fill_Light",
        light_type=LightType.AREA,
        location=(-4, -2, 2),
        rotation=(30, 0, -45),
        energy=50,
        size=2.0,
    ))

    return scene


def mascot_entrance_vfx(config: MascotEntranceConfig | None = None) -> dict:
    """Get VFX for mascot entrance."""
    cfg = config or MascotEntranceConfig()
    rr, rg, rb = cfg.rim_color

    result = {
        "materials": [
            Material(
                name="CharacterMat",
                base_color=(0.6, 0.6, 0.65, 1.0),
                metallic=0.1,
                roughness=0.5,
            ),
            Material(
                name="PedestalMat",
                base_color=(0.05, 0.05, 0.06, 1.0),
                metallic=0.9,
                roughness=0.1,
            ),
            Material(
                name="FloorMat",
                base_color=(0.01, 0.01, 0.015, 1.0),
                metallic=0.8,
                roughness=0.1,
            ),
        ],
        "volumetrics": [],
        "particles": [ambient_dust(location=(0, 0, 1))],
        "post": [cinematic_post()],
    }

    if cfg.fog_density > 0:
        result["volumetrics"].append(
            VolumetricFog(density=cfg.fog_density, anisotropy=0.3)
        )

    if cfg.spotlight:
        result["volumetrics"].append(
            VolumetricSpotlight(
                location=(0, 0, 6),
                rotation=(0, 0, 0),
                energy=cfg.spotlight_energy,
                spot_angle=25,
            )
        )

    if cfg.entrance_burst:
        result["particles"].append(
            explosion_burst(
                location=(0, 0, 0),
                frame=cfg.burst_frame,
            )
        )

    return result
