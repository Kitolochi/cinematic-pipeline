"""Tests for the core scene graph — no Blender required."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cinematic_pipeline.core.scene import Scene
from cinematic_pipeline.core.objects import Mesh, PrimitiveType, Empty
from cinematic_pipeline.core.camera import Camera, CameraPreset
from cinematic_pipeline.core.light import Light, LightType, three_point_rig
from cinematic_pipeline.core.material import Material, metallic_dark, holographic_glass
from cinematic_pipeline.core.animation import Keyframe, AnimationPath


def test_scene_creation():
    scene = Scene(name="Test", fps=30, frame_end=90)
    assert scene.duration_seconds == 3.0
    assert scene.name == "Test"


def test_scene_add_objects():
    scene = Scene()
    scene.add(Mesh(name="Cube"))
    scene.add(Camera(name="Cam"))
    scene.add(Light(name="Sun"))
    assert len(scene.objects) == 1
    assert len(scene.cameras) == 1
    assert len(scene.lights) == 1


def test_scene_serialization():
    scene = Scene(name="Serialize_Test")
    scene.add(Mesh(name="Box", primitive=PrimitiveType.CUBE, location=(1, 2, 3)))
    scene.add(Camera(name="Cam", preset=CameraPreset.ORBIT))

    data = scene.to_dict()
    assert data["name"] == "Serialize_Test"
    assert len(data["objects"]) == 1
    assert data["objects"][0]["location"] == [1, 2, 3]

    json_str = scene.to_json()
    parsed = json.loads(json_str)
    assert parsed["name"] == "Serialize_Test"


def test_mesh_to_blender_script():
    mesh = Mesh(name="Sphere", primitive=PrimitiveType.SPHERE, size=2.0, location=(1, 0, 0))
    script = mesh.to_blender_script()
    assert "primitive_uv_sphere_add" in script
    assert "radius=1.0" in script
    assert "'Sphere'" in script


def test_camera_orbit_script():
    cam = Camera(
        name="OrbitCam",
        preset=CameraPreset.ORBIT,
        preset_params={"radius": 5, "height": 2},
        track_target="Target",
    )
    script = cam.to_blender_script()
    assert "orbit_pivot" in script
    assert "TRACK_TO" in script


def test_camera_dolly_script():
    cam = Camera(name="DollyCam", preset=CameraPreset.DOLLY_IN)
    script = cam.to_blender_script()
    assert "Dolly in" in script


def test_camera_handheld_script():
    cam = Camera(name="HandheldCam", preset=CameraPreset.HANDHELD)
    script = cam.to_blender_script()
    assert "NOISE" in script


def test_light_script():
    light = Light(
        name="Spot", light_type=LightType.SPOT,
        location=(0, 0, 5), energy=300, spot_angle=35,
    )
    script = light.to_blender_script()
    assert "SPOT" in script
    assert "spot_size" in script


def test_light_volumetric():
    light = Light(name="VolSpot", light_type=LightType.SPOT, volumetric=True)
    script = light.to_blender_script()
    assert "Volume Scatter" in script


def test_three_point_rig():
    lights = three_point_rig()
    assert len(lights) == 3
    names = {l.name for l in lights}
    assert "Key_Light" in names
    assert "Fill_Light" in names
    assert "Rim_Light" in names


def test_material_script():
    mat = metallic_dark()
    script = mat.to_blender_script()
    assert "Principled BSDF" in script
    assert "Metallic" in script


def test_holographic_material():
    mat = holographic_glass()
    script = mat.to_blender_script()
    assert "Emission Strength" in script
    assert "Transmission" in script


def test_keyframe():
    kf = Keyframe(frame=30, property="location", value=(1, 2, 3))
    script = kf.to_blender_script("obj")
    assert "keyframe_insert" in script
    assert "frame=30" in script


def test_animation_path():
    path = AnimationPath(
        target_name="Cube",
        keyframes=[
            Keyframe(frame=1, property="location", value=(0, 0, 0)),
            Keyframe(frame=60, property="location", value=(5, 0, 0)),
        ],
    )
    script = path.to_blender_script()
    assert "'Cube'" in script
    assert "frame=1" in script
    assert "frame=60" in script


def test_scene_to_blender_script():
    scene = Scene(name="FullTest", render_engine="CYCLES", render_samples=32)
    scene.add(Mesh(name="Cube"))
    scene.add(Camera(name="Cam"))
    scene.add(Light(name="Light"))

    script = scene.to_blender_script()
    assert "import bpy" in script
    assert "CYCLES" in script
    assert "cycles.samples = 32" in script
    assert "Object: Cube" in script
    assert "Camera: Cam" in script
    assert "Light: Light" in script


if __name__ == "__main__":
    # Simple test runner — no pytest dependency needed
    import traceback
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {test.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed out of {len(tests)} tests")
