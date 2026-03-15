"""Model import pipeline — GLTF, FBX, OBJ with post-import cleanup.

Generates Blender Python scripts that import 3D models from files,
normalize scale, center origin, and apply transforms.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum


class ModelFormat(Enum):
    """Supported 3D model formats."""
    GLTF = "gltf"
    GLB = "glb"
    FBX = "fbx"
    OBJ = "obj"


def detect_format(file_path: str) -> ModelFormat:
    """Detect model format from file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    format_map = {
        ".gltf": ModelFormat.GLTF,
        ".glb": ModelFormat.GLB,
        ".fbx": ModelFormat.FBX,
        ".obj": ModelFormat.OBJ,
    }
    if ext not in format_map:
        raise ValueError(f"Unsupported format: {ext}. Supported: {list(format_map.keys())}")
    return format_map[ext]


@dataclass
class ImportedModel:
    """A 3D model imported from a file with post-import processing."""

    file_path: str
    name: str = ""
    location: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)  # degrees
    target_size: float | None = None  # Normalize largest dimension to this
    center_origin: bool = True
    apply_transforms: bool = True
    remove_empties: bool = True

    def __post_init__(self):
        if not self.name:
            self.name = os.path.splitext(os.path.basename(self.file_path))[0]

    def to_dict(self) -> dict:
        return {
            "type": "ImportedModel",
            "file_path": self.file_path,
            "name": self.name,
            "location": list(self.location),
            "rotation": list(self.rotation),
            "target_size": self.target_size,
            "center_origin": self.center_origin,
            "apply_transforms": self.apply_transforms,
        }

    def to_blender_script(self) -> str:
        fmt = detect_format(self.file_path)
        abs_path = os.path.abspath(self.file_path).replace("\\", "/")
        x, y, z = self.location
        rx, ry, rz = self.rotation

        lines = [
            f"# --- Import Model: {self.name} ---",
            "import math",
            "",
            "# Record existing objects before import",
            "_before = set(bpy.data.objects.keys())",
            "",
        ]

        # Format-specific import command
        if fmt in (ModelFormat.GLTF, ModelFormat.GLB):
            lines.append(f"bpy.ops.import_scene.gltf(filepath={abs_path!r})")
        elif fmt == ModelFormat.FBX:
            lines.append(f"bpy.ops.import_scene.fbx(filepath={abs_path!r})")
        elif fmt == ModelFormat.OBJ:
            lines.append(f"bpy.ops.wm.obj_import(filepath={abs_path!r})")

        lines += [
            "",
            "# Find newly imported objects",
            "_after = set(bpy.data.objects.keys())",
            "_new_names = _after - _before",
            "_new_objs = [bpy.data.objects[n] for n in _new_names]",
            f"print(f'Imported {{len(_new_objs)}} objects: {{_new_names}}')",
        ]

        # Remove empties
        if self.remove_empties:
            lines += [
                "",
                "# Remove empty objects (armature roots, etc.)",
                "_empties = [o for o in _new_objs if o.type == 'EMPTY']",
                "for e in _empties:",
                "    bpy.data.objects.remove(e, do_unlink=True)",
                "_new_objs = [o for o in _new_objs if o.name in bpy.data.objects]",
            ]

        # Apply transforms
        if self.apply_transforms:
            lines += [
                "",
                "# Apply transforms",
                "bpy.ops.object.select_all(action='DESELECT')",
                "for o in _new_objs:",
                "    if o.name in bpy.data.objects:",
                "        o.select_set(True)",
                "bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)",
            ]

        # Center origin
        if self.center_origin:
            lines += [
                "",
                "# Center origin to geometry",
                "bpy.ops.object.select_all(action='DESELECT')",
                "for o in _new_objs:",
                "    if o.name in bpy.data.objects and o.type == 'MESH':",
                "        o.select_set(True)",
                "bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')",
            ]

        # Normalize scale
        if self.target_size is not None:
            lines += [
                "",
                f"# Normalize to target size {self.target_size}",
                "_meshes = [o for o in _new_objs if o.name in bpy.data.objects and o.type == 'MESH']",
                "if _meshes:",
                "    import mathutils",
                "    _all_coords = []",
                "    for o in _meshes:",
                "        _all_coords.extend([o.matrix_world @ v.co for v in o.data.vertices])",
                "    if _all_coords:",
                "        _min = mathutils.Vector((_all_coords[0]))",
                "        _max = mathutils.Vector((_all_coords[0]))",
                "        for c in _all_coords:",
                "            for i in range(3):",
                "                _min[i] = min(_min[i], c[i])",
                "                _max[i] = max(_max[i], c[i])",
                "        _dims = _max - _min",
                "        _largest = max(_dims)",
                "        if _largest > 0:",
                f"            _scale_factor = {self.target_size} / _largest",
                "            for o in _new_objs:",
                "                if o.name in bpy.data.objects:",
                "                    o.scale *= _scale_factor",
            ]

        # Position and rotate
        lines += [
            "",
            "# Position imported model",
            "_meshes = [o for o in _new_objs if o.name in bpy.data.objects and o.type == 'MESH']",
            "for o in _meshes:",
            f"    o.location = ({x}, {y}, {z})",
            f"    o.rotation_euler = (math.radians({rx}), math.radians({ry}), math.radians({rz}))",
        ]

        # Rename primary mesh
        lines += [
            "",
            f"# Rename primary mesh to '{self.name}'",
            "if _meshes:",
            f"    _meshes[0].name = {self.name!r}",
        ]

        return "\n".join(lines)


@dataclass
class SketchfabModel:
    """Import a model from Sketchfab via MCP.

    Requires Blender MCP with Sketchfab enabled and API key configured.
    Use search_sketchfab_models() MCP tool to find UIDs.
    """

    uid: str
    name: str = ""
    target_size: float = 1.0
    location: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def to_dict(self) -> dict:
        return {
            "type": "SketchfabModel",
            "uid": self.uid,
            "name": self.name,
            "target_size": self.target_size,
            "location": list(self.location),
            "rotation": list(self.rotation),
        }
