"""HDRI environment and lighting mood presets.

Uses Poly Haven HDRIs (CC0) via Blender MCP or direct download.
Generates Blender Python scripts to set world environment.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HDRIEnvironment:
    """World environment using an HDRI image."""

    hdri_path: str = ""       # Local file path to .hdr/.exr
    polyhaven_id: str = ""    # Poly Haven asset ID (e.g., "studio_small_09")
    resolution: str = "2k"    # 1k, 2k, 4k
    strength: float = 1.0     # Environment light intensity
    rotation_z: float = 0.0   # Rotate environment (degrees)
    use_background: bool = True  # Show HDRI as visible background

    def to_dict(self) -> dict:
        return {
            "type": "HDRIEnvironment",
            "hdri_path": self.hdri_path,
            "polyhaven_id": self.polyhaven_id,
            "resolution": self.resolution,
            "strength": self.strength,
            "rotation_z": self.rotation_z,
        }

    def to_blender_script(self) -> str:
        """Generate Blender script to set HDRI as world environment."""
        if not self.hdri_path:
            return f"# HDRI: use MCP download_polyhaven_asset('{self.polyhaven_id}', 'hdris', '{self.resolution}')"

        path = self.hdri_path.replace("\\", "/")
        lines = [
            f"# --- HDRI Environment: {self.polyhaven_id or self.hdri_path} ---",
            "import math",
            "",
            "world = bpy.context.scene.world",
            "if not world:",
            "    world = bpy.data.worlds.new('World')",
            "    bpy.context.scene.world = world",
            "",
            "nodes = world.node_tree.nodes",
            "links = world.node_tree.links",
            "nodes.clear()",
            "",
            "# Environment texture",
            "tex_coord = nodes.new('ShaderNodeTexCoord')",
            "tex_coord.location = (-600, 0)",
            "",
            "mapping = nodes.new('ShaderNodeMapping')",
            "mapping.location = (-400, 0)",
            f"mapping.inputs['Rotation'].default_value = (0, 0, math.radians({self.rotation_z}))",
            "",
            "env_tex = nodes.new('ShaderNodeTexEnvironment')",
            "env_tex.location = (-200, 0)",
            f"env_tex.image = bpy.data.images.load({path!r})",
            "",
            "bg = nodes.new('ShaderNodeBackground')",
            "bg.location = (0, 0)",
            f"bg.inputs['Strength'].default_value = {self.strength}",
            "",
            "output = nodes.new('ShaderNodeOutputWorld')",
            "output.location = (200, 0)",
            "",
            "links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])",
            "links.new(mapping.outputs['Vector'], env_tex.inputs['Vector'])",
            "links.new(env_tex.outputs['Color'], bg.inputs['Color'])",
            "links.new(bg.outputs['Background'], output.inputs['Surface'])",
        ]

        if not self.use_background:
            lines += [
                "",
                "# Hide HDRI from camera (lighting only)",
                "world.cycles_visibility.camera = False",
            ]

        return "\n".join(lines)


# --- Mood Presets ---

@dataclass
class LightingMood:
    """Complete lighting mood: HDRI + optional light overrides."""

    name: str
    hdri: HDRIEnvironment
    description: str = ""
    world_color: tuple[float, float, float] = (0.0, 0.0, 0.0)  # Fallback if no HDRI

    def to_dict(self) -> dict:
        return {
            "type": "LightingMood",
            "name": self.name,
            "description": self.description,
            "hdri": self.hdri.to_dict(),
        }

    def to_blender_script(self) -> str:
        if self.hdri.hdri_path:
            return self.hdri.to_blender_script()
        # Solid color fallback
        r, g, b = self.world_color
        return "\n".join([
            f"# --- Lighting Mood: {self.name} (solid color fallback) ---",
            "world = bpy.context.scene.world",
            "if not world:",
            "    world = bpy.data.worlds.new('World')",
            "    bpy.context.scene.world = world",
            "bg = world.node_tree.nodes.get('Background')",
            f"bg.inputs['Color'].default_value = ({r}, {g}, {b}, 1.0)",
            f"bg.inputs['Strength'].default_value = {self.hdri.strength}",
        ])


# --- Poly Haven HDRI Presets ---
# These use polyhaven_id — download via MCP before using to_blender_script

def studio_soft() -> LightingMood:
    """Soft studio lighting — even, diffuse, product photography."""
    return LightingMood(
        name="Studio Soft",
        description="Even studio lighting for product shots",
        hdri=HDRIEnvironment(polyhaven_id="studio_small_09", strength=1.0),
    )


def studio_dramatic() -> LightingMood:
    """Dramatic studio — strong key, deep shadows."""
    return LightingMood(
        name="Studio Dramatic",
        description="Dramatic studio with strong directional light",
        hdri=HDRIEnvironment(polyhaven_id="photo_studio_loft_hall", strength=1.5),
    )


def outdoor_sunset() -> LightingMood:
    """Golden hour sunset — warm, cinematic."""
    return LightingMood(
        name="Outdoor Sunset",
        description="Warm golden hour lighting",
        hdri=HDRIEnvironment(polyhaven_id="kloofendal_48d_partly_cloudy_puresky", strength=0.8),
    )


def outdoor_overcast() -> LightingMood:
    """Overcast sky — soft, even, no harsh shadows."""
    return LightingMood(
        name="Outdoor Overcast",
        description="Soft overcast sky, even lighting",
        hdri=HDRIEnvironment(polyhaven_id="kloofendal_overcast_puresky", strength=0.6),
    )


def night_urban() -> LightingMood:
    """Night cityscape — dark with colored artificial light."""
    return LightingMood(
        name="Night Urban",
        description="Dark night with city lights and neon",
        hdri=HDRIEnvironment(polyhaven_id="leadenhall_market", strength=0.3),
    )


def dark_void() -> LightingMood:
    """Pure dark void — no environment, lights only."""
    return LightingMood(
        name="Dark Void",
        description="Pure black background, lighting from scene lights only",
        hdri=HDRIEnvironment(strength=0.0),
        world_color=(0.003, 0.003, 0.008),
    )


def sci_fi_blue() -> LightingMood:
    """Dark sci-fi blue ambient — cyberpunk / tech aesthetic."""
    return LightingMood(
        name="Sci-Fi Blue",
        description="Dark blue ambient for tech/cyberpunk scenes",
        hdri=HDRIEnvironment(strength=0.05),
        world_color=(0.005, 0.01, 0.03),
    )


# All presets for easy iteration
MOOD_PRESETS = {
    "studio_soft": studio_soft,
    "studio_dramatic": studio_dramatic,
    "outdoor_sunset": outdoor_sunset,
    "outdoor_overcast": outdoor_overcast,
    "night_urban": night_urban,
    "dark_void": dark_void,
    "sci_fi_blue": sci_fi_blue,
}
