"""Scene graph — the top-level container for a 3D cinematic scene."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Scene:
    """A composable 3D scene that can be serialized and rendered via Blender."""

    name: str = "Untitled"
    fps: int = 30
    frame_start: int = 1
    frame_end: int = 150  # 5 seconds at 30fps
    resolution_x: int = 1920
    resolution_y: int = 1080
    objects: list[Any] = field(default_factory=list)
    cameras: list[Any] = field(default_factory=list)
    lights: list[Any] = field(default_factory=list)
    world_color: tuple[float, float, float] = (0.01, 0.01, 0.02)
    render_engine: str = "CYCLES"  # CYCLES or BLENDER_EEVEE_NEXT
    render_samples: int = 128
    use_denoising: bool = True

    def add(self, obj: Any) -> "Scene":
        from cinematic_pipeline.core.camera import Camera
        from cinematic_pipeline.core.light import Light

        if isinstance(obj, Camera):
            self.cameras.append(obj)
        elif isinstance(obj, Light):
            self.lights.append(obj)
        else:
            self.objects.append(obj)
        return self

    @property
    def duration_seconds(self) -> float:
        return (self.frame_end - self.frame_start + 1) / self.fps

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "fps": self.fps,
            "frame_start": self.frame_start,
            "frame_end": self.frame_end,
            "resolution": [self.resolution_x, self.resolution_y],
            "world_color": list(self.world_color),
            "render_engine": self.render_engine,
            "render_samples": self.render_samples,
            "use_denoising": self.use_denoising,
            "objects": [o.to_dict() for o in self.objects],
            "cameras": [c.to_dict() for c in self.cameras],
            "lights": [l.to_dict() for l in self.lights],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: dict) -> "Scene":
        scene = cls(
            name=data["name"],
            fps=data["fps"],
            frame_start=data["frame_start"],
            frame_end=data["frame_end"],
            resolution_x=data["resolution"][0],
            resolution_y=data["resolution"][1],
            world_color=tuple(data["world_color"]),
            render_engine=data["render_engine"],
            render_samples=data["render_samples"],
            use_denoising=data["use_denoising"],
        )
        # Object deserialization handled by the Blender bridge
        return scene

    @classmethod
    def load(cls, path: str) -> "Scene":
        with open(path) as f:
            return cls.from_dict(json.load(f))

    def to_blender_script(self) -> str:
        """Generate a Blender Python script that builds this scene."""
        lines = [
            "import bpy",
            "import math",
            "",
            "# Clear existing scene",
            "bpy.ops.object.select_all(action='SELECT')",
            "bpy.ops.object.delete(use_global=False)",
            "",
            f"# Scene settings",
            f"bpy.context.scene.name = {self.name!r}",
            f"bpy.context.scene.render.fps = {self.fps}",
            f"bpy.context.scene.frame_start = {self.frame_start}",
            f"bpy.context.scene.frame_end = {self.frame_end}",
            f"bpy.context.scene.render.resolution_x = {self.resolution_x}",
            f"bpy.context.scene.render.resolution_y = {self.resolution_y}",
            "",
            f"# Render engine",
            f"bpy.context.scene.render.engine = {self.render_engine!r}",
        ]

        if self.render_engine == "CYCLES":
            lines += [
                f"bpy.context.scene.cycles.samples = {self.render_samples}",
                f"bpy.context.scene.cycles.use_denoising = {self.use_denoising}",
                "# Prefer GPU if available",
                "prefs = bpy.context.preferences.addons.get('cycles')",
                "if prefs:",
                "    prefs.preferences.compute_device_type = 'OPTIX'",
                "    bpy.context.scene.cycles.device = 'GPU'",
            ]

        # World background
        r, g, b = self.world_color
        lines += [
            "",
            "# World background",
            "world = bpy.data.worlds.get('World') or bpy.data.worlds.new('World')",
            "bpy.context.scene.world = world",
            "world.use_nodes = True",
            "bg = world.node_tree.nodes.get('Background')",
            f"bg.inputs['Color'].default_value = ({r}, {g}, {b}, 1.0)",
            "",
        ]

        # Add objects
        for obj in self.objects:
            lines.append(f"# Object: {obj.name}")
            lines.append(obj.to_blender_script())
            lines.append("")

        # Add lights
        for light in self.lights:
            lines.append(f"# Light: {light.name}")
            lines.append(light.to_blender_script())
            lines.append("")

        # Add cameras
        for cam in self.cameras:
            lines.append(f"# Camera: {cam.name}")
            lines.append(cam.to_blender_script())
            lines.append("")

        # Set active camera
        if self.cameras:
            lines.append(f"bpy.context.scene.camera = bpy.data.objects[{self.cameras[0].name!r}]")

        return "\n".join(lines)
