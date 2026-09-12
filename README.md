# Blendie-Ares

## Blender 5.2.1 Plugin Implementation Plan

Goal: build a Blender addon that takes a pre-made "tile" mesh (selected by name or object selection) and distributes it over a target mesh with multiple layout modes (for example chain-like linking and dense surface fill where pieces touch/follow the target surface).

### 1) Scope and success criteria

- Blender version target: **5.2.1**
- Input A: source tile mesh object (user chooses by:
  - active selection, or
  - name search from scene objects)
- Input B: target mesh object to populate.
- Output: generated instances arranged on/around the target mesh in selectable distribution mode.

Success criteria:
- User can pick source + target in UI.
- User can run at least two placement modes:
  - **Chain/Link mode** (mail-like linked progression)
  - **Surface Fill mode** (coverage with local orientation and spacing control)
- Generation is repeatable with parameters and can be cleared/regenerated safely.

### 2) Minimal addon structure

- `blendie_ares/__init__.py`
  - `bl_info`, register/unregister entrypoint.
- `blendie_ares/properties.py`
  - `PropertyGroup` for source name, mode, spacing, random seed, density.
- `blendie_ares/operators.py`
  - `OBJECT_OT_generate_pattern`
  - `OBJECT_OT_clear_pattern`
- `blendie_ares/panel.py`
  - `VIEW3D` sidebar panel for configuration and execution.
- `blendie_ares/generator.py`
  - Core sampling/orientation/instancing logic.

### 3) Data & UX design

Addon panel fields:
- Source object mode:
  - "Use Active Object as Source"
  - "Use Named Object" (+ searchable string/dropdown)
- Target object picker.
- Distribution mode enum:
  - `CHAIN_LINK`
  - `SURFACE_FILL`
- Shared controls:
  - spacing
  - scale multiplier
  - random rotation jitter
  - random seed
  - output collection name
- Action buttons:
  - Generate
  - Clear Generated

Implementation detail:
- Place generated objects into a dedicated collection (for non-destructive cleanup).
- Prefer linked duplicates/instances for performance.

### 4) Geometry generation approach

#### A) Surface Fill mode

1. Evaluate target mesh in world space.
2. Sample candidate points across faces (area-weighted sampling or geometry nodes-style point distribution logic in Python).
3. For each point:
   - compute face normal/tangent basis,
   - align source instance local up-axis to normal,
   - apply spacing rejection (minimum distance) to reduce overlap.
4. Optionally project/offset along normal to avoid z-fighting.

#### B) Chain/Link mode

1. Build adjacency/path over target surface (edge-walk or curve path derived from selected direction axis/UV direction if available).
2. Step along path by link length + spacing.
3. Alternate instance rotation/orientation to imitate interlocking structure.
4. Keep instances tangent to surface normal while preserving chain direction continuity.

### 5) Safety, validation, and performance

- Validate source and target are mesh objects before running.
- Handle missing objects and empty mesh data with clear error messages.
- Use depsgraph-evaluated mesh where needed.
- Create/cleanup generated collection transactionally to prevent orphan objects.
- Keep operations undo-friendly (`bl_options = {'REGISTER', 'UNDO'}`).

### 6) Testing/verification strategy

Given current repository has no existing test infrastructure:
- Use manual verification in Blender:
  1. Enable addon.
  2. Create source tile mesh + target mesh.
  3. Generate in both modes and verify:
     - placement follows target,
     - spacing responds to parameter changes,
     - regenerate works,
     - clear removes only generated output.

### 7) Delivery phases

1. **Phase 1**: addon scaffold + UI + object selection + clear/generate plumbing.
2. **Phase 2**: implement Surface Fill mode.
3. **Phase 3**: implement Chain/Link mode.
4. **Phase 4**: stabilization, error handling, and Blender 5.2.1 verification pass.

## Clarifying questions

1. Should generated output be real duplicated mesh objects, collection instances, or geometry-nodes-based instances?
2. For "touching each other," do you want strict collision/contact solving, or spacing-based approximation?
3. In chain mode, should links follow:
   - a user-selected edge loop/path,
   - automatically derived surface direction, or
   - a drawn curve object?
4. Is non-destructive editing required (regenerate from saved parameters), or is one-time bake acceptable?
5. Should the addon support only one source tile object, or a set of source variants for randomization?