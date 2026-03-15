# Cinematic Pipeline

Code-driven 3D cinematic video production using Blender. Compose scenes in Python, render to MP4.

Built to produce announcement/hype videos at the quality level of the [Kinetiq $KNTQ token launch](https://x.com/kinetiq_xyz/status/1994013492370706866) — fighter jets, 3D characters, volumetric lighting, particle simulations, HUD overlays, cinematic camera movements.

## How It Works

```
Python scene description  →  Blender Python script  →  Blender renders frames  →  MP4
```

You describe scenes using Python dataclasses. The pipeline generates Blender Python scripts that build the 3D scene and render it. No manual Blender UI interaction required.

## Quick Start

### Prerequisites

- **Blender 5.0+** — [Download](https://www.blender.org/download/) (free, tested with 5.0.1)
- **Python 3.10+**
- **FFmpeg** — for video compositing (optional, Blender can render directly to MP4)
- **NVIDIA GPU** — recommended for Cycles rendering (CPU works but 10x slower)

### Install

```bash
git clone https://github.com/Kitolochi/cinematic-pipeline.git
cd cinematic-pipeline
pip install -e .
```

### Verify Blender

```bash
blender --version
# Should show Blender 3.x or 4.x
```

### Render Your First Scene

```bash
python examples/hello_cube.py
# This generates a Blender render script at ./output/hello_cube/

# Then render it:
blender --background -E CYCLES --python "./output/hello_cube/_render_script.py"
```

## Architecture

```
src/cinematic_pipeline/
├── core/           # Scene graph, camera, lights, materials, animation, rendering
│   ├── scene.py    # Scene — top-level container
│   ├── objects.py  # Mesh, Empty, ImportedModel
│   ├── camera.py   # Camera with cinematic presets (orbit, dolly, crane, handheld)
│   ├── light.py    # Lights + rig presets (three-point, dramatic, neon)
│   ├── material.py # PBR materials + presets (metallic, holographic, neon)
│   ├── animation.py # Keyframe system
│   └── render.py   # Render pipeline (Eevee preview, Cycles final)
├── vfx/            # Particles, volumetrics, post-processing (Phase 2)
├── assets/         # Model import, HDRI library, asset management (Phase 3)
├── templates/      # Pre-built Kinetiq-style shot templates (Phase 4)
└── mcp/            # Blender MCP integration for Claude control (Phase 5)
```

## Scene Composition API

```python
from cinematic_pipeline.core import *

scene = Scene(name="My_Video", fps=30, frame_end=300)

# Add objects
scene.add(Mesh(name="Hero", primitive=PrimitiveType.SPHERE, size=2.0))

# Add camera with cinematic preset
scene.add(Camera(
    name="Cam",
    preset=CameraPreset.ORBIT,
    preset_params={"radius": 5, "revolutions": 1},
    track_target="Hero",
    dof_enabled=True, dof_aperture=2.8,
))

# Add dramatic lighting
for light in three_point_rig(key_energy=200):
    scene.add(light)

# Render
from cinematic_pipeline.core.render import RenderConfig, write_and_render
cmd = write_and_render(scene, RenderConfig(output_dir="./output"))
print(cmd)  # blender --background -E CYCLES --python ...
```

## Camera Presets

| Preset | Description |
|--------|-------------|
| `STATIC` | Fixed camera |
| `ORBIT` | Circle around target (configurable radius, height, revolutions) |
| `DOLLY_IN` | Push toward target |
| `DOLLY_OUT` | Pull away from target |
| `CRANE_UP` | Rise upward while looking at target |
| `CRANE_DOWN` | Lower while looking at target |
| `HANDHELD` | Subtle noise-based shake |

## Lighting Presets

| Preset | Use For |
|--------|---------|
| `three_point_rig()` | Standard cinematic lighting |
| `dramatic_side_rig()` | Noir/moody side lighting |
| `neon_accent_rig()` | Cyberpunk-style colored accents |

## Material Presets

| Preset | Look |
|--------|------|
| `metallic_dark()` | Dark brushed metal |
| `holographic_glass()` | Sci-fi holographic panel |
| `neon_emissive(color)` | Bright neon glow |
| `matte_white()` | Clean matte surface |

## Render Engines

- **Eevee** — Fast preview (~2-5s/frame). Good for iteration.
- **Cycles** — Photorealistic final render. Use with GPU + denoising.

Set via `Scene(render_engine="CYCLES")` or `Scene(render_engine="BLENDER_EEVEE")`.

## Blender MCP Integration (Phase 5)

This pipeline is designed to work with [Blender MCP](https://github.com/ahujasid/blender-mcp) for Claude-controlled scene composition. With MCP, Claude can:

- Execute pipeline scripts directly in Blender
- See the viewport via screenshots
- Search Sketchfab for 3D models
- Download HDRIs from Poly Haven
- Iterate on scenes with visual feedback

Setup guide coming in Phase 5.

## Roadmap

- [x] Phase 1: Core SDK (scene graph, camera, lights, materials, rendering)
- [ ] Phase 2: VFX (particles, volumetrics, HUD overlays, post-processing)
- [ ] Phase 3: Asset pipeline (model import, HDRI library, Sketchfab integration)
- [ ] Phase 4: Scene templates (Kinetiq-style shots)
- [ ] Phase 5: Blender MCP integration
- [ ] Phase 6: First production video

## License

MIT
