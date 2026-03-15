"""Scene templates -- pre-built Kinetiq-style shot types."""

from cinematic_pipeline.templates.token_reveal import (
    TokenRevealConfig,
    token_reveal,
    token_reveal_vfx,
    token_reveal_mcp_script,
)
from cinematic_pipeline.templates.holographic_display import (
    HolographicDisplayConfig,
    HoloPanelConfig,
    holographic_display,
    holographic_display_vfx,
    holographic_display_mcp_script,
)
from cinematic_pipeline.templates.fighter_jet import (
    FighterJetConfig,
    fighter_jet_flyby,
    fighter_jet_vfx,
    fighter_jet_mcp_instructions,
)
from cinematic_pipeline.templates.point_cloud_city import (
    PointCloudCityConfig,
    point_cloud_city,
    point_cloud_city_vfx,
    point_cloud_city_mcp_script,
)
from cinematic_pipeline.templates.mascot_entrance import (
    MascotEntranceConfig,
    mascot_entrance,
    mascot_entrance_vfx,
)

__all__ = [
    "TokenRevealConfig",
    "token_reveal",
    "token_reveal_vfx",
    "token_reveal_mcp_script",
    "HolographicDisplayConfig",
    "HoloPanelConfig",
    "holographic_display",
    "holographic_display_vfx",
    "holographic_display_mcp_script",
    "FighterJetConfig",
    "fighter_jet_flyby",
    "fighter_jet_vfx",
    "fighter_jet_mcp_instructions",
    "PointCloudCityConfig",
    "point_cloud_city",
    "point_cloud_city_vfx",
    "point_cloud_city_mcp_script",
    "MascotEntranceConfig",
    "mascot_entrance",
    "mascot_entrance_vfx",
]
