"""Rendering pipeline — generates Blender scripts for still and animation renders."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from cinematic_pipeline.core.scene import Scene


@dataclass
class RenderConfig:
    """Render output configuration."""

    output_dir: str = "./output"
    filename_prefix: str = "frame_"
    image_format: str = "PNG"  # PNG, JPEG, OPEN_EXR
    video_codec: str = "H264"
    video_format: str = "FFMPEG"
    quality: int = 90  # For JPEG/video
    use_compositing: bool = True
    use_sequencer: bool = False


def render_still_script(scene: Scene, config: RenderConfig, frame: int | None = None) -> str:
    """Generate a Blender script that renders a single frame."""
    output_path = os.path.join(config.output_dir, f"{config.filename_prefix}still")
    frame_num = frame or scene.frame_start

    lines = [
        scene.to_blender_script(),
        "",
        "# --- Render Still ---",
        f"bpy.context.scene.frame_set({frame_num})",
        f"bpy.context.scene.render.image_settings.file_format = {config.image_format!r}",
        f"bpy.context.scene.render.filepath = {output_path!r}",
        f"bpy.context.scene.render.use_compositing = {config.use_compositing}",
        "bpy.ops.render.render(write_still=True)",
        f"print('Rendered still to: {output_path}')",
    ]
    return "\n".join(lines)


def render_animation_script(scene: Scene, config: RenderConfig) -> str:
    """Generate a Blender script that renders a full animation to MP4."""
    output_path = os.path.join(config.output_dir, f"{config.filename_prefix}video.mp4")

    lines = [
        scene.to_blender_script(),
        "",
        "# --- Render Animation ---",
        f"bpy.context.scene.render.image_settings.file_format = {config.video_format!r}",
        f"bpy.context.scene.render.ffmpeg.format = 'MPEG4'",
        f"bpy.context.scene.render.ffmpeg.codec = {config.video_codec!r}",
        f"bpy.context.scene.render.ffmpeg.constant_rate_factor = 'HIGH'",
        f"bpy.context.scene.render.ffmpeg.audio_codec = 'AAC'",
        f"bpy.context.scene.render.filepath = {output_path!r}",
        f"bpy.context.scene.render.use_compositing = {config.use_compositing}",
        "bpy.ops.render.render(animation=True)",
        f"print('Rendered animation to: {output_path}')",
    ]
    return "\n".join(lines)


def render_frame_sequence_script(scene: Scene, config: RenderConfig) -> str:
    """Generate a Blender script that renders individual frames (for FFmpeg compositing)."""
    output_path = os.path.join(config.output_dir, config.filename_prefix)

    lines = [
        scene.to_blender_script(),
        "",
        "# --- Render Frame Sequence ---",
        f"bpy.context.scene.render.image_settings.file_format = {config.image_format!r}",
        f"bpy.context.scene.render.filepath = {output_path!r}",
        f"bpy.context.scene.render.use_compositing = {config.use_compositing}",
        "bpy.ops.render.render(animation=True)",
        f"print('Rendered frames to: {output_path}')",
    ]
    return "\n".join(lines)


def write_and_render(scene: Scene, config: RenderConfig, mode: str = "animation") -> str:
    """Write scene script to disk and return the blender CLI command to execute it."""
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    script_path = os.path.join(config.output_dir, "_render_script.py")

    if mode == "still":
        script = render_still_script(scene, config)
    elif mode == "frames":
        script = render_frame_sequence_script(scene, config)
    else:
        script = render_animation_script(scene, config)

    with open(script_path, "w") as f:
        f.write(script)

    engine_flag = ""
    if scene.render_engine == "BLENDER_EEVEE":
        engine_flag = " -E BLENDER_EEVEE"
    elif scene.render_engine == "CYCLES":
        engine_flag = " -E CYCLES"

    cmd = f"blender --background{engine_flag} --python {script_path!r}"
    return cmd
