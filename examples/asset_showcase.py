"""
Asset Showcase -- demonstrates the Phase 3 asset pipeline.

Downloads an HDRI from Poly Haven, sets up lighting moods,
imports a model, and renders multiple mood variants.

Usage:
    python examples/asset_showcase.py
    # Then run the printed blender command

For MCP-based workflow (interactive in Blender):
    1. Launch Blender with MCP: blender --python scripts/start_blender_mcp.py
    2. Use download_polyhaven_asset MCP tool to fetch the HDRI
    3. Execute the generated script via execute_blender_code
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cinematic_pipeline.core.scene import Scene
from cinematic_pipeline.core.objects import Mesh, PrimitiveType
from cinematic_pipeline.core.camera import Camera, CameraPreset
from cinematic_pipeline.core.light import three_point_rig
from cinematic_pipeline.core.material import Material, metallic_dark, matte_white
from cinematic_pipeline.core.render import RenderConfig, write_and_render

from cinematic_pipeline.assets.hdri import dark_void, sci_fi_blue, MOOD_PRESETS
from cinematic_pipeline.assets.model_import import ImportedModel
from cinematic_pipeline.assets.library import AssetLibrary


def main():
    # --- Asset Library ---
    lib = AssetLibrary()
    print(f"Asset Library: {lib.summary()}")
    print(f"Library location: {lib.library_dir}")

    # --- Show available moods ---
    print(f"\nAvailable lighting moods ({len(MOOD_PRESETS)}):")
    for name, factory in MOOD_PRESETS.items():
        mood = factory()
        print(f"  {name}: {mood.description}")
        if mood.hdri.polyhaven_id:
            print(f"    HDRI: {mood.hdri.polyhaven_id} (download via MCP)")

    # --- Scene with dark void mood ---
    mood = dark_void()

    scene = Scene(
        name="Asset_Showcase",
        fps=30,
        frame_start=1,
        frame_end=90,
        render_engine="CYCLES",
        render_samples=64,
        world_color=mood.world_color,
    )

    # Hero cube
    hero_mat = metallic_dark()
    scene.add(Mesh(
        name="Hero_Cube", primitive=PrimitiveType.CUBE, size=1.8,
        location=(0, 0, 0), material_name="Metallic_Dark",
    ))

    # Floor
    floor_mat = Material(
        name="Floor", base_color=(0.02, 0.02, 0.02, 1.0),
        metallic=0.8, roughness=0.1,
    )
    scene.add(Mesh(
        name="Floor", primitive=PrimitiveType.PLANE, size=20.0,
        location=(0, 0, -1.5), material_name="Floor",
    ))

    # Camera
    scene.add(Camera(
        name="Main_Camera",
        focal_length=50,
        preset=CameraPreset.ORBIT,
        preset_params={"radius": 5.0, "height": 2.0, "revolutions": 0.1},
        track_target="Hero_Cube",
        dof_enabled=True,
        dof_focus_target="Hero_Cube",
        dof_aperture=2.8,
    ))

    # Lighting
    for light in three_point_rig(key_energy=300):
        scene.add(light)

    # --- Generate render script ---
    output_dir = "./output/asset_showcase"
    config = RenderConfig(output_dir=output_dir, filename_prefix="showcase_")
    cmd = write_and_render(scene, config, mode="still")

    # Patch with materials + mood
    script_path = os.path.join(output_dir, "_render_script.py")
    with open(script_path, "r") as f:
        base_script = f.read()

    vfx_block = "\n\n".join([
        "# ===== MATERIALS =====",
        hero_mat.to_blender_script(),
        floor_mat.to_blender_script(),
        "",
        "# ===== LIGHTING MOOD =====",
        mood.to_blender_script(),
    ])

    patched = base_script.replace(
        "# Object: Hero_Cube",
        vfx_block + "\n\n# Object: Hero_Cube",
    )

    with open(script_path, "w") as f:
        f.write(patched)

    print(f"\nScene: {scene.name}")
    print(f"Mood: {mood.name} -- {mood.description}")
    print(f"\nTo render:")
    print(f'  "C:/Program Files/Blender Foundation/Blender 5.0/blender.exe" --background -E CYCLES --python {os.path.abspath(script_path)!r}')
    print(f"\nOutput: {os.path.abspath(output_dir)}")

    # --- Show model import usage ---
    print("\n--- Model Import Examples ---")

    model_glb = ImportedModel(
        file_path="models/fighter_jet.glb",
        name="FighterJet",
        target_size=4.0,
        location=(0, 0, 0),
    )
    print(f"\nGLB import ({model_glb.name}):")
    print(f"  Target size: {model_glb.target_size}m")
    print(f"  Script generates: import_scene.gltf + auto-scale + center origin")

    model_fbx = ImportedModel(
        file_path="models/character.fbx",
        name="Character",
        target_size=1.7,
    )
    print(f"\nFBX import ({model_fbx.name}):")
    print(f"  Target size: {model_fbx.target_size}m")

    # --- MCP workflow ---
    print("\n--- MCP Workflow ---")
    print("For interactive scene building with real assets:")
    print("  1. search_polyhaven_assets('models') -> find model IDs")
    print("  2. download_polyhaven_asset(id, 'models') -> import into Blender")
    print("  3. search_polyhaven_assets('hdris', 'studio') -> find HDRI IDs")
    print("  4. download_polyhaven_asset(id, 'hdris', '2k') -> set environment")
    print("  5. get_viewport_screenshot() -> preview the scene")
    print("  6. execute_blender_code(render_script) -> final render")

    scene.save(os.path.join(output_dir, "scene.json"))


if __name__ == "__main__":
    main()
