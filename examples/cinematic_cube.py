"""
Cinematic Cube — Full pipeline demo with VFX.

Metallic cube with dramatic lighting, volumetric fog, ambient particles,
orbit camera with depth of field, and cinematic post-processing.

Usage:
    python examples/cinematic_cube.py
    # Then run the printed blender command
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cinematic_pipeline.core.scene import Scene
from cinematic_pipeline.core.objects import Mesh, PrimitiveType, Empty
from cinematic_pipeline.core.camera import Camera, CameraPreset
from cinematic_pipeline.core.light import Light, three_point_rig, neon_accent_rig
from cinematic_pipeline.core.material import Material, metallic_dark, neon_emissive
from cinematic_pipeline.core.animation import Keyframe
from cinematic_pipeline.core.render import RenderConfig, write_and_render

from cinematic_pipeline.vfx.particles import ambient_dust, holographic_dust
from cinematic_pipeline.vfx.volumetrics import VolumetricFog, dramatic_overhead
from cinematic_pipeline.vfx.compositing import cinematic_post


def main():
    # --- Materials ---
    hero_mat = metallic_dark()
    floor_mat = Material(
        name="Floor", base_color=(0.03, 0.03, 0.04, 1.0),
        metallic=0.1, roughness=0.85,
    )
    accent_mat = neon_emissive(color=(0.0, 0.5, 1.0))

    # --- Scene ---
    scene = Scene(
        name="Cinematic_Cube",
        fps=30,
        frame_start=1,
        frame_end=90,  # 3 seconds (short for fast test render)
        render_engine="CYCLES",
        render_samples=64,
        world_color=(0.003, 0.003, 0.008),
    )

    # Floor
    scene.add(Mesh(
        name="Floor", primitive=PrimitiveType.PLANE, size=30.0,
        location=(0, 0, -1.5), material_name="Floor",
    ))

    # Hero cube with slow rotation
    scene.add(Mesh(
        name="Hero_Cube", primitive=PrimitiveType.CUBE, size=1.8,
        location=(0, 0, 0), material_name="Metallic_Dark",
        keyframes=[
            Keyframe(frame=1, property="rotation_euler", value=(15, 15, 0)),
            Keyframe(frame=90, property="rotation_euler", value=(15, 15, 45)),
        ],
    ))

    # Small accent sphere (neon glow)
    scene.add(Mesh(
        name="Accent_Sphere", primitive=PrimitiveType.SPHERE, size=0.3,
        segments=24, location=(1.5, -0.5, 0.8), material_name="Neon_Emissive",
    ))

    # Camera — slow orbit with DOF
    scene.add(Camera(
        name="Main_Camera",
        focal_length=65,
        dof_enabled=True,
        dof_focus_target="Hero_Cube",
        dof_aperture=2.0,
        preset=CameraPreset.ORBIT,
        preset_params={"radius": 5.5, "height": 1.5, "revolutions": 0.15},
        track_target="Hero_Cube",
    ))

    # Lighting — three-point base + neon accents
    for light in three_point_rig(key_energy=300):
        scene.add(light)
    for light in neon_accent_rig(
        accent_color=(0.0, 0.5, 1.0), energy=400,
    ):
        scene.add(light)

    # --- Generate the render script ---
    output_dir = "./output/cinematic_cube"
    config = RenderConfig(
        output_dir=output_dir,
        filename_prefix="cine_",
    )
    cmd = write_and_render(scene, config, mode="still")

    # Now patch the render script with materials, VFX, and post-processing
    script_path = os.path.join(output_dir, "_render_script.py")
    with open(script_path, "r") as f:
        base_script = f.read()

    # Build the full script with materials + VFX + post inserted
    vfx_sections = []

    # Materials (before objects)
    vfx_sections.append("# ===== MATERIALS =====")
    vfx_sections.append(hero_mat.to_blender_script())
    vfx_sections.append(floor_mat.to_blender_script())
    vfx_sections.append(accent_mat.to_blender_script())

    # VFX (after objects)
    vfx_sections.append("")
    vfx_sections.append("# ===== VFX =====")

    # Volumetric fog
    fog = VolumetricFog(density=0.015, anisotropy=0.3)
    vfx_sections.append(fog.to_blender_script())

    # Volumetric overhead spot
    spot = dramatic_overhead(target=(0, 0, 0), energy=600)
    vfx_sections.append(spot.to_blender_script())

    # Ambient particles
    dust = holographic_dust(location=(0, 0, 0))
    vfx_sections.append(dust.to_blender_script())

    # Post-processing
    post = cinematic_post()
    vfx_sections.append("")
    vfx_sections.append("# ===== POST-PROCESSING =====")
    vfx_sections.append(post.to_blender_script())

    vfx_block = "\n\n".join(vfx_sections)

    # Inject materials before objects, VFX after objects
    patched = base_script.replace(
        "# Object: Floor",
        vfx_block + "\n\n# Object: Floor",
    )

    with open(script_path, "w") as f:
        f.write(patched)

    print(f"\nScene: {scene.name}")
    print(f"Duration: {scene.duration_seconds}s at {scene.fps}fps")
    print(f"Engine: {scene.render_engine}")
    print(f"VFX: volumetric fog, overhead spot, holographic dust, cinematic post")
    print(f"\nTo render a still frame:")
    print(f'  "C:/Program Files/Blender Foundation/Blender 5.0/blender.exe" --background -E CYCLES --python {os.path.abspath(script_path)!r}')
    print(f"\nOutput will be in: {os.path.abspath(output_dir)}")

    scene.save(os.path.join(output_dir, "scene.json"))


if __name__ == "__main__":
    main()
