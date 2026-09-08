# Real-room Scene Comparison and Validation v1 Implementation Plan

> **For agentic workers:** Execute this plan task-by-task only after the slice specification has been reviewed and approved. Keep every implementation task independently testable.

**Goal:** Add a deterministic, reusable comparison between canonical room data, the generation plan and a normalized generated-scene representation without changing measurement schemas or real-room data.

**Current checkpoint:** T3.01–T3.04, T3.05-P, T3.05 and T3.06 are implemented
and validated. T3.06 has passed real-scene acceptance against a new
generator-2 artifact, with the historical generator-1 artifact preserved;
later scene work remains pending.

**Architecture:** Keep a pure-Python comparison core independent of `bpy`. Add a read-only Blender adapter that maps the existing generated scene and custom properties into a normalized representation, then produce a stable `ComparisonReport` from the core. Preserve the existing generator and scene validator contracts; integrate only the minimum delegation and metadata checks needed by the new comparison.

**Tech Stack:** Python standard library, JSON, existing room schemas v1/v1.1, `unittest`, Blender `bpy` only for the explicitly authorized integration gate.

**Spec:** `specs/003-real-room-scene-comparison-and-validation/spec.md`

## Global Constraints

- `measurements/` remains the source of truth; no scene-to-measurement promotion.
- room-v1 and its golden logical signature remain unchanged.
- room-v1.1 reconciliation, status and fallback metadata remain explicit.
- `MATH_TOLERANCE_M = 1e-6 m` is the initial computational comparison tolerance.
- Area comparisons use `m²` and a tolerance derived from coordinate propagation;
  `1e-6 m` is never reused as an area tolerance.
- Observation uncertainty is context, not an automatic plan-to-scene tolerance.
- No boolean openings, new real measurements, new rooms, furniture, decoration, photos, LiDAR or MCP changes.
- Unknown values remain unknown; fallback values must remain marked derived and fallback-enabled.
- The comparison must not depend on Blender object ordering or personal paths.
- The historical `.blend` and preview artifacts are immutable evidence. T3.06
  uses a separately generated generator-2 review artifact and never overwrites
  the historical scene.
- Gates must report real `PASS`, `FAIL`, `NO APLICA`, `PENDIENTE DE INFRAESTRUCTURA` or `NO EJECUTADO` states.

## Files and responsibilities

The implementation uses these focused boundaries:

- Create `blender/scripts/measurements/compare_room_scene.py`: pure comparison models, finding codes, tolerance checks, deterministic sorting and report serialization.
- Create `blender/scripts/measurements/normalize_room_scene.py`: keep the
  pure normalized-scene contract and the duck-typed read-only Blender adapter
  together without importing `bpy` at module load time.
- Modify `blender/scripts/measurements/validate_generated_room.py` only to invoke the adapter/core and retain the existing CLI behavior where compatible.
- Modify `blender/scripts/measurements/generate_room.py` only for the additive
  v1.1 provenance block required by T3.05-P; do not refactor unrelated
  generation paths.
- Create `tests/measurements/test_room_scene_comparison.py` for pure core and mutation tests.
- Create normalized test fixtures under `measurements/fixtures/` only when deriving them in test code would hide the adapter contract.
- Add `docs/setup/003-room-scene-comparison-validation.md` for commands, evidence and explicit Blender limitations.
- Reuse the existing `HS3D_ROOM_<room_id>` root, child collection roles,
  `HS3D_*` names and `hs3d_*` metadata to identify managed entities; do not
  introduce a second ownership convention.
- Do not modify `measurements/schema/`, `measurements/rooms/`, existing fixtures or binary artifacts unless a reviewed contract gap proves unavoidable.

## Data flow and interfaces

The implementation should expose stable interfaces equivalent to:

```python
def normalize_scene(scene_payload: object) -> dict[str, object]:
    raise NotImplementedError

def normalize_blender_scene(scene_source: object) -> dict[str, object]:
    raise NotImplementedError

def compare_room_to_plan(room: dict[str, object], plan: dict[str, object]) -> ComparisonReport:
    raise NotImplementedError

def compare_plan_to_scene(plan: dict[str, object], scene: dict[str, object]) -> ComparisonReport:
    raise NotImplementedError

def compare_room_to_scene(
    room: dict[str, object],
    plan: dict[str, object],
    scene: dict[str, object],
) -> ComparisonReport:
    raise NotImplementedError
```

The exact dataclass or dictionary implementation may follow repository style,
but field names and semantics must match the spec before code is written. The
normalized scene must contain canonical IDs, geometry values, source/geometry
statuses, fallback flags, provenance fields and opening flags. It must not
contain raw Blender paths or non-deterministic object handles.

Every finding must include a `comparison_stage` and a nested
`source_context` with `observed`, `effective_geometry` and `scene` contexts.
The first context may be null for a non-measurement entity; the fields must
not duplicate `expected` or `actual` numeric values. Managed entities are
the existing Home Studio 3D descendants of `HS3D_ROOM_<room_id>` with the
roles `floor`, `wall`, `opening_proxy`, `fixed_element_proxy`,
`preview_camera` or `preview_light`. Non-managed objects outside that root are
allowed and ignored; malformed or duplicate managed entities are errors.

The report must reject incompatible `report_version`, `scene_adapter_version`
or `generation_plan_version` when the comparison contract requires a specific
version. Schema version remains an independent capability input.

The report canonicalization must sort findings by severity, comparison stage,
entity type, entity ID, path and code. Entity collections are sorted by ID;
vectors preserve component order; maps use sorted keys; floats are finite and
normalize `-0.0` to `0.0` without pre-comparison rounding. Serialization uses
sorted keys and compact separators. The first implementation needs stable
serialization tests, not a new report golden hash.

Linear comparisons use `1e-6 m`. Area comparisons use `m²` and derive their
computational tolerance from the shoelace coordinate-error bound in the spec;
they must never label `1e-6 m` as an area tolerance. Observation uncertainty
remains context and does not relax plan-to-scene comparison.

## Implementation order

### Task 1: Freeze the authority and report contract

Document the report schema, stage field, nested provenance context, finding
codes, severity rules, managed-entity domain, normalized-scene fields,
version matrix and tolerance policy in tests or contract fixtures before
implementation. Confirm that all fields needed by `living-room-main` already
exist in the current plan/scene metadata.

### Task 2: Build the pure comparison core

Implement room/plan checks and plan/normalized-scene checks without importing
`bpy`. Compare dictionaries by stable IDs, use the explicit computational
tolerance, preserve the three provenance contexts and sort findings using
severity, stage, entity type, entity ID, path and code.

#### T3.04 checkpoint: room-to-plan core

The pure `compare_room_to_plan(room, plan)` transition is implemented in
`blender/scripts/measurements/compare_room_scene.py`. It consumes validated
room/plan dictionaries, compares supported entities by canonical ID, preserves
observed versus effective geometry context, validates v1/v1.1 fallback and
reconciliation metadata, and leaves `scene` as `null`. It does not read files,
import `bpy`, or change the generator's plan behavior. Historical v1 uses
`height_m` and wall height statuses; its duplicated top-level `height_status` is not authoritative
because the existing plan can overwrite it while processing fixed-element
metadata. The v1 logical signature remains unchanged. Fallback constants and
the Shoelace operation are imported from the pure shared
`blender/scripts/measurements/generation_policy.py`; no second fallback policy
is maintained in the comparator.

T3.04 checks the provenance subset exposed by the historical plan and retains
the explicit limitation `not verifiable at room_to_plan with generation-plan
contract current version` for that contract. T3.05-P is now the completed,
additive v1.1 extension described below; it does not start the Blender adapter
or any `plan_to_scene` validation.

#### T3.05-P checkpoint: field-level provenance extension

The schema `1.0` plan remains exactly `room-v1-generator-1`, including its
historical logical signature. The schema `1.1` plan previously emitted
`room-v1.1-generator-1`; it now emits `room-v1.1-generator-2` because the
plan contract gained a top-level `provenance` block. The bump is a contract
version change, not a geometry change.

The block contains deterministic `room`, `boundary`, `walls`, `openings` and
`fixed_elements` maps. The room map also carries the required session metadata
`measurement_method` and `measured_at`. Measurement fields use `observed` and
`effective_geometry` metadata. The transport includes status, uncertainty,
method, note, formula, dependencies and source IDs when present in the room,
plus effective geometry status, fallback metadata and reconciliation metadata
when applicable. Physical `value`/`value_m` fields and geometry coordinates
remain exclusively in their existing plan locations.

`compare_room_to_plan` validates this block only when the plan is
`room-v1.1-generator-2`. It compares provenance by stable IDs and fields,
emits structured provenance/reconciliation/fallback findings, and never
reconstructs unavailable metadata. Existing consumers continue to read the
unchanged geometry keys; the scene validator and Blender path were not
modified. Full plan-to-scene provenance validation remains a later task.

#### T3.05 checkpoint: normalized scene and read-only adapter

`blender/scripts/measurements/normalize_room_scene.py` provides the pure
`normalize_scene(mapping)` core and the `normalize_blender_scene(scene_source)`
read-only extraction boundary. The normalized contract exposes
`scene_adapter_version` (`room-scene-adapter-1`), room identity, explicit
metric/metres units, the managed root, the four managed child collections,
canonical managed entities and their finite transforms, mesh vertices and
materialized `hs3d_*` metadata. Local paths and runtime Blender handles are
excluded.

Managed entities are identified by role and canonical IDs under
`HS3D_ROOM_<room_id>`. Entities and collections are ordered canonically;
unmanaged auxiliary objects outside the root are classified separately, while
duplicate, malformed, wrongly-owned or non-finite managed input raises a
structured normalization error. The adapter never writes to Blender and no
`plan_to_scene` comparison is implemented. Pure/synthetic verification and the
authorized read-only verification against the existing real `.blend` are
complete. The real run confirmed 31 managed entities, stable serialization,
no structural errors, no mutation and an unchanged `.blend` SHA-256
(`79D9ECCFE874A0DFA507638871462F260C6BD678C8A5E78860461B3A71911DC5`).
Scene provenance remains partial and is limited to metadata materialized in
Blender; T3.06 was outside this T3.05 checkpoint and is closed in the
validated plan-to-scene checkpoint below.

### Task 3: Add normalized scene and Blender adapter

Map the existing root collection, four child collections, walls, floor,
openings, fixed elements and preview camera/light to the normalized
representation. Read only the metadata already emitted by the generator.
Ignore non-managed auxiliary objects outside the root; duplicate or malformed
managed entities are rejected with structured normalization errors. Missing
critical fields are rejected; the adapter does not repair, infer or write the
scene.

The T3.05 implementation and its pure/synthetic tests are complete. Real
Blender extraction was verified read-only against the versioned `.blend`; no
scene or preview was regenerated or saved.

### Task 4: Integrate the existing validation entry point

Keep `validate_generated_room.py` usable with its current input contract. Add
the comparison result as an explicit report while preserving the existing
`SCENE_VALID` semantics and avoiding a second independent tolerance policy.

### Task 5: Add regression and compatibility coverage

Cover positive v1, positive v1.1, the real acceptance case and every required
controlled mutation. Assert stable codes, severity, expected/actual context,
`source_context`, `valid`, summary counts, version checks and order
independence. Assert the historical v1 logical signature exactly.

### Task 6: Run authorized real-room integration evidence

Only in the implementation task, and only with explicit authorization, open
the existing versioned `.blend` read-only, normalize it, compare it with the
canonical JSON and record `GENERATION_VALID`, `SCENE_VALID`, comparison result,
determinism and QA visual status. Do not regenerate or overwrite artifacts as
part of this design task.

### Task 7: Document and audit

Record commands, outputs, artifact identities, privacy checks, limitations and
rollback. Review the complete diff and confirm that no schema, JSON, code
outside scope or binary was changed accidentally.

## Test strategy

Pure tests must construct plans from existing fixtures and build controlled
normalized-scene mutations. Required groups are:

- report shape and deterministic serialization;
- v1 compatibility and golden signature;
- v1.1 observed/geometry fields;
- unknown/fallback semantics;
- wall-05/wall-16 reconciliation;
- six opening fields and flags;
- missing/unexpected managed objects, duplicate IDs and malformed normalized
  entities;
- allowed unmanaged auxiliary objects;
- numeric and metadata mismatches;
- provenance, wrong units, incompatible versions and ordering;
- dimensional area tolerance derived from coordinate tolerance.

Blender integration tests remain separate from the pure suite. If Blender is
unavailable, the result is recorded as `PENDIENTE DE INFRAESTRUCTURA` or
`NO EJECUTADO`, never as an invented PASS.

## Compatibility and rollback

The comparator is additive. It consumes validated rooms and existing plans,
does not change schemas and does not mutate input dictionaries. A v1 plan is
checked using its historical fields; v1.1-only reconciliation and fallback
checks activate only when those fields exist. Rollback removes the comparison
module, adapter integration, tests and documentation while leaving the
published JSON and derived scenes untouched.

## Gates

The implementation gate set is:

- fixture v1 validator: `VALID`;
- fixture v1.1 validator: `VALID`;
- `living-room-main` validator: `VALID`;
- pure comparison and existing `tests/measurements` suite: `PASS`;
- historical v1 golden signature: exact match;
- JSON and Python syntax: `PASS`;
- `git diff --check`: `PASS`;
- if Blender integration is in scope for the implementation run:
  `GENERATION_VALID`, `SCENE_VALID`, deterministic signatures and visual QA
  with evidence from the existing artifact, without using those gates to
  claim a result when infrastructure is unavailable.

#### T3.06 checkpoint: validated plan-to-scene comparison

compare_plan_to_scene(plan, normalized_scene) compares the generation plan
with normalized-scene evidence without importing bpy, reading a room, calling
the generator or mutating either input. It supports the published plan
versions room-v1-generator-1 and room-v1.1-generator-2 with
room-scene-adapter-1, compares managed semantic entities by ID, derives
world-space geometry from local vertices plus direct transforms, and checks
scene metadata independently from geometry evidence.

The current generator-scene contract is intentionally narrow: managed mesh
objects have no semantic parent transform, their local vertices are paired
with direct location/rotation/scale values, and the comparator does not claim
support for arbitrary Blender parent hierarchies or other transform graphs.

The pure/synthetic regression suite is green and the real acceptance is closed.
The historical artifact
`blender/scenes/review/2026-09-07-living-room-main-v1.1-regenerated.blend`
remains preserved with SHA-256
`79D9ECCFE874A0DFA507638871462F260C6BD678C8A5E78860461B3A71911DC5`.
Because it materializes the pre-T3.05-P contract `room-v1.1-generator-1`,
acceptance uses the separately generated artifact
`blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend`,
whose SHA-256 is
`352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.
That scene materializes `room-v1.1-generator-2`, logical signature
`182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a` and
`room-scene-adapter-1`. The report is valid with zero errors, warnings and
info; its logical hash is
`db50f1bd661e8ef3be8966a8c62b1e64ede9ff14f79c468e2ccaecc22f1ef3fe`.

Historical/new semantic geometry equivalence passed with no unexpected
differences and common projection hash
`31c7a1698c0479a34bdd8e276b6e06fbd0c1dbf2ab90378dfcb3d2a2583cd82f`.
Controlled anti-false-pass mutations, deterministic serializations and
read-only/no-mutation checks also passed. This closure does not start T3.07.
