"""Volumetric lighting and fog effects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VolumetricFog:
    """Global volumetric fog / atmospheric haze."""

    density: float = 0.02
    color: tuple[float, float, float] = (1.0, 1.0, 1.0)
    anisotropy: float = 0.3  # 0 = uniform scatter, 1 = forward scatter

    def to_blender_script(self) -> str:
        r, g, b = self.color
        return "\n".join([
            "# --- Volumetric Fog ---",
            "world = bpy.context.scene.world",
            "if world:",
            "    nodes = world.node_tree.nodes",
            "    links = world.node_tree.links",
            "    # Create or find volume scatter node",
            "    vol = None",
            "    for n in nodes:",
            "        if n.type == 'VOLUME_SCATTER':",
            "            vol = n",
            "            break",
            "    if not vol:",
            "        vol = nodes.new('ShaderNodeVolumeScatter')",
            f"    vol.inputs['Density'].default_value = {self.density}",
            f"    vol.inputs['Color'].default_value = ({r}, {g}, {b}, 1.0)",
            f"    vol.inputs['Anisotropy'].default_value = {self.anisotropy}",
            "    output = nodes.get('World Output')",
            "    if output:",
            "        links.new(vol.outputs['Volume'], output.inputs['Volume'])",
        ])


@dataclass
class VolumetricSpotlight:
    """A spotlight with visible volumetric cone — god rays effect."""

    name: str = "VolumetricSpot"
    location: tuple[float, float, float] = (0.0, 0.0, 5.0)
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)  # degrees
    energy: float = 500.0
    color: tuple[float, float, float] = (1.0, 0.95, 0.9)
    spot_angle: float = 40.0
    spot_blend: float = 0.3
    shadow_soft_size: float = 0.1
    volume_density: float = 0.05

    def to_dict(self) -> dict:
        return {
            "type": "VolumetricSpotlight",
            "name": self.name,
            "location": list(self.location),
            "rotation": list(self.rotation),
            "energy": self.energy,
            "color": list(self.color),
            "spot_angle": self.spot_angle,
            "volume_density": self.volume_density,
        }

    def to_blender_script(self) -> str:
        x, y, z = self.location
        rx, ry, rz = self.rotation
        r, g, b = self.color

        lines = [
            "# --- Volumetric Spotlight ---",
            f"spot_data = bpy.data.lights.new({self.name!r}, type='SPOT')",
            f"spot_data.energy = {self.energy}",
            f"spot_data.color = ({r}, {g}, {b})",
            f"spot_data.spot_size = math.radians({self.spot_angle})",
            f"spot_data.spot_blend = {self.spot_blend}",
            f"spot_data.shadow_soft_size = {self.shadow_soft_size}",
            "spot_data.use_shadow = True",
            "",
            f"spot_obj = bpy.data.objects.new({self.name!r}, spot_data)",
            "bpy.context.collection.objects.link(spot_obj)",
            f"spot_obj.location = ({x}, {y}, {z})",
            f"spot_obj.rotation_euler = (math.radians({rx}), math.radians({ry}), math.radians({rz}))",
            "",
            "# Enable volumetric cone",
            f"spot_data.use_volumetric_lighting = True" if False else "",  # This is a Cycles-level setting
            "",
            "# World volume scatter (required for visible cones)",
        ]

        # Add fog to make the spotlight cone visible
        fog = VolumetricFog(density=self.volume_density)
        lines.append(fog.to_blender_script())

        return "\n".join(line for line in lines if line is not None)


@dataclass
class GodRays:
    """God rays through geometry — light shafts through windows/openings.

    Creates a spotlight aimed through an opening, with world volume scatter
    to make the rays visible. The 'opening' is any existing geometry with
    holes (windows, door frames, blinds, etc.)
    """

    name: str = "GodRays"
    light_location: tuple[float, float, float] = (0.0, 0.0, 8.0)
    light_rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)
    target_location: tuple[float, float, float] = (0.0, 0.0, 0.0)
    energy: float = 1000.0
    color: tuple[float, float, float] = (1.0, 0.95, 0.85)
    beam_angle: float = 25.0
    volume_density: float = 0.04

    def to_blender_script(self) -> str:
        lx, ly, lz = self.light_location
        tx, ty, tz = self.target_location
        r, g, b = self.color

        lines = [
            "# --- God Rays ---",
            "# Target empty for the light to track",
            f"bpy.ops.object.empty_add(type='PLAIN_AXES', location=({tx}, {ty}, {tz}))",
            "ray_target = bpy.context.active_object",
            f"ray_target.name = '{self.name}_Target'",
            "",
            f"spot_data = bpy.data.lights.new('{self.name}_Light', type='SPOT')",
            f"spot_data.energy = {self.energy}",
            f"spot_data.color = ({r}, {g}, {b})",
            f"spot_data.spot_size = math.radians({self.beam_angle})",
            "spot_data.spot_blend = 0.2",
            "spot_data.shadow_soft_size = 0.05",
            "spot_data.use_shadow = True",
            "",
            f"spot_obj = bpy.data.objects.new('{self.name}_Light', spot_data)",
            "bpy.context.collection.objects.link(spot_obj)",
            f"spot_obj.location = ({lx}, {ly}, {lz})",
            "",
            "# Track to target",
            "track = spot_obj.constraints.new(type='TRACK_TO')",
            "track.target = ray_target",
            "track.track_axis = 'TRACK_NEGATIVE_Z'",
            "track.up_axis = 'UP_Y'",
            "",
            "# Volume scatter for visible rays",
        ]

        fog = VolumetricFog(density=self.volume_density, color=self.color)
        lines.append(fog.to_blender_script())

        return "\n".join(lines)


# --- Presets ---

def dramatic_overhead(
    target: tuple[float, float, float] = (0, 0, 0),
    energy: float = 800,
) -> VolumetricSpotlight:
    """Single dramatic overhead spotlight — noir/interrogation look."""
    return VolumetricSpotlight(
        name="DramaticOverhead",
        location=(target[0], target[1], target[2] + 6),
        rotation=(0, 0, 0),
        energy=energy,
        spot_angle=30,
        volume_density=0.04,
    )


def side_god_rays(
    target: tuple[float, float, float] = (0, 0, 0),
    energy: float = 1200,
) -> GodRays:
    """Side-angle god rays — cathedral/cinematic light shafts."""
    return GodRays(
        name="SideGodRays",
        light_location=(target[0] + 8, target[1] - 3, target[2] + 6),
        target_location=target,
        energy=energy,
        beam_angle=20,
        color=(1.0, 0.92, 0.8),
        volume_density=0.03,
    )
