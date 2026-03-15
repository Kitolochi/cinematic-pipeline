"""Post-processing pipeline via Blender's compositor nodes.

Blender 5.0 API: compositor uses node groups assigned to
scene.compositing_node_group. NodeGroupOutput replaces CompositorNodeComposite.
ShaderNodeMix replaces CompositorNodeMixRGB.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PostProcessing:
    """Configurable post-processing stack using Blender's compositor."""

    bloom_enabled: bool = True
    bloom_threshold: float = 0.8
    bloom_intensity: float = 0.5
    bloom_radius: int = 6

    chromatic_aberration: bool = False
    ca_dispersion: float = 0.01

    vignette: bool = True
    vignette_intensity: float = 0.4

    color_grade_contrast: float = 1.1
    color_grade_saturation: float = 1.05
    color_grade_lift: tuple[float, float, float] = (1.0, 1.0, 1.0)
    color_grade_gain: tuple[float, float, float] = (1.0, 1.0, 1.0)

    glare_enabled: bool = False
    glare_type: str = "FOG_GLOW"  # FOG_GLOW, STREAKS, GHOSTS
    glare_quality: str = "HIGH"
    glare_threshold: float = 1.0

    def to_blender_script(self) -> str:
        lines = [
            "# --- Post-Processing Compositor (Blender 5.0) ---",
            "# Create compositor node group",
            "comp_tree = bpy.data.node_groups.new('CinematicPost', 'CompositorNodeTree')",
            "bpy.context.scene.compositing_node_group = comp_tree",
            "nodes = comp_tree.nodes",
            "links = comp_tree.links",
            "",
            "# Render layers input",
            "rl = nodes.new('CompositorNodeRLayers')",
            "rl.location = (0, 0)",
            "",
            "# Group output (replaces CompositorNodeComposite in 5.0)",
            "out = nodes.new('NodeGroupOutput')",
            "out.location = (1400, 0)",
            "comp_tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')",
            "",
            "# Viewer node",
            "viewer = nodes.new('CompositorNodeViewer')",
            "viewer.location = (1400, -200)",
            "",
            "# Track the current output socket",
            "current_output = rl.outputs['Image']",
            "x_offset = 250",
        ]

        # Bloom / Glare (Blender 5.0: uses input sockets, not properties)
        if self.bloom_enabled or self.glare_enabled:
            glare_type = self.glare_type if self.glare_enabled else "Fog Glow"
            # Map old enum names to Blender 5.0 menu values
            type_map = {"FOG_GLOW": "Fog Glow", "STREAKS": "Streaks", "GHOSTS": "Ghost"}
            glare_type_val = type_map.get(glare_type, glare_type)
            quality_map = {"HIGH": "High", "MEDIUM": "Medium", "LOW": "Low"}
            quality_val = quality_map.get(self.glare_quality, self.glare_quality)
            threshold = self.glare_threshold if self.glare_enabled else self.bloom_threshold
            lines += [
                "",
                "# Bloom / Glare",
                "glare = nodes.new('CompositorNodeGlare')",
                "glare.location = (x_offset, 0)",
                f"glare.inputs['Type'].default_value = {glare_type_val!r}",
                f"glare.inputs['Quality'].default_value = {quality_val!r}",
                f"glare.inputs['Threshold'].default_value = {threshold}",
            ]
            if self.bloom_enabled:
                lines.append(f"glare.inputs['Size'].default_value = {self.bloom_radius / 10.0}")
            lines += [
                "links.new(current_output, glare.inputs['Image'])",
                "current_output = glare.outputs['Image']",
                "x_offset += 250",
            ]

        # Color grading (Blender 5.0: all settings are socket inputs)
        lr, lg, lb = self.color_grade_lift
        gr, gg, gb = self.color_grade_gain
        lines += [
            "",
            "# Color Balance (color grading)",
            "cb = nodes.new('CompositorNodeColorBalance')",
            "cb.location = (x_offset, 0)",
            "cb.inputs['Type'].default_value = 'Lift/Gamma/Gain'",
            f"cb.inputs[4].default_value = ({lr}, {lg}, {lb}, 1.0)",  # Lift RGBA
            f"cb.inputs[8].default_value = ({gr}, {gg}, {gb}, 1.0)",  # Gain RGBA
            "links.new(current_output, cb.inputs['Image'])",
            "current_output = cb.outputs['Image']",
            "x_offset += 250",
        ]

        # Brightness/Contrast
        if self.color_grade_contrast != 1.0:
            contrast_val = (self.color_grade_contrast - 1.0) * 50
            lines += [
                "",
                "# Contrast",
                "bc = nodes.new('CompositorNodeBrightContrast')",
                "bc.location = (x_offset, 0)",
                f"bc.inputs['Contrast'].default_value = {contrast_val}",
                "links.new(current_output, bc.inputs['Image'])",
                "current_output = bc.outputs['Image']",
                "x_offset += 250",
            ]

        # Saturation
        if self.color_grade_saturation != 1.0:
            lines += [
                "",
                "# Saturation",
                "hue_sat = nodes.new('CompositorNodeHueSat')",
                "hue_sat.location = (x_offset, 0)",
                f"hue_sat.inputs['Saturation'].default_value = {self.color_grade_saturation}",
                "links.new(current_output, hue_sat.inputs['Image'])",
                "current_output = hue_sat.outputs['Image']",
                "x_offset += 250",
            ]

        # Chromatic Aberration
        if self.chromatic_aberration:
            lines += [
                "",
                "# Chromatic Aberration",
                "lens = nodes.new('CompositorNodeLensdist')",
                "lens.location = (x_offset, 0)",
                f"lens.inputs['Dispersion'].default_value = {self.ca_dispersion}",
                "lens.inputs['Fit'].default_value = True",
                "links.new(current_output, lens.inputs['Image'])",
                "current_output = lens.outputs['Image']",
                "x_offset += 250",
            ]

        # Vignette (ellipse mask + blur + multiply via ShaderNodeMix)
        if self.vignette:
            lines += [
                "",
                "# Vignette",
                "ellipse = nodes.new('CompositorNodeEllipseMask')",
                "ellipse.location = (x_offset - 200, -300)",
                "ellipse.inputs['Size'].default_value = (0.85, 0.85)",
                "",
                "blur_vig = nodes.new('CompositorNodeBlur')",
                "blur_vig.location = (x_offset - 50, -300)",
                "blur_vig.inputs['Size'].default_value = (200, 200)",
                "links.new(ellipse.outputs['Mask'], blur_vig.inputs['Image'])",
                "",
                "# Multiply vignette over image using ShaderNodeMix",
                "mix_vig = nodes.new('ShaderNodeMix')",
                "mix_vig.location = (x_offset, 0)",
                "mix_vig.data_type = 'RGBA'",
                "mix_vig.blend_type = 'MULTIPLY'",
                f"mix_vig.inputs['Factor'].default_value = {self.vignette_intensity}",
                "links.new(current_output, mix_vig.inputs[6])",   # A input for RGBA mode
                "links.new(blur_vig.outputs['Image'], mix_vig.inputs[7])",  # B input for RGBA mode
                "current_output = mix_vig.outputs[2]",  # Result output for RGBA mode
                "x_offset += 250",
            ]

        # Final connections
        lines += [
            "",
            "# Connect to output",
            "links.new(current_output, out.inputs['Image'])",
            "links.new(current_output, viewer.inputs['Image'])",
        ]

        return "\n".join(lines)


# --- Presets ---

def cinematic_post() -> PostProcessing:
    """Cinematic post-processing — bloom, vignette, warm grade."""
    return PostProcessing(
        bloom_enabled=True,
        bloom_threshold=0.7,
        bloom_intensity=0.6,
        bloom_radius=7,
        chromatic_aberration=True,
        ca_dispersion=0.008,
        vignette=True,
        vignette_intensity=0.5,
        color_grade_contrast=1.15,
        color_grade_saturation=1.1,
        color_grade_lift=(0.98, 0.95, 0.9),
        color_grade_gain=(1.05, 1.0, 0.95),
    )


def clean_tech() -> PostProcessing:
    """Clean tech look — subtle bloom, no grain, slight blue grade."""
    return PostProcessing(
        bloom_enabled=True,
        bloom_threshold=1.0,
        bloom_radius=4,
        chromatic_aberration=False,
        vignette=True,
        vignette_intensity=0.3,
        color_grade_contrast=1.05,
        color_grade_lift=(0.95, 0.97, 1.0),
        color_grade_gain=(0.98, 1.0, 1.05),
    )


def sci_fi_glow() -> PostProcessing:
    """Sci-fi neon glow — heavy bloom, chromatic aberration, blue grade."""
    return PostProcessing(
        bloom_enabled=True,
        bloom_threshold=0.5,
        bloom_intensity=0.8,
        bloom_radius=8,
        chromatic_aberration=True,
        ca_dispersion=0.015,
        vignette=True,
        vignette_intensity=0.6,
        glare_enabled=True,
        glare_type="STREAKS",
        glare_threshold=0.8,
        color_grade_contrast=1.2,
        color_grade_saturation=1.15,
        color_grade_lift=(0.9, 0.92, 1.0),
        color_grade_gain=(0.95, 1.0, 1.1),
    )
