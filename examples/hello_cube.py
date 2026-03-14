"""
Hello Cube — The simplest cinematic pipeline scene.

Renders a metallic cube with dramatic lighting and a slow orbit camera.
This is the smoke test: if this renders, the pipeline works.

Usage:
    # Generate the Blender script and render command
    python examples/hello_cube.py

    # Then run the output command, e.g.:
    blender --background -E CYCLES --python output/hello_cube/_render_script.py
"""

import sys
from pathlib import Path

# Add src to path for running examples directly
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cinematic_pipeline.core.scene import Scene
from cinematic_pipeline.core.objects import Mesh, PrimitiveType
from cinematic_pipeline.core.camera import Camera, CameraPreset
from cinematic_pipeline.core.light import Light, LightType, three_point_rig
from cinematic_pipeline.core.material import Material, metallic_dark
from cinematic_pipeline.core.animation import Keyframe
from cinematic_pipeline.core.render import RenderConfig, write_and_render


def main():
    # Create materials
    dark_metal = metallic_dark()
    floor_mat = Material(
        name="Floor",
        base_color=(0.05, 0.05, 0.06, 1.0),
        metallic=0.1, roughness=0.9,
    )

    # Create scene
    scene = Scene(
        name="Hello_Cube",
        fps=30,
        frame_end=150,  # 5 seconds
        render_engine="CYCLES",
        render_samples=64,  # Low for fast preview
        world_color=(0.005, 0.005, 0.01),
    )

    # Floor
    scene.add(Mesh(
        name="Floor",
        primitive=PrimitiveType.PLANE,
        size=20.0,
        location=(0, 0, -1),
        material_name="Floor",
    ))

    # Hero cube with rotation animation
    scene.add(Mesh(
        name="Hero_Cube",
        primitive=PrimitiveType.CUBE,
        size=1.5,
        location=(0, 0, 0),
        material_name="Metallic_Dark",
        keyframes=[
            Keyframe(frame=1, property="rotation_euler", value=(0, 0, 0)),
            Keyframe(frame=150, property="rotation_euler", value=(0, 0, 90)),
        ],
    ))

    # Camera — orbit around the cube
    scene.add(Camera(
        name="Main_Camera",
        location=(4, -4, 3),
        focal_length=50,
        dof_enabled=True,
        dof_focus_target="Hero_Cube",
        dof_aperture=2.8,
        preset=CameraPreset.ORBIT,
        preset_params={"radius": 5, "height": 2, "revolutions": 0.5},
        track_target="Hero_Cube",
    ))

    # Three-point lighting
    for light in three_point_rig(key_energy=200):
        scene.add(light)

    # Write render script
    config = RenderConfig(output_dir="./output/hello_cube", filename_prefix="hello_")

    # Generate the Blender command
    cmd = write_and_render(scene, config, mode="animation")
    print(f"\nScene: {scene.name}")
    print(f"Duration: {scene.duration_seconds}s at {scene.fps}fps")
    print(f"Engine: {scene.render_engine}")
    print(f"\nTo render, run:\n  {cmd}")

    # Also save the scene JSON for reproducibility
    scene.save("./output/hello_cube/scene.json")
    print(f"\nScene saved to: ./output/hello_cube/scene.json")

    # Also generate the material scripts (they need to be in the render script)
    # The scene's to_blender_script() handles objects but materials need to be created first
    script_path = "./output/hello_cube/_render_script.py"
    with open(script_path, "r") as f:
        existing = f.read()

    material_scripts = "\n".join([
        "# --- Materials ---",
        dark_metal.to_blender_script(),
        "",
        floor_mat.to_blender_script(),
        "",
    ])

    # Insert materials after the imports but before object creation
    parts = existing.split("# Clear existing scene")
    if len(parts) == 2:
        patched = parts[0] + "# Clear existing scene" + parts[1].split("\n", 2)[0] + "\n"
        # Find where objects start and insert materials before
        patched = existing.replace(
            "# Object: Floor",
            material_scripts + "\n# Object: Floor",
        )
        with open(script_path, "w") as f:
            f.write(patched)
        print("Materials injected into render script.")


if __name__ == "__main__":
    main()
