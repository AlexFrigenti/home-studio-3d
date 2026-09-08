# Room Scene Comparison Validation

## Scope

This document records the reproducible validation boundary for the real
`living-room-main` room in slice 003:

```text
canonical room JSON
    -> validated room
    -> generation plan
    -> normalized Blender scene
    -> ComparisonReport
```

The comparison is one-way from measurements to the derived scene. Blender is
not a source of truth, and the scene is never promoted back into measurements.
The slice does not create constructive opening geometry or boolean cuts; the
six openings remain explicit visual proxies.

All paths below are repository-relative and all commands are run from the
repository root.

## Versions

| Contract | Role |
| --- | --- |
| `room-v1-generator-1` | Current v1 plan contract; its historical golden remains intact. |
| `room-v1.1-generator-1` | Historical generator contract materialized by the preserved pre-T3.05-P scene; not the current acceptance contract. |
| `room-v1.1-generator-2` | Current v1.1 generation-plan and scene contract. |
| `room-scene-adapter-1` | Normalized Blender-scene adapter contract. |
| `room-scene-comparison-1` | Generated `ComparisonReport` output contract. |

The current acceptance uses `room-v1.1-generator-2`. The historical
`room-v1.1-generator-1` artifact is preserved for provenance and geometry
equivalence only. The v1 contract `room-v1-generator-1` and its golden
signature remain supported and unchanged.

## Real room

- Room: `living-room-main`
- Canonical input: `measurements/rooms/living-room-main.json`
- Schema: `1.1`
- Units: metres (`m`)
- Current generation-plan version: `room-v1.1-generator-2`
- Current logical plan signature:
  `182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a`
- Current scene signature:
  `490071b899fbfb442f9b14fc3f71e2607c5449b0f1a7f270605040c09513a30b`
- Scene adapter: `room-scene-adapter-1`
- Normalized scene: 31 managed entities, 22 walls, 6 `opening_proxy`, 1
  floor, 1 `preview_camera`, 1 `preview_light`, and 0 fixed elements.

## Canonical room facts

- 22 boundary segments/walls.
- 6 openings: P1, P2, V1, V2, V3 and V4.
- Room height: `2.50 m`, `measured`.
- `wall-05`: `0.45 m` observed and `0.47 m` effective geometry, reconciled
  and `derived`.
- `wall-16`: `1.00 m` observed and `0.99 m` effective geometry, reconciled
  and `derived`.
- V2 (`window-v2`): offset `0.64 m`, `derived`; width `2.40 m`, `measured`.
- Six wall thicknesses are `0.08 m`, `measured`.
- The other sixteen wall thicknesses remain `unknown` and use the explicit
  `0.10 m` derived fallback for materialization.
- There are zero active vertical opening proxies.
- Every opening has `proxy_only=true` and `constructive_geometry=false`.

These fallbacks and derived values do not promote unknown source measurements
to measured values.

## Artifacts

| Artifact | Role | SHA-256 |
| --- | --- | --- |
| `blender/scenes/review/2026-09-07-living-room-main-v1.1-regenerated.blend` | Historical generator-1 scene; preserved and not overwritten. | `79D9ECCFE874A0DFA507638871462F260C6BD678C8A5E78860461B3A71911DC5` |
| `blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend` | Current generator-2 scene used for T3.06 real acceptance. | `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280` |
| `renders/previews/2026-09-08-living-room-main-v1.1-generator-2/qa-top-orthographic.png` | Current technical QA preview; 167944 bytes. | `D145DDD3473F02ABCC45FAC613158CEC02C1D4C7CA86656D11CFA3D3ED27915E` |

No artifact was regenerated or modified during T3.08/T3.09. The preview is
technical QA evidence, not an artistic approval gate.

## Generation and validation evidence

The following results were obtained during the authorized T3.05/T3.06 real
acceptance and are reused here without reopening Blender:

- Canonical room validation: `VALID`.
- `build_generation_plan(room)`: PASS; current version and logical signature
  are recorded above.
- `compare_room_to_plan(room, plan)`: `valid=true`, errors `0`, warnings `0`,
  info `0`.
- `GENERATION_VALID`: PASS.
- `SCENE_VALID`: PASS.
- `normalize_blender_scene(scene)`: PASS; adapter version and normalized
  entity inventory are recorded above.
- `compare_plan_to_scene(plan, normalized_scene)`: `valid=true`.

The real Blender acceptance is intentionally not repeated in this
documentation-only checkpoint. Its evidence is the versioned generator-2
artifact and the T3.06 acceptance record.

## Historical/current geometry equivalence

The normalized historical generator-1 scene and the current generator-2 scene
were compared through an explicit semantic geometry projection:

- `GEOMETRY_EQUIVALENT = PASS`.
- Common projection hash:
  `31c7a1698c0479a34bdd8e276b6e06fbd0c1dbf2ab90378dfcb3d2a2583cd82f`.
- Unexpected geometric differences: `0`.

The only expected differences were contractual metadata changes caused by the
generator bump:

1. root `hs3d_generator_version`;
2. root `hs3d_logical_signature`;
3. preview-camera generator version;
4. preview-light generator version.

## Comparison acceptance

For the current generator-2 scene:

- `comparison_stage=plan_to_scene`.
- `valid=true`.
- `errors=0`.
- `warnings=0`.
- `info=0`.
- `checked_entities=29`.
- ComparisonReport logical hash:
  `db50f1bd661e8ef3be8966a8c62b1e64ede9ff14f79c468e2ccaecc22f1ef3fe`.
- NormalizedScene logical hash:
  `784b027af6ffd851561e57d4f20378c06f2ec96cbb5cf57c177a6064c2e182d6`.

These two logical hashes are evidence from this acceptance, not permanent
golden values.

## Anti-false-pass evidence

Independent deep-copy mutations produced the following stable failures:

| Mutation | Result |
| --- | --- |
| Wall translation `+0.01 m` | `geometry_value_mismatch` |
| Wall mesh vertex `+0.01 m` | `geometry_value_mismatch` |
| Wall thickness metadata `+0.01 m` | `wall_thickness_mismatch` |
| Opening `proxy_only` change | `proxy_flag_mismatch` |
| Materialized `source_id` change | `source_id_mismatch` |

The independent compound checks also passed: correct metadata with corrupt
geometry is `INVALID`, and correct geometry with corrupt metadata is
`INVALID`.

## Determinism and mutation safety

The real acceptance recorded:

- repeated normalization with identical normalized-scene serialization;
- repeated comparison with identical report serialization, findings order and
  summary;
- unchanged room input;
- unchanged generation plan input;
- unchanged original normalized scene;
- unchanged Blender scenes during read-only validation;
- no save operation during read-only validation.

## Test and quality gates

The pure gates for this slice are:

```text
python blender/scripts/measurements/validate_measurements.py measurements/fixtures/room-v1-synthetic.json
python blender/scripts/measurements/validate_measurements.py measurements/fixtures/room-v1.1-reconciliation-synthetic.json
python blender/scripts/measurements/validate_measurements.py measurements/rooms/living-room-main.json
python -c "import json,sys; from pathlib import Path; sys.path.insert(0,'blender/scripts/measurements'); import generate_room, compare_room_scene; room=json.loads(Path('measurements/rooms/living-room-main.json').read_text(encoding='utf-8')); plan=generate_room.build_generation_plan(room); report=compare_room_scene.compare_room_to_plan(room,plan); raise SystemExit(0 if report.valid else 1)"
python -m unittest -q tests.measurements.test_room_scene_comparison
python -m unittest -q tests.measurements.test_normalize_room_scene
python -m unittest -q tests.measurements.test_room_generation
python -m unittest discover -s tests/measurements -p 'test_*.py' -q
python -m unittest -q tests.measurements.test_room_v1_validation
python -m compileall -q blender/scripts/measurements tests/measurements
python -c "import json; from pathlib import Path; paths=sorted(Path('measurements').rglob('*.json')); [json.loads(p.read_text(encoding='utf-8')) for p in paths]; print(f'JSON_FILES_VALID {len(paths)}')"
git diff --check
```

The recorded results are:

- comparison: `137/137 PASS`;
- normalization: `22/22 PASS`;
- generation: `34/34 PASS`;
- measurement suite: `230/230 PASS`;
- historical suite: `37/37 PASS`;
- v1, v1.1 and real-room JSON validators: `VALID`;
- `build_generation_plan(living-room-main)`: PASS;
- `compare_room_to_plan(living-room-main)`: `valid=true`, all counters `0`;
- JSON syntax: `JSON_FILES_VALID 5`;
- v1 golden: exact match
  `1105946a0dfe0088f5ad59da4178939644305b0d09b94022bfe5c87d9dde36f0`;
- Python syntax: PASS;
- JSON syntax: PASS;
- `git diff --check`: PASS.

`build_generation_plan(room)`, `compare_room_to_plan(room, plan)`,
`normalize_blender_scene(scene)` and
`compare_plan_to_scene(plan, normalized_scene)` are Python entrypoints, not
additional CLI tools. The real-scene `GENERATION_VALID`, `SCENE_VALID` and
Blender normalization/comparison evidence is reused from T3.06 and is not
claimed as newly executed in this checkpoint.

## Privacy

The reviewed slice contains:

- no real photographs, EXIF, LiDAR or photogrammetry data;
- no credentials, tokens, passwords or private keys;
- no personal absolute paths in versioned documentation or artifacts;
- no external asset payloads.

`hs3d_input_path` may exist as generator-side metadata, but it is excluded
from `NormalizedScene`; the normalization tests protect that boundary.
`source_id`, status, method and uncertainty remain governed by the room/plan
contract. Only provenance actually materialized by Blender is available to
`plan_to_scene`.

## Provenance boundaries

The v1.1 generation plan transports rich provenance, including observed values,
effective geometry, status, fallback and reconciliation information. The
Blender scene materializes only a contract-defined subset. The comparator:

- validates metadata that is actually materialized;
- does not require non-materialized per-field `method`, `uncertainty`,
  `reconciliation_id` or `delta_m`;
- does not reconstruct missing scene provenance from the room during
  `plan_to_scene`;
- never promotes `unknown` to `measured`;
- preserves source IDs and explicit fallback semantics where materialized.

## Reproducibility and infrastructure limits

This checkpoint is reproducible from repository-relative JSON, Python
entrypoints, tests, versioned artifacts and the hashes above. It does not
require regenerating the scene. Blender 5.2.1 LTS CLI background was used for
the prior real acceptance; Blender/MCP was deliberately not used for this
documentation checkpoint.

Known non-blocking limitations are:

- scene provenance is partial by contract;
- arbitrary Blender parent hierarchies are not supported by the adapter;
- openings are proxies and have no constructive/boolean geometry;
- sixteen wall thicknesses remain unknown at source and use explicit derived
  fallbacks for materialization;
- `opening_direction` remains unknown;
- the historical `room-v1.1-generator-1` scene is not accepted as the current
  generator-2 contract;
- the known BlenderMCP/`get_addon_status` infrastructure debt remains outside
  this slice.

These limitations do not invalidate the current acceptance; they define the
scope boundary for later work.
