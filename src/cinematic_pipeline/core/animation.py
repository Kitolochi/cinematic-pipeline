"""Keyframe animation system."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Keyframe:
    """A single keyframe on an object property."""

    frame: int
    property: str  # "location", "rotation_euler", "scale", or custom path
    value: tuple[float, ...] | float
    interpolation: str = "BEZIER"  # BEZIER, LINEAR, CONSTANT
    easing: str = "EASE_IN_OUT"  # AUTO, EASE_IN, EASE_OUT, EASE_IN_OUT

    def to_dict(self) -> dict:
        return {
            "frame": self.frame,
            "property": self.property,
            "value": list(self.value) if isinstance(self.value, tuple) else self.value,
            "interpolation": self.interpolation,
            "easing": self.easing,
        }

    def to_blender_script(self, var: str = "obj") -> str:
        lines = []
        if isinstance(self.value, (tuple, list)):
            vals = ", ".join(str(v) for v in self.value)
            if self.property == "rotation_euler":
                vals = ", ".join(f"math.radians({v})" for v in self.value)
            lines.append(f"{var}.{self.property} = ({vals})")
        else:
            lines.append(f"{var}.{self.property} = {self.value}")

        lines.append(
            f"{var}.keyframe_insert(data_path={self.property!r}, frame={self.frame})"
        )

        # Set interpolation on the just-inserted keyframe
        lines += [
            f"if {var}.animation_data and {var}.animation_data.action:",
            f"    for fc in {var}.animation_data.action.fcurves:",
            f"        if fc.data_path == {self.property!r}:",
            f"            for kp in fc.keyframe_points:",
            f"                if kp.co.x == {self.frame}:",
            f"                    kp.interpolation = {self.interpolation!r}",
            f"                    kp.easing = {self.easing!r}",
        ]
        return "\n".join(lines)


@dataclass
class AnimationPath:
    """A sequence of keyframes forming a complete animation on one object."""

    target_name: str
    keyframes: list[Keyframe]

    def to_dict(self) -> dict:
        return {
            "target_name": self.target_name,
            "keyframes": [k.to_dict() for k in self.keyframes],
        }

    def to_blender_script(self) -> str:
        lines = [
            f"anim_target = bpy.data.objects[{self.target_name!r}]",
        ]
        for kf in self.keyframes:
            lines.append(kf.to_blender_script("anim_target"))
        return "\n".join(lines)
