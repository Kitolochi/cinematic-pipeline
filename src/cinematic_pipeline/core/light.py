"""Lighting system with cinematic presets."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LightType(Enum):
    POINT = "POINT"
    SUN = "SUN"
    SPOT = "SPOT"
    AREA = "AREA"


@dataclass
class Light:
    """A light source."""

    name: str = "Light"
    light_type: LightType = LightType.POINT
    location: tuple[float, float, float] = (0.0, 0.0, 3.0)
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)
    color: tuple[float, float, float] = (1.0, 1.0, 1.0)
    energy: float = 100.0
    size: float = 0.5  # For area/spot soft shadows
    spot_angle: float = 45.0  # degrees, spot only
    spot_blend: float = 0.15  # spot only
    use_shadow: bool = True
    volumetric: bool = False  # Enable volumetric cone
    keyframes: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": "Light",
            "name": self.name,
            "light_type": self.light_type.value,
            "location": list(self.location),
            "rotation": list(self.rotation),
            "color": list(self.color),
            "energy": self.energy,
            "size": self.size,
            "use_shadow": self.use_shadow,
            "volumetric": self.volumetric,
        }

    def to_blender_script(self) -> str:
        x, y, z = self.location
        rx, ry, rz = self.rotation
        r, g, b = self.color
        lines = [
            f"light_data = bpy.data.lights.new({self.name!r}, type={self.light_type.value!r})",
            f"light_data.color = ({r}, {g}, {b})",
            f"light_data.energy = {self.energy}",
            f"light_data.use_shadow = {self.use_shadow}",
        ]

        if self.light_type in (LightType.AREA, LightType.SPOT):
            lines.append(f"light_data.shadow_soft_size = {self.size}")

        if self.light_type == LightType.SPOT:
            lines += [
                f"light_data.spot_size = math.radians({self.spot_angle})",
                f"light_data.spot_blend = {self.spot_blend}",
            ]

        lines += [
            f"light_obj = bpy.data.objects.new({self.name!r}, light_data)",
            "bpy.context.collection.objects.link(light_obj)",
            f"light_obj.location = ({x}, {y}, {z})",
            f"light_obj.rotation_euler = (math.radians({rx}), math.radians({ry}), math.radians({rz}))",
        ]

        if self.volumetric:
            lines += [
                "",
                "# Volumetric: ensure world has volume scatter",
                "world = bpy.context.scene.world",
                "if world and world.use_nodes:",
                "    nodes = world.node_tree.nodes",
                "    links = world.node_tree.links",
                "    vol = nodes.get('Volume Scatter') or nodes.new('ShaderNodeVolumeScatter')",
                "    vol.inputs['Density'].default_value = 0.02",
                "    vol.inputs['Color'].default_value = (1, 1, 1, 1)",
                "    output = nodes.get('World Output')",
                "    links.new(vol.outputs['Volume'], output.inputs['Volume'])",
            ]

        for kf in self.keyframes:
            lines.append(kf.to_blender_script("light_obj"))

        return "\n".join(lines)


# --- Lighting Rig Presets ---

def three_point_rig(
    target_location: tuple[float, float, float] = (0, 0, 0),
    key_energy: float = 200,
) -> list[Light]:
    """Classic three-point lighting setup."""
    tx, ty, tz = target_location
    return [
        Light(
            name="Key_Light", light_type=LightType.AREA,
            location=(tx + 3, ty - 3, tz + 4), rotation=(55, 0, 45),
            energy=key_energy, size=1.0,
        ),
        Light(
            name="Fill_Light", light_type=LightType.AREA,
            location=(tx - 3, ty - 2, tz + 2), rotation=(40, 0, -30),
            energy=key_energy * 0.3, size=1.5,
        ),
        Light(
            name="Rim_Light", light_type=LightType.AREA,
            location=(tx - 1, ty + 3, tz + 3), rotation=(30, 0, 180),
            energy=key_energy * 0.6, size=0.5,
        ),
    ]


def dramatic_side_rig(
    target_location: tuple[float, float, float] = (0, 0, 0),
    energy: float = 300,
    color: tuple[float, float, float] = (1.0, 0.9, 0.8),
) -> list[Light]:
    """Strong side light with minimal fill — noir/cinematic look."""
    tx, ty, tz = target_location
    return [
        Light(
            name="Side_Key", light_type=LightType.SPOT,
            location=(tx + 4, ty, tz + 2), rotation=(10, 0, 90),
            energy=energy, color=color, spot_angle=35, spot_blend=0.3,
        ),
        Light(
            name="Faint_Fill", light_type=LightType.AREA,
            location=(tx - 3, ty - 1, tz + 1), rotation=(20, 0, -45),
            energy=energy * 0.05, size=2.0,
        ),
    ]


def neon_accent_rig(
    target_location: tuple[float, float, float] = (0, 0, 0),
    accent_color: tuple[float, float, float] = (0.0, 0.5, 1.0),
    energy: float = 150,
) -> list[Light]:
    """Cyberpunk-style colored accent lights."""
    tx, ty, tz = target_location
    return [
        Light(
            name="Neon_Left", light_type=LightType.AREA,
            location=(tx - 3, ty - 1, tz + 1), rotation=(10, 0, -45),
            energy=energy, color=accent_color, size=0.5,
        ),
        Light(
            name="Neon_Right", light_type=LightType.AREA,
            location=(tx + 3, ty - 1, tz + 1), rotation=(10, 0, 45),
            energy=energy, color=(accent_color[0] * 0.3, accent_color[1] * 0.3, accent_color[2] * 0.3), size=0.5,
        ),
        Light(
            name="Top_Fill", light_type=LightType.AREA,
            location=(tx, ty, tz + 4), rotation=(90, 0, 0),
            energy=energy * 0.2, size=2.0,
        ),
    ]
