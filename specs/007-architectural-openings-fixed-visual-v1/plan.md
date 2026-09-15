# Architectural Openings & Fixed Visual Elements v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir una capa visual procedural de los seis openings contractuales de `living-room-main` sobre una nueva derivada, sin modificar la arquitectura ni inventar fixed elements.

**Architecture:** Un helper puro leerá el room/generation plan y producirá un contrato lógico determinista. Una operación posterior en Blender GUI/MCP materializará ese contrato bajo el root hermano `HSARCH_VISUAL_living-room-main_slice-007_v1`, reutilizando la presentación de Slice 006 y guardando únicamente una nueva derivada. T7.03 mantiene el plan geométrico puro separado de un plan de materiales puro y de su adaptador Blender.

**Tech Stack:** Python estándar para contrato, validación e inventario; JSON room-v1.1; Blender 5.2.1 LTS en GUI; Blender MCP local en `127.0.0.1:9876`; sin dependencias, assets o texturas externas.

**Spec:** `specs/007-architectural-openings-fixed-visual-v1/spec.md`

## Global Constraints

- Source arquitectónico read-only: `blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend` con SHA-256 `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.
- Input visual read-only: Slice 006 derived con SHA-256 `74EA4AF015C95FADD85EC5007E806A550D9F4E88CCC132E35A274ED3493FAC1D`.
- Autoridad geométrica: room-v1.1 generation plan; no lectura inversa desde la geometría visual.
- Target real: exactamente 2 doors, 4 windows y `fixed_elements=[]`.
- Todas las aproximaciones visuales deben marcarse `procedural_synthetic`; no se promueven a medidas.
- No modificar `measurements/`, schemas, room pipeline, FurniturePlan, Slice 005, Slice 006, cámara o luces.
- No abrir el source como escena de trabajo; usar `Save As` para la derivada
  Slice 007 materializada.
- No generar swings, animación, booleanos, decoración, assets externos ni render hasta la fase visual autorizada.
- No prometer determinismo binario de `.blend` o PNG; solo determinismo lógico y privacidad verificable.

## Archivos y áreas afectadas

- Crear durante implementación: `blender/scripts/architecture/generate_architectural_visual.py`.
- Crear durante implementación: `tests/architecture/test_architectural_visual_contract.py`.
- Crear durante T7.02: `blender/scripts/architecture/architectural_visual_geometry.py` y `blender/scripts/architecture/materialize_architectural_visual.py`.
- Crear durante T7.02: `tests/architecture/test_architectural_visual_geometry.py`.
- Crear durante integración T7.02: `blender/scenes/review/2026-09-10-living-room-main-slice-007-architectural-visual-v1.blend`.
- Salida opcional de review únicamente si la inspección visual la requiere:
  `renders/previews/living-room-main-slice-007-architectural-visual-v1/review-v1.png`.
  No se requirió ni creó PNG de Slice 007; la evidencia de viewport fue suficiente.
- Crear ahora: `spec.md`, `plan.md` y `tasks.md` de este directorio.
- Modificar `measurements/`, schemas, scripts room, FurniturePlan, Slice 006 o `.blend` existentes: `No aplica; prohibido por el alcance`.

## Fases

1. Congelar el contrato arquitectónico y la matriz de viabilidad sin crear geometría.
2. Implementar el contrato puro para frames, hojas neutras, vidrio y banda de alféizar.
3. Implementar y verificar descriptores geométricos con tests deterministas y casos malformed/no-mutation.
4. Materializar la capa en una nueva derivada mediante Blender GUI/MCP y detenerse para aceptación visual.
5. Auditar idempotencia, preservación de arquitectura, privacidad y render, sin exigir hashes binarios.
6. Documentar evidencia y cerrar el slice solo con todos los gates y aceptación humana.

## Validaciones

- Validación del room JSON y `build_generation_plan`; la firma esperada es `182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a`.
- Resolución exacta de IDs, tipos, offsets, dimensiones, depths, sills, wall IDs, vectores de wall y estados de provenance.
- Rechazo explícito de tipos desconocidos, `opening_direction` interpretable como swing y `fixed_elements` no vacío para este target.
- Tests puros para naming, ownership, hierarchy, transforms, material assignments, no mutation y repetición determinista.
- `git diff --check`, Python syntax, JSON syntax, privacy text/binary y hygiene.
- Validación visual en Blender GUI/MCP, con cámara/luces de Slice 006 reutilizadas y STOP VISUAL humano.
- Verificación de source SHA, Slice 006 derived SHA y ausencia de mutaciones en roots técnicos.
- PNG final, si existe, validado con el guard de privacidad existente; no se usa su SHA como golden.

## Estrategia de reversión y compatibilidad

La implementación se ejecuta sobre una copia `Slice 007` de la derivada de
Slice 006. El rollback normal es eliminar esa nueva derivada/capa y regenerarla
desde los contratos, sin guardar sobre el source ni sobre la derivada aprobada
de Slice 006. La compatibilidad se conserva porque la capa visual vive fuera
de `HS3D_ROOM_*`, `HSLAYOUT_*` y de las colecciones técnicas gestionadas por
los normalizers existentes.

## Dependencias externas

Ninguna. Blender 5.2.1, Blender MCP local y Python estándar ya forman parte
del entorno del repositorio. No instalar addons, paquetes, servicios, assets ni
texturas.

## Secuencia de implementación propuesta

### T7.01 — Architectural visual contract

**Files:**
- Create: `blender/scripts/architecture/generate_architectural_visual.py`
- Test: `tests/architecture/test_architectural_visual_contract.py`
- Read-only inputs: `measurements/rooms/living-room-main.json`, `blender/scripts/measurements/generate_room.py`, Slice 006 contracts.

**Interfaces:**
- Consumes: validated room JSON and effective generation plan.
- Produces: a JSON-compatible architectural visual contract with six opening entries, deterministic names, source IDs/statuses, visual approximations and an empty fixed-element channel.

- [x] Define `ARCHITECTURAL_VISUAL_CONTRACT_VERSION = "architectural-visual-contract-1"` and `ARCHITECTURAL_VISUAL_GENERATOR_VERSION = "slice-007-architectural-visual-generator-1"`.
- [x] Define a builder that resolves only `door` and `window` entries, sorts by ID, copies effective geometry fields without mutating input, and rejects unsupported kinds or non-empty fixed elements for the target.
- [x] Preserve `opening_direction="unknown"`; represent `closed_neutral` only as a presentation capability, never as physical door inference.
- [x] Freeze the capability, ownership, root/collection and object naming boundary without creating geometry or materials.
- [x] Add tests for the six real IDs, exact type counts, field statuses, source IDs, fixed-element empty invariant, deterministic serialization and input non-mutation.
- [x] Run the pure contract tests and room validator; result is PASS with the six-entry contract.

**T7.01 evidence:** the pure helper and its 20 tests pass. The builder uses
only the validated room JSON and effective generation plan, returns a
JSON-compatible contract, rejects unsupported capabilities and fixed-element
input, and does not import Blender or mutate its inputs. T7.02 consumes this
contract without changing its authority boundary.

### T7.02 — Opening visual geometry v1

**Files:**
- Create: `blender/scripts/architecture/architectural_visual_geometry.py`.
- Create: `blender/scripts/architecture/materialize_architectural_visual.py`.
- Create: `tests/architecture/test_architectural_visual_geometry.py`.
- Create via GUI/MCP Save As: `blender/scenes/review/2026-09-10-living-room-main-slice-007-architectural-visual-v1.blend`.

**Interfaces:**
- Consumes: T7.01 contract entries.
- Produces: deterministic component descriptors for `FRAME`, `DOOR_INFILL` (doors, with stable `LEAF` object names), `GLASS` (windows) and `SILL` (windows).

- [x] Generate frame descriptors from `position_m`, `direction`, `outward`, width, effective height and measured depth; use the fixed visual parameters from the spec and label them synthetic.
- [x] Generate door leaves only as centered, closed, planar slabs; never compute a swing from `unknown`.
- [x] Generate window glass as a flat procedural panel inside the measured window envelope.
- [x] Generate a flush sill band at measured `sill_height_m`; do not add overhang or claim a measured profile.
- [x] Generate no `FixedElementVisual` component for `living-room-main`; fail explicitly if fixed inputs are supplied.
- [x] Test component counts, names, transforms, dimensions, no `.001/.002`, no duplicate component IDs and repeated descriptor equality.

**T7.02 evidence:** the initial implementation was visually insufficient: the
frame profile was 0.04 m, the frame/panel front gap was 0.005 m and all local
component centers shared the same depth plane. The refinement RED run
reproduced two failures before the production change. GREEN now passes 34/34,
including the frame-profile, three-sided/perimeter and recess assertions. The planner uses the
single synthetic `frame_profile_width_m=0.05` and explicit
`panel_recess_m=0.01`; frames/sills are advanced within their visual depth and
glass/door infills are recessed. Blender GUI/MCP rematerializó únicamente
`HSARCH_VISUAL_*` in the existing Slice 007 derived scene and compare two
passes. Blender GUI/MCP (`bpy.app.background=false`, `VIEW_3D` disponible)
rematerializó dos veces únicamente los meshes de `HSARCH_VISUAL_*`; ambas
pasadas conservaron los mismos 22 nombres, 12 collections de escena y 78
objects totales, sin `.001/.002`. The inventory remains 6 roots, 6 frames, 2
neutral door infills, 4 glass panels, 4 sill bands and an empty
`FixedElementVisual`. No materials are created at this T7.02 checkpoint; T7.03
was intentionally out of scope at that stage. Human visual acceptance was
completed later and is recorded in the T7.03 evidence below.

The final depth refinements add no semantic component and keep
`frame_profile_width_m=0.05`. All six frames now use
`depth/2 + frame_projection_m` as their synthetic room-facing front. Window
glass and door infills are placed `panel_recess_m=0.01` behind the frame back;
`door-main` keeps its width/height and one-piece infill, while `door-terrace`
is depth-bounded to 0.02 m. Window geometry remains unchanged. The saved
derived scene is 178386 bytes with puntual SHA
`9CE444108950CBF715BF295EDC0256C79C7B10AA7AFD8BDB31F72A3F3CB39CE4`, not a
binary golden. Human acceptance was subsequently completed and approved after
the final door review; T7.02 is frozen for T7.03.

### T7.03 — Architectural materials v1

**Files:**
- Create: `blender/scripts/architecture/architectural_visual_materials.py`.
- Modify: `blender/scripts/architecture/materialize_architectural_visual.py`.
- Create: `tests/architecture/test_architectural_visual_materials.py`.
- Create: `blender/scripts/architecture/architectural_visual_visibility.py`.
- Create: `blender/scripts/architecture/materialize_architectural_visual_visibility.py`.
- Create: `tests/architecture/test_architectural_visual_visibility.py`.

**Interfaces:**
- Consumes: T7.01/T7.02 component descriptors.
- Produces: four deterministic material descriptors and role-to-component assignments.
- Produces: a deterministic, reversible presentation-visibility policy for the six represented technical opening proxies.

- [x] Freeze `hs3d_visual_mat_arch_opening_frame_v1`, `hs3d_visual_mat_arch_door_leaf_v1`, `hs3d_visual_mat_arch_window_glass_v1` and `hs3d_visual_mat_arch_sill_v1` with stable `material_id`, semantic role, base color, roughness, metallic and `procedural_synthetic` provenance.
- [x] Keep assignments one-to-one by component role and reject external image nodes, texture paths, duplicate suffixes and unowned materials.
- [x] Test stable parameters, assignment completeness, malformed material rejection and no input mutation.
- [x] Keep all six technical proxies in `Openings` and apply visibility-only presentation overrides to exactly those proxies when their `HSARCH_VISUAL_*` roots exist.
- [x] Preserve proxy name, mesh identity, dimensions, transforms, material, metadata and collection; exclude visibility flags from the proxy geometry fingerprint.
- [x] Validate reversible `hide_viewport`/`hide_render` application, deterministic targeting, idempotence and no changes to unrelated scene domains.

**T7.03 evidence:** the T7.03 pure material plan passes 20/20 tests. It
produces exactly four materials and 16 deterministic assignments: 6 frames,
4 glass panels, 2 door infills and 4 sill bands, with one slot per mesh. The
Blender GUI/MCP adapter materialized the plan twice in the existing Slice 007
scene, reused exactly four owned datablocks, retained 22 visual objects, 12
scene collections, 0 fixed objects and the live geometry signature
`11632:642518` on both passes. All materials use only Principled BSDF plus
Material Output; no image nodes, external paths or duplicate suffixes were
introduced. The scene remains on `BLENDER_EEVEE`, and T7.03 was approved by
human visual review through the material-preview closeups. The current glass
calibration is base color `[0.88, 0.90, 0.92, 1.0]`, roughness `0.06`, alpha
`0.16` and transmission weight `0.88`; one additional calibration was allowed
after the first pass, without changing nodes, engine, geometry or other
materials. The pre-policy viewport still showed a predominantly blue panel, so
the policy below was added before visual acceptance; T7.03 is now accepted.

The A/B diagnosis found that the blue panel was the opaque technical proxy
behind/overlapping the visual glass. The pure visibility plan and Blender
adapter now apply an explicit `presentation visibility override` to exactly
`HS3D_DOOR_door-main`, `HS3D_DOOR_door-terrace`, `HS3D_WINDOW_window-v1`,
`HS3D_WINDOW_window-v2`, `HS3D_WINDOW_window-v3` and
`HS3D_WINDOW_window-v4`. Each remains in `Openings`, with `hide_viewport=True`
and `hide_render=True` in the derived review scene; no proxy geometry,
transform, material, metadata or collection ownership is changed. The HSARCH
inventory remains 6 roots, 16 meshes, 22 visual objects and zero fixed objects.
The policy was applied twice with equal results and independent proxy
fingerprints before/after. T7.03 is now accepted by human visual review.

### T7.04 — Scene integration & visual review

**Files:**
- Read-only output from T7.02: `blender/scenes/review/2026-09-10-living-room-main-slice-007-architectural-visual-v1.blend`.
- Modify: none of the existing source, Slice 006 derived scene, room collections, FurnitureVisual or ReviewPresentation objects.
- Evidence: viewport capture and review render only after the visual checkpoint.

**Interfaces:**
- Consumes: T7.01–T7.03 contract and read-only Slice 006 derived scene.
- Produces: a new derived scene with `HSARCH_VISUAL_living-room-main_slice-007_v1` and `ArchitecturalVisual` collections.

- [x] Confirm Blender 5.2.1 GUI, `bpy.app.background=false`, `VIEW_3D` and MCP localhost before materialization.
- [x] Create only the new sibling root and its `OpeningVisual`/`FixedElementVisual` children; ownership must be exclusive.
- [x] Reuse Slice 006 `ReviewPresentation` camera/key/fill without adding or changing camera/light parameters.
- [x] Verify numerically all six visual envelopes against the generation plan and confirm the technical six proxies remain unchanged.
- [x] Inspect the viewport and, only if needed, generate one final 960×720 review PNG in the Slice 007 preview path.
- [x] Stop and obtain explicit human approval for recognition, legibility, no functional clipping and architecture context.

**T7.04 evidence:** the existing Slice 007 derived scene was inspected through
the live Blender GUI/MCP session. Blender 5.2.1 LTS reported
`bpy.app.background=false`, `VIEW_3D` and `BLENDER_EEVEE`. The integrated layer
contains the expected root and three visual collections, 6 opening roots, 16
meshes, 22 visual objects and 0 fixed objects. All six technical proxies remain
in `Openings` with their presentation visibility override; their contractual
data is unchanged. ReviewPresentation still contains exactly the existing
review camera, key area and fill area. Viewport evidence was captured for room
context, windows and doors; no new render was needed. The explicit human
acceptance confirmed joint recognition, architectural legibility, FurnitureVisual
integration and absence of functional clipping. T7.04 is approved and frozen;
no additional changes are required.

### T7.05 — Reproducibility, mutation & privacy validation

**Files:**
- Modify: `tests/architecture/test_architectural_visual_contract.py` if coverage requires it.
- Create: no new production artifact beyond the approved Slice 007 derivation/render.

**Interfaces:**
- Consumes: approved derived scene, T7 contract, source hash and existing review PNG guard.
- Produces: normalized logical inventory and validation evidence.

- [x] Read the normalized inventory twice and compare collections, names, types, ownership, hierarchy, transforms, dimensions, metadata, materials, assignments and fixed-element emptiness.
- [x] Re-run the pure contract twice without saving Blender and confirm identical logical output; do not destroy the approved scene to simulate idempotence.
- [x] Confirm source SHA and Slice 006 derived SHA are unchanged, no technical collection/material/camera/light mutation occurred, and no external/private paths exist.
- [x] Validate the applicable preview evidence with the existing byte-level guard; no Slice 007 PNG exists and no PNG was generated for this audit.
- [x] Run relevant room/furniture/historical validators, syntax checks, privacy/hygiene checks and `git diff --check`.

**T7.05 evidence:** the explicit suites totalled `555/555 PASS`:
architecture `92/92`, measurements `230/230` and furniture `233/233`, with
validators, generation plan, `room_to_plan`, spatial, golden, Python AST
`42/42`, JSON `11/11`, privacy/hygiene and whitespace also passing. The
generic repository discovery returned `0 tests`; it is recorded as a known
discovery debt, not as a passing suite. Historical Blender runners that
regenerate or mutate scenes were deliberately omitted. The normalized Blender
inventory was read twice with equal output; pure contract/idempotence checks
were equal; `bpy.data.is_dirty=False`; source and Slice 006 hashes and all
contract signatures were preserved. Live Blender GUI/MCP worked with Blender
5.2.1 LTS, `bpy.app.background=False` and `VIEW_3D`; the historical
`get_addon_status` import error remains non-blocking and production was not
changed to address it. No contractual Slice 007 PNG exists.

### T7.06 — Documentation & final audit

**Files:**
- Modify: `spec.md`, `plan.md`, `tasks.md` only for actual evidence.
- Optional, only if factually required: `README.md` or `PROJECT_CONTEXT.md`; broad cleanup is out of scope.

**Interfaces:**
- Consumes: all T7 evidence and human acceptance.
- Produces: final design/implementation audit and review-ready branch.

- [x] Record human approval and all accepted non-blocking limitations without converting them into defects.
- [x] Reconcile spec/plan/tasks with actual implementation and mark only evidenced tasks `[x]`.
- [x] Audit the complete diff for scope, privacy, provenance, binary artifacts, temporary files and paths outside authorization.
- [x] Confirm no Slice 008 or unrelated future scope was introduced.
- [x] Leave staging, commit, push and PR decisions to the authorized follow-up workflow.

**T7.06 evidence:** the final audit reconciled the three Slice 007 documents
with the implementation, tests, derived scene and inherited contracts. Scope is
limited to the HSARCH procedural architectural-opening layer: 6 roots, 16
meshes, 6 frames, 4 glass panels, 2 neutral door infills, 4 sill bands, 0 fixed
visual objects and 22 managed HSARCH objects. The exact four procedural
materials and approved glass calibration remain unchanged. Technical opening
proxies remain the authority in `Openings`; `hide_viewport=True` and
`hide_render=True` are presentation-only in the derived scene and
`hide_set/hide_get` was not used as a substitute. Architecture, FurniturePlan,
FurnitureVisual, ReviewPresentation, camera, lights, source and Slice 006
derived remain intact. No private path, username, sensitive metadata, new
`.blend1` generated by Slice 007, temporary file, accidental screenshot, Slice
008 artifact or unrelated scope was found. The only `.blend1` observed is the
historical/pre-existing ignored fixture
`blender/scenes/tests/001-foundation-room.blend1`, outside Slice 007 scope.
The live glass material audit observed Base Color
`(0.88, 0.90, 0.92, 1.0)`, Roughness `0.06`, Metallic `0.0`, Alpha `0.16`,
Transmission Weight `0.88`, IOR `1.5`, `surface_render_method=DITHERED` and
the API alias `blend_method=HASHED`. Human visual acceptance remains recorded only for T7.02, T7.03 and
T7.04; no new visual acceptance is claimed for T7.05 or T7.06.

**Final state:** `SLICE 007 FINAL AUDIT PASSED — READY FOR PRECOMMIT REVIEW`.

## Plan self-review

- Spec coverage: the six-opening inventory, support matrix, reduced scope,
  architecture, failure handling, privacy, human acceptance and all six T7
  tasks are covered above.
- Placeholder scan: no task depends on an unspecified opening type, fixed
  element, direction, header measurement, external asset or private path.
- Type consistency: T7.01 produces the contract consumed by T7.02/T7.03;
  T7.02 produces geometry consumed by the pure T7.03 material plan and its
  Blender adapter; T7.04 integrates/reviews the combined result; T7.05 validates the same inventory;
  T7.06 documents only evidenced results.
- Scope check: implementation is a single vertical opening-visual layer;
  fixed-element output is explicitly empty for the real target.
