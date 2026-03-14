"""Camera system with cinematic presets."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CameraPreset(Enum):
    """Pre-built cinematic camera movements."""
    STATIC = "static"
    ORBIT = "orbit"               # Circle around a target
    DOLLY_IN = "dolly_in"         # Push toward target
    DOLLY_OUT = "dolly_out"       # Pull away from target
    CRANE_UP = "crane_up"         # Rise upward while looking at target
    CRANE_DOWN = "crane_down"     # Lower while looking at target
    TRACKING = "tracking"         # Follow a path alongside target
    HANDHELD = "handheld"         # Subtle noise-based shake


@dataclass
class Camera:
    """A camera with optional cinematic animation preset."""

    name: str = "Camera"
    location: tuple[float, float, float] = (0.0, -5.0, 2.0)
    rotation: tuple[float, float, float] = (70.0, 0.0, 0.0)  # degrees
    focal_length: float = 50.0  # mm
    sensor_width: float = 36.0  # mm (full frame)
    dof_enabled: bool = False
    dof_focus_distance: float = 5.0
    dof_aperture: float = 2.8  # f-stop
    dof_focus_target: str | None = None  # Object name to focus on
    preset: CameraPreset = CameraPreset.STATIC
    preset_params: dict[str, Any] = field(default_factory=dict)
    track_target: str | None = None  # Object name to always look at
    keyframes: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": "Camera",
            "name": self.name,
            "location": list(self.location),
            "rotation": list(self.rotation),
            "focal_length": self.focal_length,
            "sensor_width": self.sensor_width,
            "dof_enabled": self.dof_enabled,
            "dof_focus_distance": self.dof_focus_distance,
            "dof_aperture": self.dof_aperture,
            "dof_focus_target": self.dof_focus_target,
            "preset": self.preset.value,
            "preset_params": self.preset_params,
            "track_target": self.track_target,
            "keyframes": [k.to_dict() for k in self.keyframes],
        }

    def to_blender_script(self) -> str:
        x, y, z = self.location
        rx, ry, rz = self.rotation
        lines = [
            f"cam_data = bpy.data.cameras.new({self.name!r})",
            f"cam_data.lens = {self.focal_length}",
            f"cam_data.sensor_width = {self.sensor_width}",
        ]

        if self.dof_enabled:
            lines += [
                "cam_data.dof.use_dof = True",
                f"cam_data.dof.focus_distance = {self.dof_focus_distance}",
                f"cam_data.dof.aperture_fstop = {self.dof_aperture}",
            ]
            if self.dof_focus_target:
                lines.append(
                    f"cam_data.dof.focus_object = bpy.data.objects.get({self.dof_focus_target!r})"
                )

        lines += [
            f"cam_obj = bpy.data.objects.new({self.name!r}, cam_data)",
            "bpy.context.collection.objects.link(cam_obj)",
            f"cam_obj.location = ({x}, {y}, {z})",
            f"cam_obj.rotation_euler = (math.radians({rx}), math.radians({ry}), math.radians({rz}))",
        ]

        # Track-to constraint
        if self.track_target:
            lines += [
                "track = cam_obj.constraints.new(type='TRACK_TO')",
                f"track.target = bpy.data.objects.get({self.track_target!r})",
                "track.track_axis = 'TRACK_NEGATIVE_Z'",
                "track.up_axis = 'UP_Y'",
            ]

        # Camera presets
        if self.preset == CameraPreset.ORBIT:
            lines += self._orbit_script()
        elif self.preset == CameraPreset.DOLLY_IN:
            lines += self._dolly_script(direction="in")
        elif self.preset == CameraPreset.DOLLY_OUT:
            lines += self._dolly_script(direction="out")
        elif self.preset == CameraPreset.CRANE_UP:
            lines += self._crane_script(direction="up")
        elif self.preset == CameraPreset.CRANE_DOWN:
            lines += self._crane_script(direction="down")
        elif self.preset == CameraPreset.HANDHELD:
            lines += self._handheld_script()

        # Manual keyframes
        for kf in self.keyframes:
            lines.append(kf.to_blender_script("cam_obj"))

        return "\n".join(lines)

    def _orbit_script(self) -> list[str]:
        radius = self.preset_params.get("radius", 5.0)
        height = self.preset_params.get("height", 2.0)
        revolutions = self.preset_params.get("revolutions", 1.0)
        return [
            "",
            "# Orbit: parent camera to rotating empty",
            "orbit_empty = bpy.data.objects.new('_orbit_pivot', None)",
            "bpy.context.collection.objects.link(orbit_empty)",
            f"cam_obj.parent = orbit_empty",
            f"cam_obj.location = ({radius}, 0, {height})",
            "cam_obj.rotation_euler = (0, 0, 0)",
            f"orbit_empty.rotation_euler = (0, 0, 0)",
            f"orbit_empty.keyframe_insert(data_path='rotation_euler', frame=bpy.context.scene.frame_start)",
            f"orbit_empty.rotation_euler = (0, 0, math.radians({360 * revolutions}))",
            f"orbit_empty.keyframe_insert(data_path='rotation_euler', frame=bpy.context.scene.frame_end)",
            "# Smooth interpolation",
            "for fc in orbit_empty.animation_data.action.fcurves:",
            "    for kp in fc.keyframe_points:",
            "        kp.interpolation = 'BEZIER'",
            "        kp.easing = 'EASE_IN_OUT'",
        ]

    def _dolly_script(self, direction: str) -> list[str]:
        distance = self.preset_params.get("distance", 3.0)
        sign = -1 if direction == "in" else 1
        x, y, z = self.location
        return [
            "",
            f"# Dolly {direction}",
            f"cam_obj.keyframe_insert(data_path='location', frame=bpy.context.scene.frame_start)",
            f"cam_obj.location.y += {sign * distance}",
            f"cam_obj.keyframe_insert(data_path='location', frame=bpy.context.scene.frame_end)",
            "for fc in cam_obj.animation_data.action.fcurves:",
            "    for kp in fc.keyframe_points:",
            "        kp.interpolation = 'BEZIER'",
            "        kp.easing = 'EASE_IN_OUT'",
        ]

    def _crane_script(self, direction: str) -> list[str]:
        height = self.preset_params.get("height", 3.0)
        sign = 1 if direction == "up" else -1
        return [
            "",
            f"# Crane {direction}",
            f"cam_obj.keyframe_insert(data_path='location', frame=bpy.context.scene.frame_start)",
            f"cam_obj.location.z += {sign * height}",
            f"cam_obj.keyframe_insert(data_path='location', frame=bpy.context.scene.frame_end)",
            "for fc in cam_obj.animation_data.action.fcurves:",
            "    for kp in fc.keyframe_points:",
            "        kp.interpolation = 'BEZIER'",
            "        kp.easing = 'EASE_IN_OUT'",
        ]

    def _handheld_script(self) -> list[str]:
        intensity = self.preset_params.get("intensity", 0.02)
        return [
            "",
            "# Handheld shake via noise modifier on f-curves",
            "cam_obj.keyframe_insert(data_path='location', frame=1)",
            "cam_obj.keyframe_insert(data_path='rotation_euler', frame=1)",
            "action = cam_obj.animation_data.action",
            "for fc in action.fcurves:",
            "    mod = fc.modifiers.new(type='NOISE')",
            f"    mod.strength = {intensity}",
            "    mod.scale = 3.0",
            "    mod.phase = fc.array_index * 17.3",
        ]
