"""Material system using Blender's Principled BSDF."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Material:
    """A PBR material using Blender's Principled BSDF."""

    name: str = "Material"
    base_color: tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0)
    metallic: float = 0.0
    roughness: float = 0.5
    emission_color: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    emission_strength: float = 0.0
    alpha: float = 1.0
    transmission: float = 0.0  # Glass
    ior: float = 1.45

    def to_dict(self) -> dict:
        return {
            "type": "Material",
            "name": self.name,
            "base_color": list(self.base_color),
            "metallic": self.metallic,
            "roughness": self.roughness,
            "emission_color": list(self.emission_color),
            "emission_strength": self.emission_strength,
            "alpha": self.alpha,
            "transmission": self.transmission,
            "ior": self.ior,
        }

    def to_blender_script(self) -> str:
        r, g, b, a = self.base_color
        er, eg, eb, ea = self.emission_color
        lines = [
            f"mat = bpy.data.materials.new({self.name!r})",
            "# Nodes enabled by default in Blender 5.0+",
            "bsdf = mat.node_tree.nodes.get('Principled BSDF')",
            f"bsdf.inputs['Base Color'].default_value = ({r}, {g}, {b}, {a})",
            f"bsdf.inputs['Metallic'].default_value = {self.metallic}",
            f"bsdf.inputs['Roughness'].default_value = {self.roughness}",
        ]

        if self.emission_strength > 0:
            lines += [
                f"bsdf.inputs['Emission Color'].default_value = ({er}, {eg}, {eb}, {ea})",
                f"bsdf.inputs['Emission Strength'].default_value = {self.emission_strength}",
            ]

        if self.alpha < 1.0:
            lines += [
                f"bsdf.inputs['Alpha'].default_value = {self.alpha}",
            ]

        if self.transmission > 0:
            lines += [
                f"bsdf.inputs['Transmission Weight'].default_value = {self.transmission}",
                f"bsdf.inputs['IOR'].default_value = {self.ior}",
            ]

        return "\n".join(lines)


# --- Material Presets ---

def metallic_dark() -> Material:
    return Material(
        name="Metallic_Dark",
        base_color=(0.02, 0.02, 0.03, 1.0),
        metallic=0.9, roughness=0.2,
    )

def holographic_glass() -> Material:
    return Material(
        name="Holographic_Glass",
        base_color=(0.1, 0.3, 0.8, 0.3),
        metallic=0.0, roughness=0.05,
        emission_color=(0.2, 0.5, 1.0, 1.0),
        emission_strength=2.0,
        alpha=0.3, transmission=0.8, ior=1.1,
    )

def neon_emissive(color: tuple[float, float, float] = (0.0, 1.0, 0.25)) -> Material:
    r, g, b = color
    return Material(
        name="Neon_Emissive",
        base_color=(r * 0.1, g * 0.1, b * 0.1, 1.0),
        emission_color=(r, g, b, 1.0),
        emission_strength=5.0,
    )

def matte_white() -> Material:
    return Material(
        name="Matte_White",
        base_color=(0.9, 0.9, 0.92, 1.0),
        metallic=0.0, roughness=0.8,
    )
