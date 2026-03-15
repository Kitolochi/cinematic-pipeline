"""Asset pipeline — model import, HDRI environments, asset library."""

from cinematic_pipeline.assets.model_import import (
    ImportedModel,
    SketchfabModel,
    ModelFormat,
    detect_format,
)
from cinematic_pipeline.assets.hdri import (
    HDRIEnvironment,
    LightingMood,
    MOOD_PRESETS,
    studio_soft,
    studio_dramatic,
    outdoor_sunset,
    outdoor_overcast,
    night_urban,
    dark_void,
    sci_fi_blue,
)
from cinematic_pipeline.assets.library import (
    AssetLibrary,
    AssetMetadata,
)

__all__ = [
    "ImportedModel",
    "SketchfabModel",
    "ModelFormat",
    "detect_format",
    "HDRIEnvironment",
    "LightingMood",
    "MOOD_PRESETS",
    "studio_soft",
    "studio_dramatic",
    "outdoor_sunset",
    "outdoor_overcast",
    "night_urban",
    "dark_void",
    "sci_fi_blue",
    "AssetLibrary",
    "AssetMetadata",
]
