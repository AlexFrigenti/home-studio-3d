# Furniture Placement v1 Implementation Plan

> **For agentic workers:** Execute this plan task-by-task only after the Slice 004 specification has been reviewed and approved. Keep every implementation task independently testable and do not start a later task while an earlier contract is unresolved.

**Goal:** Add a separate, deterministic furniture-layout domain that can validate synthetic proxy placements, generate a reversible Blender overlay, normalize it, compare it back to the furniture plan and prove that the room architecture is unchanged.

**Architecture:** Keep `measurements/`, the room schemas, the room generation plan and the existing room scene adapter unchanged. Add a pure furniture pipeline under its own modules: layout validation → furniture plan → spatial validation → derived Blender overlay → independent normalized furniture scene → furniture comparison report. The only Blender write is to a new derived scene; the canonical architectural `.blend` is opened as a source and never overwritten.

**Tech Stack:** Python standard library, JSON, existing room plan helpers, `unittest`, Blender `bpy` only for the explicitly authorized overlay and acceptance gate. No external furniture assets or services.

**Spec:** `specs/004-furniture-placement-v1/spec.md`

**Current checkpoint:** T4.01, T4.02, T4.03, T4.04, T4.05 y T4.06 están implementadas y validadas.
T4.02 produce un furniture plan puro con yaw canónico, geometría efectiva y
firma determinista; T4.03 produce validación espacial pura y determinista;
T4.04 produce un overlay Blender reversible; T4.05 produce normalización
read-only y comparación pura; T4.06 cierra la acceptance canónica, el artefacto
derivado, el preview técnico y la documentación del slice.

## Global Constraints

- `measurements/` remains the source of truth for architecture; layouts are not room measurements.
- The canonical layout location is `layouts/<room_id>/<layout_id>.json`; there is no mutable `current` alias.
- The input contract is `furniture-layout-1`, with `units=m`, `coordinate_system=canonical_room`, `placement_method=manual` and `anchor=bottom_center`.
- `dimensions_m` is ordered `[width, depth, height]`; dimensions are finite and positive; `unknown` is not accepted for generated v1 proxies.
- Furniture positions use `position_xy_m` at the center of the proxy base and finite `yaw_deg` degrees; T4.02 normalizes the plan output to `[0, 360)`.
- The pure furniture plan version is `furniture-placement-generator-1` and carries the room plan version and logical signature it was built against.
- The Blender namespace is `HSLAYOUT_<room_id>_<layout_id>` with a managed `Furniture` collection and physical objects named `HSLAYOUT_FURNITURE_<room_id>_<layout_id>_<item_id>`; the semantic `item_id` remains separate metadata.
- The logical collection role is `Furniture`; the physical Blender Collection datablock name is qualified by room and layout to remain unique across multiple layouts.
- Furniture generation may only create or replace its own HSLAYOUT root; it must not call `read_factory_settings`, delete `HS3D_ROOM_*`, modify architecture collections or overwrite the source `.blend`.
- `furniture-scene-adapter-1` and `furniture-scene-comparison-1` are independent contracts; `room-scene-adapter-1` is not extended.
- Spatial errors are evaluated against effective room-plan geometry and are not claims of constructive openings, human clearance or physical wall certainty.
- Same canonical layout plus same room plan must produce the same furniture plan, signature and normalized overlay state.
- All validators and pure functions must avoid mutating their inputs; stable ordering and stable findings are required.
- The first acceptance uses two or three synthetic furniture proxies and must label them `dimensions_status=synthetic`.
- Existing Slice 001–003 code, schemas, measurements, scenes and previews are reused read-only and are not changed by this slice.
- Future real assets, materials, UI, optimization, physics, constructive openings and multi-room are excluded.
- Gates must report actual `PASS`, `FAIL`, `NO APLICA`, `PENDIENTE DE INFRAESTRUCTURA` or `NO EJECUTADO`; no unavailable check is promoted to PASS.

## Planned file boundaries

These paths are planned for implementation tasks; entries marked as created
reflect completed checkpoints:

- Create `layouts/schema/furniture-layout-v1.schema.json`: the machine-readable
  input contract after T4.01 decisions are accepted.
- Create `layouts/living-room-main/<layout-id>.json`: the synthetic acceptance
  layout, only when T4.06 is authorized to create acceptance data.
- Create `blender/scripts/furniture/validate_furniture_layout.py`: pure input
  validation and canonicalization.
- Created `blender/scripts/furniture/build_furniture_plan.py`: pure plan,
  effective proxy geometry and logical signature.
- Created `blender/scripts/furniture/validate_furniture_spatial.py`: floor,
  wall, opening and furniture-overlap checks plus explicitly separated
  warnings.
- Created `blender/scripts/furniture/generate_furniture.py`: read-only source
  opening, owned overlay generation and derived-scene saving.
- Created `tests/furniture/test_furniture_generation_contract.py`: pure overlay
  naming, metadata, geometry, path, determinism and projection tests.
- Created `tests/furniture/blender_test_furniture_generation.py` and
  `tests/furniture/blender_test_furniture_real_acceptance.py`: Blender CLI
  synthetic and temporary source-derived integration checks.
- Created `blender/scripts/furniture/normalize_furniture_scene.py`: independent
  HSLAYOUT adapter.
- Created `blender/scripts/furniture/compare_furniture_scene.py`: pure plan to
  normalized-furniture comparison and report serialization.
- Created `tests/furniture/test_normalize_furniture_scene.py`,
  `tests/furniture/test_furniture_scene_comparison.py`,
  `tests/furniture/blender_test_furniture_scene_normalization.py` and the
  temporary real acceptance runner: normalization, comparison, ownership,
  mutation and deterministic regression tests.
- Create `docs/setup/004-furniture-placement-validation.md`: commands,
  acceptance evidence, artifact hashes, privacy and rollback after the real
  acceptance exists.

Existing files explicitly not modified by this plan:

- `measurements/rooms/living-room-main.json`;
- `measurements/schema/room-v1.schema.json`;
- `measurements/schema/room-v1.1.schema.json`;
- `blender/scripts/measurements/generate_room.py`;
- `blender/scripts/measurements/generation_policy.py`;
- `blender/scripts/measurements/normalize_room_scene.py`;
- `blender/scripts/measurements/compare_room_scene.py`;
- `blender/scripts/measurements/validate_generated_room.py`;
- all existing room tests, historical fixtures, `.blend` files and previews.

## Contract sequence and checkpoints

### T4.01 — Fix furniture authority and input contract

**Objective:** Turn the approved conceptual contract into a closed, testable
layout contract without creating the real acceptance layout yet.

**Planned files:** `layouts/schema/furniture-layout-v1.schema.json`,
`blender/scripts/furniture/validate_furniture_layout.py`,
`tests/furniture/test_furniture_layout.py`, and the Slice 004 specification
files if a decision must be clarified.

**Invariants:** layout remains outside `measurements/`; unknown fields reject;
IDs are stable and unique; dimensions are finite positive
`[width,depth,height]`; statuses are explicit; source IDs contain no personal
paths; input objects are not mutated.

**Tests and gates:** valid minimal layout; each supported item type; missing
required field; unknown field; invalid ID; duplicate ID; wrong units; wrong
coordinate system; wrong placement method; non-finite/non-positive dimensions;
`unknown` dimensions status; invalid position/yaw; deterministic
canonicalization and input no mutation. Existing measurement and generation
gates remain unchanged.

**Blender:** No.

**Closure:** schema and validator agree on every field, the contract is
versioned, and pure validation tests pass without a layout being inserted into
the canonical room data.

### T4.02 — Build the pure furniture plan

**Objective:** Produce a deterministic furniture plan bound to a specific room
plan without importing Blender or writing files.

**Implemented files:** `blender/scripts/furniture/build_furniture_plan.py`,
`tests/furniture/test_furniture_plan.py`.

**Interfaces:**

```text
build_furniture_plan(layout, room_plan) -> furniture_plan
canonicalize_layout(layout) -> canonical_layout
```

The output must contain `furniture-placement-generator-1`, layout identity,
room plan version/signature, sorted items, normalized yaw, effective proxy
geometry, provenance and `logical_signature`.

**Invariants:** room identity and units match; no architecture is copied into
the layout; no input mutation; identical canonical inputs produce byte-stable
plan serialization and signature; geometry uses the bottom-center anchor and
canonical room coordinates. T4.02, not T4.01, owns modulo-360 yaw
normalization. T4.02 supports `room-v1.1-generator-2`; legacy room plan
versions are rejected. Spatial validation is not part of this checkpoint.

**Tests and gates:** 30 pure tests covering room/layout mismatch,
version/signature mismatch, ordering-independent input, yaw values such as
`-360`, `0`, `360` and `720`, `-0.0`, position and rotated footprint
calculations, signature changes for each contractual field, same inputs
produce identical output, provenance preservation and unchanged room plan and
layout.

**Blender:** No.

**Closure:** complete. A pure, serializable plan exists with no dependency on
`bpy`; its signature is stable for all supported input orderings and no
spatial validation or Blender overlay is created.

### T4.03 — Validate spatial placement

**Objective:** Validate only spatial claims that can be demonstrated from the
effective room plan and proxy geometry.

**Planned files:** `blender/scripts/furniture/validate_furniture_spatial.py`,
`tests/furniture/test_furniture_spatial.py`.

**Interface:**

```text
validate_furniture_spatial(furniture_plan, room_plan) -> SpatialValidationReport
```

**Errors:** incompatible binding; malformed effective proxy; outside effective
floor polygon; wall-proxy intersection; opening-proxy intersection; unsupported
floor overlap; duplicate IDs or malformed plan. Geometry is checked only after
the room identity, version, signature, units and coordinate-system binding
passes.

**Warnings:** human clearance, door swing, passage width, ergonomics, window
design rules and other intent that needs data not present in the room contract.

**Invariants:** calculations use effective geometry already present in both
plans, retain entity IDs, use `MATH_TOLERANCE_M=1e-6`, treat floor/wall/opening
touching within tolerance as non-overlap, and never turn the 16 wall-thickness
fallbacks, `opening_direction=unknown`, `proxy_only=true` or
`constructive_geometry=false` into false physical claims. Opening checks use XY
SAT plus Z overlap when both ranges are available, so an elevated window with
no Z overlap does not produce a false collision. `fixed_elements=[]` is
supported without inferred geometry.

**Tests and gates:** 54 pure tests cover binding, boundary-touch tolerance,
rotated OBB/footprint, non-rectangular floor, outside-floor anti-cascade, wall
and opening proxy intersections, measured/fallback walls, Z-separated windows,
fixed-element limitations, two-item overlap, stable finding ordering,
determinism and no mutation. `world_footprint_m` is authoritative and `obb_2d`
is checked for finite, non-degenerate, orthonormal and mutually consistent
derived geometry. Malformed room entities return `malformed_room_plan` without
crashing. Limitations are aggregated by entity kind and code rather than
repeated for every furniture pair. Cross-product comparisons use
`MATH_TOLERANCE_M * max(vector_lengths, MATH_TOLERANCE_M)` in `m²`.

**Blender:** No.

**Closure:** complete. Spatial validity is deterministic, independently
testable and honest about what is geometric proof versus a design heuristic;
no Blender overlay or later furniture task is started.

### T4.04 — Generate a reversible Blender overlay

**Objective:** Materialize only furniture proxies on a new derived scene while
preserving the source architecture.

**Implemented files:** `blender/scripts/furniture/generate_furniture.py`,
`tests/furniture/test_furniture_generation_contract.py`,
`tests/furniture/blender_test_furniture_generation.py` and
`tests/furniture/blender_test_furniture_real_acceptance.py`.

**Interfaces:**

```text
generate_furniture_overlay(source_scene, furniture_plan, output_path) -> derived_scene_metadata
```

**Invariants:** source is opened read-only as input; output is a new path;
only `HSLAYOUT_<room_id>_<layout_id>` and its `Furniture` collection are
managed; no `read_factory_settings`; no deletion or modification of
`HS3D_ROOM_*`; external/manual objects are not owned; duplicate output paths
fail instead of silently overwriting; regenerated layout does not remove
another layout.

**Tests and gates:** source/output path protection; namespace and metadata;
same plan twice; same `item_id` across two layouts; one-layout cleanup does
not remove another; room collection and object snapshot unchanged;
architecture projection/signature equal before and after; no parent transforms;
metric units; generated cube dimensions and transforms agree with the plan;
no Blender auto-suffixes.

**Blender:** Required and executed with Blender `5.2.1 LTS` background CLI for
synthetic and temporary source-derived overlay checks; pure ownership/path
tests run without Blender.

**Closure:** `[x]` one temporary derived `.blend` is generated without
overwriting the source, ownership/idempotence/multiple-layout checks pass, and
an independent architecture projection plus room plan-to-scene comparison
proves before == after.

### T4.05 — Normalize and compare furniture scenes

**Objective:** Add the independent normalized scene and comparison contracts
without extending the room adapter or comparator.

**Planned files:** `blender/scripts/furniture/normalize_furniture_scene.py`,
`blender/scripts/furniture/compare_furniture_scene.py`,
`tests/furniture/test_normalize_furniture_scene.py`,
`tests/furniture/test_furniture_scene_comparison.py`.

**Interfaces:**

```text
normalize_furniture_scene(scene, room_id, layout_id) -> normalized_furniture_scene
normalize_scene(scene_data, room_id, layout_id) -> normalized_furniture_scene
compare_furniture_plan_to_scene(plan, normalized_scene) -> comparison_report
```

**Invariants:** only HSLAYOUT is managed; entities are sorted by type/id;
metadata is limited to what Blender materializes; malformed roots, collections,
roles, units, IDs, geometry, parent transforms and non-finite values fail;
report findings are stable; missing/unexpected items do not cascade into
unrelated fields; furniture metadata for the requested room/layout outside its
exact root is rejected for both objects and collections, while other layouts
and ordinary external objects remain ignored.

**Tests and gates:** valid synthetic normalized scene; duplicate/malformed
entity; wrong units/version/identity/signature; missing/unexpected item; type,
dimension, position, yaw, anchor, geometry and metadata mutation; equivalent
ordering; repeated serialization; metadata-correct/geometry-bad and
geometry-correct/metadata-bad anti-false-pass; architecture entities are not
accepted as furniture entities; same-layout furniture object/collection
outside-root rejection; standalone pure test execution.

**Blender:** No for the core tests; Blender background read-only is used for
synthetic normalization and a temporary generator-2 acceptance. No source
scene is saved and no canonical artifact is created.

**Closure:** the independent adapter and report validate a furniture domain,
are read-only/pure at their respective boundaries, and cannot be mistaken for
`room-scene-adapter-1` or `room-scene-comparison-1`.

### T4.06 — Real acceptance, evidence and setup documentation

**Objective:** Validate the complete recommended slice on `living-room-main`
using a small synthetic layout and record reproducible evidence.

**Implemented files:** `layouts/living-room-main/slice-004-acceptance-v1.json`,
`blender/scenes/review/2026-09-09-living-room-main-slice-004-acceptance-v1-furniture-v1.blend`,
`renders/previews/2026-09-09-living-room-main-slice-004-acceptance-v1-furniture-v1/qa-top-orthographic.png`,
`docs/setup/004-furniture-placement-validation.md` and
`tests/furniture/blender_test_furniture_t406_acceptance.py`.

**Acceptance invariants:** room source hash unchanged; architecture before and
after equal; furniture plan, spatial validation, normalized furniture scene and
comparison report valid; two runs have identical logical serializations;
source `.blend` is not overwritten; all dimensions are explicitly synthetic;
no furniture asset is introduced.

**Gates:** all furniture tests; existing 230/230 measurements suite and
historical 37/37 validation; validators v1/v1.1/real; room plan and room→plan;
golden v1 exact; Python/JSON syntax; diff check; read-only privacy and artifact
review; authorized Blender CLI background acceptance. MCP is not required.

**Blender:** Required for the acceptance and preview, with the source scene
opened and the derived scene saved under a new name.

**Closure:** `[x]` documented real acceptance, hashes, deterministic report,
anti-false-pass, architecture protection, preview review, privacy/provenance
review and rollback are available; no task beyond T4.06 is implied.

## T4.06 evidence

The canonical acceptance layout is `slice-004-acceptance-v1`. The derived
scene SHA-256 is
`7A0F5683D11C5203A9A01D8243C3173FE53022217AC7C00F36FB2DE9A18D422F` and the
technical preview SHA-256 is
`0184EBD44140BB91178FB38E11B800C09B671B4366D95C0D50C4DE26AEA6F773`.
The preview is sanitized without changing decoded pixels; textual PNG metadata,
including Blender's local `tEXt/File` path, is removed and the runner guards
against its reintroduction.
The setup document records the command, report hashes, source preservation,
logical determinism, anti-false-pass, privacy and rollback evidence.

## Dependency graph

```text
T4.01 contract/authority
  └── T4.02 pure furniture plan
        └── T4.03 spatial validation
        └── T4.04 Blender overlay
              └── T4.05 normalized furniture + comparison
                    └── T4.06 real acceptance and documentation
```

T4.03 can be implemented after T4.02 and reviewed independently. T4.04 needs
T4.02 and the room plan API but must remain independent of T4.05. T4.05 can
develop synthetic adapters after the overlay contract is fixed, but its real
scene connection waits for T4.04. T4.06 is the only task that creates the
acceptance layout, derived binary and preview.

## Gates and evidence policy

Every task records its own pure tests and `git diff --check`. The complete
slice additionally re-runs the room gates so a furniture change cannot hide a
regression in Slices 001–003. Blender is used only in T4.04/T4.05/T4.06 and only
with explicit read-only source handling and a new output path.

Evidence must distinguish:

- `PASS`: command or test actually ran and passed;
- `NO APLICA`: a deliberately excluded capability, such as real assets in v1;
- `PENDIENTE DE INFRAESTRUCTURA`: a check unavailable for an external reason;
- `NO EJECUTADO`: intentionally not part of the current task.

No report may label synthetic furniture as measured or call proxy intersection
constructive geometry.

## Reversal and compatibility

Before T4.06, rollback is removal of the new furniture modules, tests and
contract artifacts; no room artifact is involved. After T4.06, remove only
the derived furniture layout, preview and `.blend`, preserving the source
architectural `.blend` and all room artifacts. A future asset replacement must
consume the same item ID, dimensions, anchor and transform semantics rather
than changing placement data.

Room v1, room v1.1, `room-scene-adapter-1`,
`room-scene-comparison-1`, the historical golden and existing artifacts remain
bit-for-bit compatible. Furniture versions are additive and independent.

## Review checkpoints

1. Review T4.01 contract before creating a schema or acceptance layout.
2. Review T4.02/T4.03 pure plan and spatial findings before using Blender.
3. Review T4.04 ownership and architecture-before/after evidence before
   accepting any derived scene.
4. Review T4.05 normalized/comparison report and anti-false-pass coverage.
5. Review T4.06 artifacts, privacy, hashes and complete diff before any commit
   or PR.
