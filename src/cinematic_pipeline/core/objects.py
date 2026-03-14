"""3D objects — meshes, empties, and imported models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PrimitiveType(Enum):
    CUBE = "cube"
    SPHERE = "sphere"
    CYLINDER = "cylinder"
    PLANE = "plane"
    CONE = "cone"
    TORUS = "torus"
    MONKEY = "monkey"  # Suzanne — useful for testing


@dataclass
class Object3D:
    """Base class for all 3D objects in a scene."""

    name: str = "Object"
    location: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)  # degrees
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0)
    material_name: str | None = None
    parent: str | None = None
    keyframes: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "name": self.name,
            "location": list(self.location),
            "rotation": list(self.rotation),
            "scale": list(self.scale),
            "material_name": self.material_name,
            "parent": self.parent,
            "keyframes": [k.to_dict() for k in self.keyframes],
        }

    def _transform_script(self, var: str = "obj") -> str:
        x, y, z = self.location
        rx, ry, rz = self.rotation
        sx, sy, sz = self.scale
        lines = [
            f"{var}.location = ({x}, {y}, {z})",
            f"{var}.rotation_euler = (math.radians({rx}), math.radians({ry}), math.radians({rz}))",
            f"{var}.scale = ({sx}, {sy}, {sz})",
        ]
        if self.parent:
            lines.append(f"{var}.parent = bpy.data.objects.get({self.parent!r})")
        # Keyframes
        for kf in self.keyframes:
            lines.append(kf.to_blender_script(var))
        return "\n".join(lines)


@dataclass
class Mesh(Object3D):
    """A primitive mesh object."""

    primitive: PrimitiveType = PrimitiveType.CUBE
    size: float = 1.0
    segments: int = 32

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["primitive"] = self.primitive.value
        d["size"] = self.size
        d["segments"] = self.segments
        return d

    def to_blender_script(self) -> str:
        ops_map = {
            PrimitiveType.CUBE: f"bpy.ops.mesh.primitive_cube_add(size={self.size})",
            PrimitiveType.SPHERE: f"bpy.ops.mesh.primitive_uv_sphere_add(radius={self.size/2}, segments={self.segments})",
            PrimitiveType.CYLINDER: f"bpy.ops.mesh.primitive_cylinder_add(radius={self.size/2}, depth={self.size}, vertices={self.segments})",
            PrimitiveType.PLANE: f"bpy.ops.mesh.primitive_plane_add(size={self.size})",
            PrimitiveType.CONE: f"bpy.ops.mesh.primitive_cone_add(radius1={self.size/2}, depth={self.size}, vertices={self.segments})",
            PrimitiveType.TORUS: f"bpy.ops.mesh.primitive_torus_add(major_radius={self.size/2}, minor_radius={self.size/6})",
            PrimitiveType.MONKEY: "bpy.ops.mesh.primitive_monkey_add(size=1)",
        }
        lines = [
            ops_map[self.primitive],
            "obj = bpy.context.active_object",
            f"obj.name = {self.name!r}",
            self._transform_script("obj"),
        ]
        if self.material_name:
            lines += [
                f"mat = bpy.data.materials.get({self.material_name!r})",
                "if mat:",
                "    obj.data.materials.append(mat)",
            ]
        return "\n".join(lines)


@dataclass
class Empty(Object3D):
    """An empty object — useful as a parent/target for cameras and constraints."""

    display_size: float = 0.5

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["display_size"] = self.display_size
        return d

    def to_blender_script(self) -> str:
        lines = [
            f"bpy.ops.object.empty_add(type='PLAIN_AXES')",
            "obj = bpy.context.active_object",
            f"obj.name = {self.name!r}",
            f"obj.empty_display_size = {self.display_size}",
            self._transform_script("obj"),
        ]
        return "\n".join(lines)


@dataclass
class ImportedModel(Object3D):
    """A model imported from a file (GLTF, FBX, OBJ)."""

    file_path: str = ""
    file_format: str = "GLTF"  # GLTF, FBX, OBJ

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["file_path"] = self.file_path
        d["file_format"] = self.file_format
        return d

    def to_blender_script(self) -> str:
        import_map = {
            "GLTF": f"bpy.ops.import_scene.gltf(filepath={self.file_path!r})",
            "FBX": f"bpy.ops.import_scene.fbx(filepath={self.file_path!r})",
            "OBJ": f"bpy.ops.wm.obj_import(filepath={self.file_path!r})",
        }
        lines = [
            import_map.get(self.file_format, import_map["GLTF"]),
            "obj = bpy.context.active_object",
            f"obj.name = {self.name!r}",
            self._transform_script("obj"),
        ]
        return "\n".join(lines)
