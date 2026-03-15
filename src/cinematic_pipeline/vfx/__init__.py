"""Visual effects — particles, volumetrics, post-processing."""

from cinematic_pipeline.vfx.particles import (
    ParticleSystem, ParticlePreset, EmissionShape,
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

__all__ = [
    "ParticleSystem", "ParticlePreset", "EmissionShape",
    "ambient_dust", "explosion_burst", "particle_trail", "holographic_dust", "sparks",
    "VolumetricFog", "VolumetricSpotlight", "GodRays",
    "dramatic_overhead", "side_god_rays",
    "PostProcessing",
    "cinematic_post", "clean_tech", "sci_fi_glow",
]
