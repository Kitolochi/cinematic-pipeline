"""Tests for VFX modules — no Blender required."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cinematic_pipeline.vfx.particles import (
    ParticleSystem, EmissionShape,
    ambient_dust, explosion_burst, particle_trail, holographic_dust, sparks,
)
from cinematic_pipeline.vfx.volumetrics import (
    VolumetricFog, VolumetricSpotlight, GodRays,
    dramatic_overhead, side_god_rays,
)
from cinematic_pipeline.vfx.compositing import (
    PostProcessing,
    cinematic_post, clean_tech, sci_fi_glow,
)


# --- Particles ---

def test_particle_system_defaults():
    ps = ParticleSystem()
    assert ps.count == 200
    assert ps.gravity == 0.0
    script = ps.to_blender_script()
    assert "PARTICLE_SYSTEM" in script
    assert "HALO" in script


def test_ambient_dust():
    ps = ambient_dust()
    assert ps.count == 100
    assert ps.gravity == 0.0
    script = ps.to_blender_script()
    assert "DustEmitter" in script
    assert "TURBULENCE" in script


def test_explosion_burst():
    ps = explosion_burst(location=(1, 2, 3), frame=30)
    assert ps.count == 500
    assert ps.frame_start == 30
    assert ps.velocity_normal == 5.0
    script = ps.to_blender_script()
    assert "ExplosionEmitter" in script


def test_particle_trail():
    ps = particle_trail()
    assert ps.lifetime == 30
    script = ps.to_blender_script()
    assert "TrailEmitter" in script


def test_holographic_dust():
    ps = holographic_dust()
    assert ps.count == 60
    assert ps.emission_strength == 2.5


def test_sparks():
    ps = sparks(frame=50)
    assert ps.frame_start == 50
    assert ps.gravity == 0.8


def test_particle_serialization():
    ps = ambient_dust()
    d = ps.to_dict()
    assert d["type"] == "ParticleSystem"
    assert d["count"] == 100


# --- Volumetrics ---

def test_volumetric_fog():
    fog = VolumetricFog(density=0.05)
    script = fog.to_blender_script()
    assert "Volume Scatter" in script or "VolumeScatter" in script
    assert "0.05" in script


def test_volumetric_spotlight():
    spot = VolumetricSpotlight(energy=500, spot_angle=30)
    script = spot.to_blender_script()
    assert "SPOT" in script
    assert "500" in script


def test_god_rays():
    rays = GodRays(energy=1000)
    script = rays.to_blender_script()
    assert "TRACK_TO" in script
    assert "SPOT" in script


def test_dramatic_overhead():
    spot = dramatic_overhead(target=(0, 0, 0))
    assert spot.location[2] == 6  # 6 meters above target
    assert spot.spot_angle == 30


def test_side_god_rays():
    rays = side_god_rays()
    script = rays.to_blender_script()
    assert "SideGodRays" in script


# --- Compositing ---

def test_post_processing_defaults():
    pp = PostProcessing()
    script = pp.to_blender_script()
    assert "CompositorNodeRLayers" in script
    assert "NodeGroupOutput" in script  # Blender 5.0 uses group output


def test_cinematic_post():
    pp = cinematic_post()
    script = pp.to_blender_script()
    assert "Glare" in script or "glare" in script.lower()
    assert "EllipseMask" in script
    assert "Lensdist" in script  # chromatic aberration


def test_clean_tech():
    pp = clean_tech()
    assert pp.chromatic_aberration is False
    script = pp.to_blender_script()
    assert "Lensdist" not in script


def test_sci_fi_glow():
    pp = sci_fi_glow()
    assert pp.glare_enabled is True
    assert pp.glare_type == "STREAKS"
    script = pp.to_blender_script()
    assert "Streaks" in script  # Blender 5.0 uses title case for menu values


def test_post_no_bloom():
    pp = PostProcessing(bloom_enabled=False, glare_enabled=False)
    script = pp.to_blender_script()
    assert "Glare" not in script


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
