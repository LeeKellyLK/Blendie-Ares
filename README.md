# Blendie-Ares

Blendie-Ares is a Blender add-on (targeting Blender **5.2.1**) for distributing a source mesh across a target mesh in multiple placement modes.

## Blender support

- Primary target: **Blender 5.2.1**
- Backward compatibility: not guaranteed in this MVP

## Features (MVP)

- Source mesh selection by:
  - object name
  - active selection helper button
- Target mesh selection by:
  - object name
  - active selection helper button
  - optional use of all selected mesh objects as targets
- Distribution modes:
  - **Chain**: sequential linked placement
  - **Fill**: area coverage with contact tolerance controls
  - **Guided**: tangent-informed orientation flow
- Distribution strategies:
  - uniform
  - random
  - weighted by triangle area
- Non-destructive linked-instance output by default
- Optional convert-to-real meshes on apply
- Preview / Apply / Clear workflow

## Add-on structure

- `/home/runner/work/Blendie-Ares/Blendie-Ares/blendie_ares/__init__.py`  
  Add-on metadata and registration entry point
- `/home/runner/work/Blendie-Ares/Blendie-Ares/blendie_ares/properties.py`  
  Scene-level add-on settings
- `/home/runner/work/Blendie-Ares/Blendie-Ares/blendie_ares/ui.py`  
  3D View sidebar panel
- `/home/runner/work/Blendie-Ares/Blendie-Ares/blendie_ares/operators.py`  
  Preview/Apply/Clear/selection operators
- `/home/runner/work/Blendie-Ares/Blendie-Ares/blendie_ares/validation.py`  
  Source/target resolution and validation
- `/home/runner/work/Blendie-Ares/Blendie-Ares/blendie_ares/sampling.py`  
  Surface sampling and orientation helpers
- `/home/runner/work/Blendie-Ares/Blendie-Ares/blendie_ares/placement.py`  
  Chain/fill/guided placement strategies
- `/home/runner/work/Blendie-Ares/Blendie-Ares/blendie_ares/utils.py`  
  Collection/output utility helpers

## Installation

1. Open Blender 5.2.1.
2. Go to `Edit > Preferences > Add-ons`.
3. Click `Install...`.
4. Select the add-on folder (or zip containing `blendie_ares`).
5. Enable **Blendie Ares**.

## Quick workflow

1. In 3D Viewport, open sidebar (`N`) and the **Blendie Ares** tab.
2. Set source object (name field or **Use Active as Source**).
3. Set target object (name field or **Use Active as Target**).
4. Choose mode and settings.
5. Click **Preview** for draft output.
6. Click **Apply** for final output.
7. Click **Clear Generated** to remove generated collections.

## Recommended starter presets

- Chain mail-like strips:
  - Mode: `CHAIN`
  - Distribution: `WEIGHTED`
  - Spacing: `0.12`
  - Rotation jitter: `5.0`
  - Contact tolerance: `0.15`
- Dense surface fill:
  - Mode: `FILL`
  - Distribution: `WEIGHTED`
  - Spacing: `0.08`
  - Density: `1.3`
  - Contact tolerance: `0.20`
- Flow-like guided layout:
  - Mode: `GUIDED`
  - Distribution: `UNIFORM`
  - Spacing: `0.10`
  - Rotation jitter: `7.5`

## Manual validation matrix

- Source shape variety: simple ring, elongated link, irregular mesh
- Target topology: plane, sphere, curved manifold, non-manifold
- Transform states: unapplied scale, mirrored scale, rotated objects
- Density scales: low, medium, high
- Mode checks:
  - Chain continuity and spacing behavior
  - Fill coverage and contact tolerance behavior
  - Guided orientation consistency
- Operational checks:
  - Preview then Apply
  - Clear cleanup
  - Undo/redo stability

## Acceptance criteria coverage

- Source can be selected by name or active selection
- At least two robust modes provided (Chain and Fill, plus Guided optional mode)
- Reproducible output via random seed controls
- Instancing-first workflow for practical scene performance

## Post-MVP enhancements

- Geodesic-aware chain progression over surface topology
- Advanced packing heuristics and collision solvers
- Optional curve/UV-guided direction fields
- Spatial acceleration for very dense fills