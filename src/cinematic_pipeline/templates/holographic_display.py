"""Holographic Display / Floating UI template.

Floating 3D UI panels with holographic material (emission + transparency),
scan-line overlay, scale-up entrance animation. Data readouts animate in.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cinematic_pipeline.core.scene import Scene
from cinematic_pipeline.core.objects import Mesh, PrimitiveType, Empty
from cinematic_pipeline.core.camera import Camera, CameraPreset
from cinematic_pipeline.core.light import Light, LightType
from cinematic_pipeline.core.material import Material
from cinematic_pipeline.core.animation import Keyframe
from cinematic_pipeline.vfx.particles import holographic_dust
from cinematic_pipeline.vfx.compositing import sci_fi_glow


@dataclass
class HoloPanelConfig:
    """Configuration for a single holographic panel."""

    name: str = "Panel"
    width: float = 2.0
    height: float = 1.2
    location: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)
    entrance_frame: int = 1
    entrance_duration: int = 20  # frames


@dataclass
class HolographicDisplayConfig:
    """Configuration for the holographic display shot."""

    # Panels
    panels: list[HoloPanelConfig] = field(default_factory=lambda: [
        HoloPanelConfig(name="Main_Panel", width=2.5, height=1.5,
                        location=(0, 0, 0.5), rotation=(0, -10, 0)),
        HoloPanelConfig(name="Side_Panel_L", width=1.2, height=0.8,
                        location=(-2.2, 0.3, 0.8), rotation=(0, -20, 5),
                        entrance_frame=15),
        HoloPanelConfig(name="Side_Panel_R", width=1.2, height=0.8,
                        location=(2.2, 0.3, 0.2), rotation=(0, 20, -5),
                        entrance_frame=25),
    ])

    # Material
    holo_color: tuple[float, float, float] = (0.0, 0.8, 1.0)  # Cyan
    holo_emission: float = 3.0
    holo_alpha: float = 0.15

    # Scene
    duration_seconds: float = 5.0
    fps: int = 30
    render_engine: str = "CYCLES"
    render_samples: int = 128


def holographic_display(config: HolographicDisplayConfig | None = None) -> Scene:
    """Build a holographic display scene with floating panels."""
    cfg = config or HolographicDisplayConfig()
    frame_end = int(cfg.duration_seconds * cfg.fps)

    scene = Scene(
        name="Holographic_Display",
        fps=cfg.fps,
        frame_start=1,
        frame_end=frame_end,
        render_engine=cfg.render_engine,
        render_samples=cfg.render_samples,
        world_color=(0.003, 0.003, 0.008),
    )

    # --- Floor ---
    scene.add(Mesh(
        name="Floor",
        primitive=PrimitiveType.PLANE,
        size=20.0,
        location=(0, 0, -1.5),
        material_name="HoloFloor",
    ))

    # --- Panels with scale-up entrance ---
    for panel_cfg in cfg.panels:
        px, py, pz = panel_cfg.location
        rx, ry, rz = panel_cfg.rotation
        ef = panel_cfg.entrance_frame
        ed = panel_cfg.entrance_duration

        scene.add(Mesh(
            name=panel_cfg.name,
            primitive=PrimitiveType.PLANE,
            size=1.0,
            location=panel_cfg.location,
            rotation=panel_cfg.rotation,
            scale=(panel_cfg.width, panel_cfg.height, 1.0),
            material_name="Holographic",
            keyframes=[
                # Scale entrance: 0 -> full size
                Keyframe(frame=ef, property="scale",
                         value=(0.01, 0.01, 0.01)),
                Keyframe(frame=ef + ed, property="scale",
                         value=(panel_cfg.width, panel_cfg.height, 1.0)),
                # Slight wobble at end
                Keyframe(frame=ef + ed + 5, property="rotation_euler",
                         value=(rx + 2, ry - 1, rz)),
                Keyframe(frame=ef + ed + 15, property="rotation_euler",
                         value=(rx, ry, rz)),
            ],
        ))

    # --- Camera ---
    scene.add(Camera(
        name="Main_Camera",
        location=(0, -5, 1.0),
        focal_length=35,
        dof_enabled=True,
        dof_focus_target="Main_Panel",
        dof_aperture=4.0,
        preset=CameraPreset.STATIC,
        track_target="Main_Panel",
    ))

    # --- Lighting ---
    hr, hg, hb = cfg.holo_color
    scene.add(Light(
        name="Holo_Key",
        light_type=LightType.AREA,
        location=(0, -3, 3),
        rotation=(60, 0, 0),
        energy=150,
        color=cfg.holo_color,
        size=2.0,
    ))
    scene.add(Light(
        name="Fill",
        light_type=LightType.AREA,
        location=(3, -2, 2),
        rotation=(40, 0, 45),
        energy=50,
        size=1.5,
    ))

    return scene


def holographic_display_vfx(config: HolographicDisplayConfig | None = None) -> dict:
    """Get VFX for holographic display."""
    cfg = config or HolographicDisplayConfig()
    hr, hg, hb = cfg.holo_color

    return {
        "materials": [
            Material(
                name="Holographic",
                base_color=(hr, hg, hb, cfg.holo_alpha),
                metallic=0.0,
                roughness=0.3,
                emission_color=(hr, hg, hb),
                emission_strength=cfg.holo_emission,
                alpha=cfg.holo_alpha,
            ),
            Material(
                name="HoloFloor",
                base_color=(0.01, 0.01, 0.015, 1.0),
                metallic=0.9,
                roughness=0.05,
            ),
        ],
        "particles": [holographic_dust(location=(0, 0, 0))],
        "post": [sci_fi_glow()],
    }


def holographic_display_mcp_script(config: HolographicDisplayConfig | None = None) -> str:
    """Generate MCP script for scan-line overlay on panels."""
    cfg = config or HolographicDisplayConfig()
    hr, hg, hb = cfg.holo_color
    frame_end = int(cfg.duration_seconds * cfg.fps)

    panel_names = [p.name for p in cfg.panels]

    return f"""
import bpy
import math

# --- Scan-line material for holographic panels ---
for panel_name in {panel_names!r}:
    obj = bpy.data.objects.get(panel_name)
    if not obj:
        continue

    mat = bpy.data.materials.new(f"Holo_{{panel_name}}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear defaults
    for n in nodes:
        nodes.remove(n)

    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)

    # Mix shader for transparency
    mix = nodes.new('ShaderNodeMixShader')
    mix.location = (400, 0)

    # Transparent BSDF
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    transparent.location = (200, -100)

    # Emission for holographic glow
    emission = nodes.new('ShaderNodeEmission')
    emission.location = (200, 100)
    emission.inputs['Color'].default_value = ({hr}, {hg}, {hb}, 1.0)
    emission.inputs['Strength'].default_value = {cfg.holo_emission}

    # Scan-line pattern: wave texture for horizontal lines
    wave = nodes.new('ShaderNodeTexWave')
    wave.location = (-200, 0)
    wave.wave_type = 'BANDS'
    wave.inputs['Scale'].default_value = 20.0
    wave.inputs['Detail'].default_value = 0.0

    # Color ramp to sharpen lines
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (0, 0)
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[1].position = 0.55

    links.new(wave.outputs['Color'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], mix.inputs['Fac'])
    links.new(transparent.outputs['BSDF'], mix.inputs[1])
    links.new(emission.outputs['Emission'], mix.inputs[2])
    links.new(mix.outputs['Shader'], output.inputs['Surface'])

    # Assign to panel
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

print("Holographic scan-line materials applied to panels")
"""
