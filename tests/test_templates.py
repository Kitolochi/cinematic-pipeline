"""Tests for scene templates -- no Blender required."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cinematic_pipeline.core.scene import Scene
from cinematic_pipeline.core.material import Material

from cinematic_pipeline.templates.token_reveal import (
    TokenRevealConfig, token_reveal, token_reveal_vfx, token_reveal_mcp_script,
)
from cinematic_pipeline.templates.holographic_display import (
    HolographicDisplayConfig, HoloPanelConfig,
    holographic_display, holographic_display_vfx, holographic_display_mcp_script,
)
from cinematic_pipeline.templates.fighter_jet import (
    FighterJetConfig, fighter_jet_flyby, fighter_jet_vfx, fighter_jet_mcp_instructions,
)
from cinematic_pipeline.templates.point_cloud_city import (
    PointCloudCityConfig, point_cloud_city, point_cloud_city_vfx, point_cloud_city_mcp_script,
)
from cinematic_pipeline.templates.mascot_entrance import (
    MascotEntranceConfig, mascot_entrance, mascot_entrance_vfx,
)


# --- Token Reveal ---

def test_token_reveal_default():
    scene = token_reveal()
    assert isinstance(scene, Scene)
    assert scene.name == "Token_Reveal"
    assert scene.frame_end == 150  # 5s * 30fps


def test_token_reveal_custom_config():
    cfg = TokenRevealConfig(
        token_text="$KNTQ",
        token_size=2.0,
        duration_seconds=10.0,
        fps=24,
    )
    scene = token_reveal(cfg)
    assert scene.frame_end == 240  # 10s * 24fps
    assert scene.fps == 24


def test_token_reveal_has_objects():
    scene = token_reveal()
    obj_names = [obj.name for obj in scene.objects]
    cam_names = [c.name for c in scene.cameras]
    assert "Token" in obj_names
    assert "Floor" in obj_names
    assert "Main_Camera" in cam_names
    assert len(scene.lights) == 3


def test_token_reveal_vfx_default():
    vfx = token_reveal_vfx()
    assert "materials" in vfx
    assert "volumetrics" in vfx
    assert "particles" in vfx
    assert "post" in vfx
    assert len(vfx["materials"]) == 2  # Token + Floor
    assert len(vfx["volumetrics"]) == 2  # Fog + GodRays
    assert len(vfx["particles"]) == 1  # Holographic dust
    assert len(vfx["post"]) == 1  # Cinematic post


def test_token_reveal_vfx_no_godrays():
    cfg = TokenRevealConfig(god_rays=False, fog_density=0)
    vfx = token_reveal_vfx(cfg)
    assert len(vfx["volumetrics"]) == 0


def test_token_reveal_vfx_sci_fi():
    cfg = TokenRevealConfig(post_preset="sci_fi")
    vfx = token_reveal_vfx(cfg)
    assert len(vfx["post"]) == 1


def test_token_reveal_mcp_script():
    script = token_reveal_mcp_script()
    assert "text_add" in script
    assert "TOKEN" in script
    assert "Token_Material" in script
    assert "convert(target='MESH')" in script


def test_token_reveal_mcp_custom_text():
    cfg = TokenRevealConfig(token_text="$SUPER")
    script = token_reveal_mcp_script(cfg)
    assert "$SUPER" in script


# --- Holographic Display ---

def test_holographic_display_default():
    scene = holographic_display()
    assert isinstance(scene, Scene)
    assert scene.name == "Holographic_Display"


def test_holographic_display_panels():
    scene = holographic_display()
    names = [obj.name for obj in scene.objects]
    assert "Main_Panel" in names
    assert "Side_Panel_L" in names
    assert "Side_Panel_R" in names


def test_holographic_display_custom_panels():
    cfg = HolographicDisplayConfig(panels=[
        HoloPanelConfig(name="Single", width=3.0, height=2.0),
    ])
    scene = holographic_display(cfg)
    names = [obj.name for obj in scene.objects]
    assert "Single" in names
    assert "Side_Panel_L" not in names


def test_holographic_display_vfx():
    vfx = holographic_display_vfx()
    assert "materials" in vfx
    assert len(vfx["materials"]) == 2  # Holographic + HoloFloor
    mat_names = [m.name for m in vfx["materials"]]
    assert "Holographic" in mat_names
    assert "HoloFloor" in mat_names


def test_holographic_display_mcp_script():
    script = holographic_display_mcp_script()
    assert "ShaderNodeTexWave" in script
    assert "Main_Panel" in script
    assert "scan-line" in script.lower()


# --- Fighter Jet ---

def test_fighter_jet_default():
    scene = fighter_jet_flyby()
    assert isinstance(scene, Scene)
    assert scene.name == "Fighter_Jet_Flyby"


def test_fighter_jet_objects():
    scene = fighter_jet_flyby()
    obj_names = [obj.name for obj in scene.objects]
    cam_names = [c.name for c in scene.cameras]
    light_names = [l.name for l in scene.lights]
    assert "Fighter_Jet" in obj_names
    assert "Chase_Camera" in cam_names
    assert "Sun" in light_names
    assert "Afterburner_Glow" in light_names


def test_fighter_jet_no_afterburner():
    cfg = FighterJetConfig(afterburner_particles=False)
    scene = fighter_jet_flyby(cfg)
    light_names = [l.name for l in scene.lights]
    assert "Afterburner_Glow" not in light_names


def test_fighter_jet_vfx():
    vfx = fighter_jet_vfx()
    assert "materials" in vfx
    mat_names = [m.name for m in vfx["materials"]]
    assert "JetBody" in mat_names
    assert len(vfx["particles"]) == 1  # Afterburner trail
    assert len(vfx["post"]) == 1


def test_fighter_jet_vfx_no_particles():
    cfg = FighterJetConfig(afterburner_particles=False, fog_density=0)
    vfx = fighter_jet_vfx(cfg)
    assert len(vfx["particles"]) == 0
    assert len(vfx["volumetrics"]) == 0


def test_fighter_jet_mcp_instructions():
    instructions = fighter_jet_mcp_instructions()
    assert "search_sketchfab_models" in instructions
    assert "download_sketchfab_model" in instructions
    assert "Fighter_Jet" in instructions


# --- Point Cloud City ---

def test_point_cloud_city_default():
    scene = point_cloud_city()
    assert isinstance(scene, Scene)
    assert scene.name == "Point_Cloud_City"
    assert scene.frame_end == 240  # 8s * 30fps


def test_point_cloud_city_objects():
    scene = point_cloud_city()
    cam_names = [c.name for c in scene.cameras]
    light_names = [l.name for l in scene.lights]
    assert "FlyThrough_Camera" in cam_names
    assert "Ambient" in light_names


def test_point_cloud_city_vfx():
    vfx = point_cloud_city_vfx()
    mat_names = [m.name for m in vfx["materials"]]
    assert "PointMaterial" in mat_names
    assert len(vfx["post"]) == 1


def test_point_cloud_city_mcp_script():
    script = point_cloud_city_mcp_script()
    assert "ico_sphere_add" in script
    assert "PointMaterial" in script
    assert "PointCloud" in script
    assert "random.seed(42)" in script


def test_point_cloud_city_custom():
    cfg = PointCloudCityConfig(building_count=50, duration_seconds=5.0)
    scene = point_cloud_city(cfg)
    assert scene.frame_end == 150
    script = point_cloud_city_mcp_script(cfg)
    assert "range(50)" in script


# --- Mascot Entrance ---

def test_mascot_entrance_default():
    scene = mascot_entrance()
    assert isinstance(scene, Scene)
    assert scene.name == "Mascot_Entrance"


def test_mascot_entrance_objects():
    scene = mascot_entrance()
    obj_names = [obj.name for obj in scene.objects]
    cam_names = [c.name for c in scene.cameras]
    light_names = [l.name for l in scene.lights]
    assert "Mascot" in obj_names
    assert "Pedestal" in obj_names
    assert "Floor" in obj_names
    assert "Main_Camera" in cam_names
    assert "Key_Light" in light_names
    assert "Rim_Light" in light_names


def test_mascot_entrance_custom_name():
    cfg = MascotEntranceConfig(character_name="Dragon")
    scene = mascot_entrance(cfg)
    names = [obj.name for obj in scene.objects]
    assert "Dragon" in names
    assert "Mascot" not in names


def test_mascot_entrance_vfx():
    vfx = mascot_entrance_vfx()
    assert "materials" in vfx
    assert len(vfx["materials"]) == 3  # Character + Pedestal + Floor
    assert len(vfx["volumetrics"]) == 2  # Fog + Spotlight
    assert len(vfx["particles"]) == 2  # Dust + Explosion burst
    assert len(vfx["post"]) == 1


def test_mascot_entrance_vfx_minimal():
    cfg = MascotEntranceConfig(
        entrance_burst=False,
        fog_density=0,
        spotlight=False,
    )
    vfx = mascot_entrance_vfx(cfg)
    assert len(vfx["volumetrics"]) == 0
    assert len(vfx["particles"]) == 1  # Just ambient dust


# --- Cross-template ---

def test_all_scenes_have_camera():
    scenes = [
        token_reveal(),
        holographic_display(),
        fighter_jet_flyby(),
        point_cloud_city(),
        mascot_entrance(),
    ]
    for scene in scenes:
        assert len(scene.cameras) >= 1, f"Scene {scene.name} has no camera"


def test_all_scenes_serializable():
    scenes = [
        token_reveal(),
        holographic_display(),
        fighter_jet_flyby(),
        point_cloud_city(),
        mascot_entrance(),
    ]
    for scene in scenes:
        d = scene.to_dict()
        assert d["name"] == scene.name
        assert "objects" in d


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
