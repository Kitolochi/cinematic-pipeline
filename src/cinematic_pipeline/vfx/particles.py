"""Particle system API — ambient dust, explosions, trails."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EmissionShape(Enum):
    SPHERE = "sphere"
    BOX = "box"
    PLANE = "plane"
    RING = "ring"
    POINT = "point"


class ParticlePreset(Enum):
    AMBIENT_DUST = "ambient_dust"
    EXPLOSION = "explosion"
    TRAIL = "trail"
    HOLOGRAPHIC_DUST = "holographic_dust"
    SPARKS = "sparks"


@dataclass
class ParticleSystem:
    """A particle system attached to an emitter object."""

    name: str = "Particles"
    emitter_name: str = "ParticleEmitter"
    count: int = 200
    lifetime: int = 100  # frames
    frame_start: int = 1
    frame_end: int = 150
    emission_shape: EmissionShape = EmissionShape.SPHERE
    emission_radius: float = 3.0
    size: float = 0.02
    size_random: float = 0.5
    velocity_normal: float = 0.0
    velocity_random: float = 0.5
    gravity: float = 0.0  # 0 = floating, 1 = normal gravity
    turbulence_strength: float = 0.5
    turbulence_scale: float = 1.0
    color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    emission_strength: float = 2.0  # glow intensity
    fade_in: int = 10  # frames to fade in
    fade_out: int = 20  # frames to fade out
    location: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def to_dict(self) -> dict:
        return {
            "type": "ParticleSystem",
            "name": self.name,
            "emitter_name": self.emitter_name,
            "count": self.count,
            "lifetime": self.lifetime,
            "emission_shape": self.emission_shape.value,
            "emission_radius": self.emission_radius,
            "size": self.size,
            "color": list(self.color),
            "emission_strength": self.emission_strength,
            "gravity": self.gravity,
            "location": list(self.location),
        }

    def to_blender_script(self) -> str:
        r, g, b, a = self.color
        x, y, z = self.location

        # Create emitter mesh based on emission shape
        shape_ops = {
            EmissionShape.SPHERE: f"bpy.ops.mesh.primitive_ico_sphere_add(radius={self.emission_radius}, location=({x}, {y}, {z}))",
            EmissionShape.BOX: f"bpy.ops.mesh.primitive_cube_add(size={self.emission_radius * 2}, location=({x}, {y}, {z}))",
            EmissionShape.PLANE: f"bpy.ops.mesh.primitive_plane_add(size={self.emission_radius * 2}, location=({x}, {y}, {z}))",
            EmissionShape.RING: f"bpy.ops.mesh.primitive_torus_add(major_radius={self.emission_radius}, minor_radius=0.01, location=({x}, {y}, {z}))",
            EmissionShape.POINT: f"bpy.ops.mesh.primitive_ico_sphere_add(radius=0.01, location=({x}, {y}, {z}))",
        }

        lines = [
            "# --- Particle System ---",
            f"# Create emitter: {self.emitter_name}",
            shape_ops[self.emission_shape],
            "emitter = bpy.context.active_object",
            f"emitter.name = {self.emitter_name!r}",
            "emitter.hide_render = True",
            "emitter.display_type = 'WIRE'",
            "",
            "# Particle material (emissive)",
            f"pmat = bpy.data.materials.new({self.name + '_Mat'!r})",
            "pmat_bsdf = pmat.node_tree.nodes.get('Principled BSDF')",
            f"pmat_bsdf.inputs['Base Color'].default_value = ({r}, {g}, {b}, {a})",
            f"pmat_bsdf.inputs['Emission Color'].default_value = ({r}, {g}, {b}, {a})",
            f"pmat_bsdf.inputs['Emission Strength'].default_value = {self.emission_strength}",
            "",
            "# Add particle system",
            "mod = emitter.modifiers.new(name={name!r}, type='PARTICLE_SYSTEM')".format(name=self.name),
            "psys = mod.particle_system",
            "ps = psys.settings",
            f"ps.count = {self.count}",
            f"ps.lifetime = {self.lifetime}",
            f"ps.frame_start = {self.frame_start}",
            f"ps.frame_end = {self.frame_end}",
            "",
            "# Physics",
            f"ps.normal_factor = {self.velocity_normal}",
            f"ps.factor_random = {self.velocity_random}",
            f"ps.effector_weights.gravity = {self.gravity}",
            "",
            "# Size",
            f"ps.particle_size = {self.size}",
            f"ps.size_random = {self.size_random}",
            "",
            "# Render as halo",
            "ps.render_type = 'HALO'",
            "",
            "# Material",
            "emitter.data.materials.append(pmat)",
        ]

        # Turbulence field
        if self.turbulence_strength > 0:
            lines += [
                "",
                "# Turbulence force field",
                "bpy.ops.object.effector_add(type='TURBULENCE', location=({}, {}, {}))".format(x, y, z),
                "turb = bpy.context.active_object",
                f"turb.name = '{self.emitter_name}_Turbulence'",
                f"turb.field.strength = {self.turbulence_strength}",
                f"turb.field.noise = {self.turbulence_scale}",
                f"turb.field.flow = 1.0",
            ]

        return "\n".join(lines)


# --- Presets ---

def ambient_dust(
    location: tuple[float, float, float] = (0, 0, 0),
    count: int = 100,
    radius: float = 5.0,
    color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 0.6),
) -> ParticleSystem:
    """Floating ambient dust particles — Kinetiq holographic atmosphere."""
    return ParticleSystem(
        name="AmbientDust",
        emitter_name="DustEmitter",
        count=count,
        lifetime=200,
        emission_shape=EmissionShape.SPHERE,
        emission_radius=radius,
        size=0.008,
        size_random=0.7,
        velocity_normal=0.0,
        velocity_random=0.2,
        gravity=0.0,
        turbulence_strength=0.3,
        turbulence_scale=2.0,
        color=color,
        emission_strength=1.5,
        location=location,
    )


def explosion_burst(
    location: tuple[float, float, float] = (0, 0, 0),
    count: int = 500,
    color: tuple[float, float, float, float] = (1.0, 0.7, 0.2, 1.0),
    frame: int = 1,
) -> ParticleSystem:
    """Explosive burst — fast outward motion, short lifetime, gravity."""
    return ParticleSystem(
        name="Explosion",
        emitter_name="ExplosionEmitter",
        count=count,
        lifetime=40,
        frame_start=frame,
        frame_end=frame + 5,
        emission_shape=EmissionShape.POINT,
        emission_radius=0.1,
        size=0.03,
        size_random=0.5,
        velocity_normal=5.0,
        velocity_random=2.0,
        gravity=0.3,
        turbulence_strength=1.0,
        color=color,
        emission_strength=8.0,
        location=location,
    )


def particle_trail(
    start: tuple[float, float, float] = (0, 0, 0),
    color: tuple[float, float, float, float] = (0.3, 0.6, 1.0, 1.0),
    count: int = 300,
) -> ParticleSystem:
    """Trail particles — follow behind a moving object."""
    return ParticleSystem(
        name="Trail",
        emitter_name="TrailEmitter",
        count=count,
        lifetime=30,
        emission_shape=EmissionShape.POINT,
        emission_radius=0.05,
        size=0.015,
        size_random=0.4,
        velocity_normal=0.1,
        velocity_random=0.3,
        gravity=0.0,
        turbulence_strength=0.2,
        color=color,
        emission_strength=3.0,
        location=start,
    )


def holographic_dust(
    location: tuple[float, float, float] = (0, 0, 0),
    color: tuple[float, float, float, float] = (0.2, 0.5, 1.0, 0.5),
) -> ParticleSystem:
    """Kinetiq-style holographic floating particles — blue tint, low density."""
    return ParticleSystem(
        name="HoloDust",
        emitter_name="HoloDustEmitter",
        count=60,
        lifetime=300,
        emission_shape=EmissionShape.SPHERE,
        emission_radius=4.0,
        size=0.005,
        size_random=0.8,
        velocity_normal=0.0,
        velocity_random=0.1,
        gravity=0.0,
        turbulence_strength=0.15,
        turbulence_scale=3.0,
        color=color,
        emission_strength=2.5,
        location=location,
    )


def sparks(
    location: tuple[float, float, float] = (0, 0, 0),
    count: int = 200,
    frame: int = 1,
) -> ParticleSystem:
    """Sparks — bright, fast, with gravity and bounce."""
    return ParticleSystem(
        name="Sparks",
        emitter_name="SparkEmitter",
        count=count,
        lifetime=25,
        frame_start=frame,
        frame_end=frame + 3,
        emission_shape=EmissionShape.POINT,
        emission_radius=0.05,
        size=0.01,
        size_random=0.3,
        velocity_normal=8.0,
        velocity_random=3.0,
        gravity=0.8,
        turbulence_strength=0.5,
        color=(1.0, 0.85, 0.3, 1.0),
        emission_strength=12.0,
        location=location,
    )
