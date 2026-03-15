"""Tests for asset pipeline — no Blender required."""

import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cinematic_pipeline.assets.model_import import (
    ImportedModel, SketchfabModel, ModelFormat, detect_format,
)
from cinematic_pipeline.assets.hdri import (
    HDRIEnvironment, LightingMood,
    studio_soft, studio_dramatic, outdoor_sunset, outdoor_overcast,
    night_urban, dark_void, sci_fi_blue, MOOD_PRESETS,
)
from cinematic_pipeline.assets.library import (
    AssetLibrary, AssetMetadata,
)


# --- Model Import ---

def test_detect_format():
    assert detect_format("model.gltf") == ModelFormat.GLTF
    assert detect_format("model.glb") == ModelFormat.GLB
    assert detect_format("model.fbx") == ModelFormat.FBX
    assert detect_format("model.obj") == ModelFormat.OBJ


def test_detect_format_case_insensitive():
    assert detect_format("Model.GLB") == ModelFormat.GLB
    assert detect_format("test.FBX") == ModelFormat.FBX


def test_detect_format_unsupported():
    try:
        detect_format("model.stl")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_imported_model_gltf_script():
    m = ImportedModel(file_path="scene.glb", name="Hero", target_size=2.0)
    script = m.to_blender_script()
    assert "import_scene.gltf" in script
    assert "_before = set(bpy.data.objects.keys())" in script
    assert "target size 2.0" in script
    assert "'Hero'" in script


def test_imported_model_fbx_script():
    m = ImportedModel(file_path="robot.fbx", name="Robot")
    script = m.to_blender_script()
    assert "import_scene.fbx" in script


def test_imported_model_obj_script():
    m = ImportedModel(file_path="car.obj")
    script = m.to_blender_script()
    assert "wm.obj_import" in script


def test_imported_model_auto_name():
    m = ImportedModel(file_path="/path/to/my_model.glb")
    assert m.name == "my_model"


def test_imported_model_serialization():
    m = ImportedModel(file_path="test.glb", name="Test", target_size=1.5)
    d = m.to_dict()
    assert d["type"] == "ImportedModel"
    assert d["target_size"] == 1.5


def test_imported_model_no_empties():
    m = ImportedModel(file_path="test.glb", remove_empties=False)
    script = m.to_blender_script()
    assert "Remove empty" not in script


def test_sketchfab_model():
    s = SketchfabModel(uid="abc123", name="Fighter", target_size=4.5)
    d = s.to_dict()
    assert d["type"] == "SketchfabModel"
    assert d["uid"] == "abc123"
    assert d["target_size"] == 4.5


# --- HDRI ---

def test_hdri_with_path():
    h = HDRIEnvironment(hdri_path="/hdris/studio.hdr", strength=1.5)
    script = h.to_blender_script()
    assert "ShaderNodeTexEnvironment" in script
    assert "studio.hdr" in script
    assert "1.5" in script


def test_hdri_polyhaven_id_only():
    h = HDRIEnvironment(polyhaven_id="studio_small_09")
    script = h.to_blender_script()
    assert "MCP" in script  # Falls back to MCP instruction
    assert "studio_small_09" in script


def test_hdri_no_background():
    h = HDRIEnvironment(hdri_path="/test.hdr", use_background=False)
    script = h.to_blender_script()
    assert "cycles_visibility.camera" in script


def test_hdri_rotation():
    h = HDRIEnvironment(hdri_path="/test.hdr", rotation_z=90)
    script = h.to_blender_script()
    assert "90" in script
    assert "Rotation" in script


def test_lighting_mood_with_hdri():
    mood = studio_soft()
    assert mood.name == "Studio Soft"
    assert mood.hdri.polyhaven_id == "studio_small_09"


def test_lighting_mood_dark_void():
    mood = dark_void()
    script = mood.to_blender_script()
    assert "solid color fallback" in script
    assert "0.003" in script


def test_all_mood_presets():
    assert len(MOOD_PRESETS) == 7
    for name, factory in MOOD_PRESETS.items():
        mood = factory()
        assert mood.name, f"Preset '{name}' has no name"
        d = mood.to_dict()
        assert d["type"] == "LightingMood"


# --- Asset Library ---

def test_library_creation():
    with tempfile.TemporaryDirectory() as tmpdir:
        lib = AssetLibrary(tmpdir)
        assert lib.count == 0
        assert "empty" in lib.summary()


def test_library_register_and_get():
    with tempfile.TemporaryDirectory() as tmpdir:
        lib = AssetLibrary(tmpdir)
        # Create a fake file
        fake_file = os.path.join(tmpdir, "hdris", "test.hdr")
        Path(fake_file).touch()

        meta = lib.register_file(
            source="polyhaven",
            asset_id="studio_small_09",
            asset_type="hdri",
            file_path=fake_file,
            name="Studio Small",
            resolution="2k",
            tags=["studio", "indoor"],
        )

        assert lib.count == 1
        assert lib.has("polyhaven", "studio_small_09", "2k")
        got = lib.get("polyhaven", "studio_small_09", "2k")
        assert got is not None
        assert got.name == "Studio Small"


def test_library_search():
    with tempfile.TemporaryDirectory() as tmpdir:
        lib = AssetLibrary(tmpdir)
        fake = os.path.join(tmpdir, "models", "jet.glb")
        Path(fake).touch()

        lib.register_file(
            source="sketchfab", asset_id="abc123",
            asset_type="model", file_path=fake,
            name="Fighter Jet", tags=["military", "aircraft"],
        )
        lib.register_file(
            source="polyhaven", asset_id="studio_small_09",
            asset_type="hdri", file_path=fake,
            name="Studio Small", tags=["studio"],
        )

        assert len(lib.search("jet")) == 1
        assert len(lib.search("studio")) == 1
        assert len(lib.search("military")) == 1
        assert len(lib.search("nonexistent")) == 0


def test_library_list_by_type():
    with tempfile.TemporaryDirectory() as tmpdir:
        lib = AssetLibrary(tmpdir)
        fake = os.path.join(tmpdir, "models", "test.glb")
        Path(fake).touch()

        lib.register_file(source="local", asset_id="m1", asset_type="model", file_path=fake)
        lib.register_file(source="local", asset_id="h1", asset_type="hdri", file_path=fake)

        assert len(lib.list_assets("model")) == 1
        assert len(lib.list_assets("hdri")) == 1
        assert len(lib.list_assets()) == 2


def test_library_remove():
    with tempfile.TemporaryDirectory() as tmpdir:
        lib = AssetLibrary(tmpdir)
        fake = os.path.join(tmpdir, "models", "test.glb")
        Path(fake).touch()

        lib.register_file(source="local", asset_id="m1", asset_type="model", file_path=fake)
        assert lib.count == 1
        lib.remove("local", "m1")
        assert lib.count == 0


def test_library_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake = os.path.join(tmpdir, "models", "test.glb")
        os.makedirs(os.path.dirname(fake), exist_ok=True)
        Path(fake).touch()

        lib1 = AssetLibrary(tmpdir)
        lib1.register_file(source="local", asset_id="m1", asset_type="model", file_path=fake)

        # Reload from disk
        lib2 = AssetLibrary(tmpdir)
        assert lib2.count == 1
        assert lib2.has("local", "m1")


def test_library_summary():
    with tempfile.TemporaryDirectory() as tmpdir:
        lib = AssetLibrary(tmpdir)
        fake = os.path.join(tmpdir, "models", "test.glb")
        Path(fake).touch()

        lib.register_file(source="local", asset_id="m1", asset_type="model", file_path=fake)
        lib.register_file(source="local", asset_id="h1", asset_type="hdri", file_path=fake)

        summary = lib.summary()
        assert "2 assets" in summary
        assert "hdri" in summary
        assert "model" in summary


if __name__ == "__main__":
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
