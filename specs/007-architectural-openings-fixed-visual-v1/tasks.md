# Tareas: Architectural Openings & Fixed Visual Elements v1

Estados: `[ ]` pendiente · `[~]` en curso · `[x]` validada · `[!]` bloqueada.

> Diseño creado desde `main` después del cierre de Slice 006. Este branch
> contiene el contrato puro validado de T7.01, la geometría visual de T7.02 y
> los materiales procedurales implementados de T7.03; no contiene render final.

## Reglas comunes

- Clasificación T2 por escena Blender, MCP, ejecución privilegiada y protección
  de source.
- Baseline: `living-room-main`, room-v1.1 y la escena derivada visual de Slice 006.
- Autoridad: `measurements/` → `room-v1.1-generator-2` → generation plan.
- Target real: 6 openings tipados, 2 doors, 4 windows y 0 fixed elements.
- `opening_direction=unknown` permanece unknown; no se generan swings.
- Las aproximaciones de perfil, hoja, vidrio y sill son visuales y sintéticas.
- El source arquitectónico y la derivada de Slice 006 son read-only.
- La nueva capa usa `HSARCH_VISUAL_*`; no reutiliza colecciones técnicas ni de furniture.
- Blender GUI + MCP y STOP VISUAL humano son obligatorios para materialización.
- No assets externos, fabricantes, texturas, decoración, medidas nuevas, Slice 008,
  staging, commit, push o PR dentro de este diseño.

## Resumen de tareas

| Estado | Tarea verificable | Validación asociada |
| --- | --- | --- |
| `[x]` | T7.01 — Congelar el contrato arquitectónico de los seis openings y la frontera de fixed elements. | Room validator, generation plan, tests puros y no mutación. |
| `[x]` | T7.02 — Construir descriptores de frame, hoja neutral, vidrio y sill flush. | Aceptación visual humana registrada; geometría congelada. |
| `[x]` | T7.03 — Definir cuatro materiales visuales sintéticos y sus assignments. | Implementado y aprobado visualmente por una persona. |
| `[x]` | T7.04 — Integrar en una nueva derivada y realizar review visual. | HUMAN VISUAL ACCEPTANCE — APPROVED. |
| `[x]` | T7.05 — Auditar reproducibilidad, mutación, privacidad y hygiene. | REPRODUCIBILITY / MUTATION / PRIVACY / VALIDATION — PASS. |
| `[x]` | T7.06 — Documentar evidencia y ejecutar auditoría final. | FINAL DOCUMENTATION & AUDIT — PASS. |

## T7.01 — Architectural visual contract

**Objetivo:** fijar un contrato puro que represente únicamente los seis
openings existentes y que rechace cualquier dato no autorizado.

**Entradas:**

- `measurements/rooms/living-room-main.json`;
- `blender/scripts/measurements/generate_room.py`;
- room signature `182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a`;
- source/derived bindings de la especificación.

**Outputs:**

- contrato JSON-compatible con IDs, tipos, wall IDs, offsets, dimensiones,
  depths, sills, vectores derivados, estados, source IDs y nombres deterministas;
- `FixedElementVisual` vacío para el target;
- fallo explícito para `fixed_elements` no vacío o tipos no soportados.

**Invariantes:**

- exactamente `door-main`, `door-terrace`, `window-v1`, `window-v2`,
  `window-v3`, `window-v4`;
- `opening_direction=unknown` en todos;
- no se copian valores físicos a provenance sin su estado;
- `units=m`, `coordinate_system=canonical_room`;
- input no mutado.

**Tests/gates:**

- PASS de `validate_room` y `build_generation_plan`;
- test de counts 2/4, IDs, statuses y source IDs;
- test de input malformed y fixed elements no vacío;
- test de serialización repetida idéntica;
- Python syntax y `git diff --check`.

**Aceptación humana:** no aplica todavía; requiere revisión del contrato antes
de abrir Blender. La validación T7.01 es puramente contractual; no constituye
aceptación visual.

**Evidencia T7.01:** `test_architectural_visual_contract.py` pasa 20/20; el
validador del room pasa; `build_generation_plan` y `room_to_plan` pasan; y los
hashes/signatures de la fuente arquitectónica, Slice 006 y los contratos
históricos permanecen sin cambios. No se importó Blender, no se generaron
meshes y no se modificaron escenas.

## T7.02 — Opening visual geometry v1

**Objetivo:** crear una descripción procedural mínima que haga reconocibles
puertas y ventanas sin afirmarlas como construcción real.

**Entradas:** contrato T7.01.

**Outputs:**

- `FRAME` para cada opening;
- `DOOR_INFILL` para cada door, con nombre de objeto estable `LEAF` y pose `closed_neutral`;
- `GLASS` y `SILL` para cada window;
- ningún objeto fijo.

**Invariantes:**

- geometría alineada con el envelope efectivo del plan;
- `frame_profile_width_m=0.05` y `panel_recess_m=0.01` son constantes
  sintéticas de presentación, separadas de las medidas contractuales;
- en ventanas, el frame usa `depth/2 + frame_projection_m` como frente visual
  y el glass queda retranqueado `panel_recess_m` detrás de su reverso; el sill
  sigue el centro Y del frame;
- en puertas, el frame usa la misma proyección sintética y el único infill
  queda `panel_recess_m` detrás de su reverso, acotando su profundidad al
  opening cuando sea necesario; se preservan sus anchos y alturas;
- no booleanos, no cortes, no swings, no handles, no animation;
- nombres sin `.001/.002` y ownership `ArchitecturalVisual`;
- parámetros visuales sintéticos no modifican measurements ni plan.

**Tests/gates:**

- component counts 6 frames, 2 leaves, 4 glass y 4 sills;
- dimensions/positions comparadas con los seis envelopes;
- repeated contract output idéntico;
- no collection/object duplicates ni residual components.

**Aceptación humana:** STOP VISUAL completado en T7.02; el criterio fue
reconocimiento visual sin clipping funcional.

**Estado:** `HUMAN VISUAL ACCEPTANCE — APPROVED`.

**Evidencia:** `architectural_visual_geometry.py` produce el plan lógico y
`materialize_architectural_visual.py` lo materializa en la nueva derivada
`blender/scenes/review/2026-09-10-living-room-main-slice-007-architectural-visual-v1.blend`.
La revisión visual encontró un frame de 0.04 m, centros coplanares y solo
0.005 m de separación frontal; la RED de la última iteración falló la aserción
del plano frontal de ventana antes de GREEN; la RED de puertas falló después
la proyección del frame y el recess del infill. GREEN pasa 34/34 con perfil
visual 0.05 m, proyección sintética 0.02 m, retranqueo explícito 0.01 m y
frame/sill alineados. El inventario observado
debe conservar 6 roots, 6 frames, 2 neutral door infills, 4 glass panels, 4
sill bands, 16 meshes y 22 objetos visuales, con `FixedElementVisual` vacío.
La materialización GUI/MCP se ejecutó dos veces sobre la derivada existente y
conservó 22 nombres, 78 objetos totales y 12 collections de escena, sin
`.001/.002` ni cambios fuera de `HSARCH_VISUAL_*`. No se crean materiales en
esta tarea. La escena guardada tiene 178386 bytes y SHA puntual
`9CE444108950CBF715BF295EDC0256C79C7B10AA7AFD8BDB31F72A3F3CB39CE4`; no es un
golden binario. La aceptación humana fue completada y aprobada tras la
refinación final de puertas; en ese momento T7.03 aún quedaba pendiente de
aceptación visual humana.

## T7.03 — Architectural materials v1

**Objetivo:** diferenciar visualmente marco, hoja, vidrio y sill con materiales
procedurales mínimos.

**Entradas:** componentes T7.02.

**Outputs:** cuatro materiales exactos:

- `hs3d_visual_mat_arch_opening_frame_v1`;
- `hs3d_visual_mat_arch_door_leaf_v1`;
- `hs3d_visual_mat_arch_window_glass_v1`;
- `hs3d_visual_mat_arch_sill_v1`.

Tambien produce una politica de visibilidad de presentacion para los seis
proxies tecnicos representados, sin eliminarlos ni convertir la capa visual en
autoridad.

**Invariantes:**

- `material_id`, `semantic_role`, RGBA, roughness, metallic y
  `provenance=procedural_synthetic` estables;
- sin `TEX_IMAGE`, imágenes, rutas, texturas externas o datablocks duplicados;
- assignments determinados por role, nunca por orden incidental de datablocks.
- los proxies tecnicos siguen en `Openings`, pero se excluyen de viewport/render
  solo en la presentacion derivada mediante `hide_viewport` y `hide_render`;
  `hide_set`, geometria, transforms, materiales y metadata no forman parte de
  la mutacion.
- la politica es reversible, determinista y solo selecciona los seis proxies
  con representacion `HSARCH_VISUAL_*`; las colecciones y objetos no relacionados
  permanecen intactos.

**Tests/gates:**

- exact material name/count test;
- stable parameter and assignment test;
- glass policy test: low-saturation tint, low roughness, transparent alpha and
  materially stronger transmission;
- malformed material and privacy text scan;
- Python/JSON syntax.
- exact six-proxy visibility policy, preserved proxy fingerprint and no unrelated
  scene mutation;
- repeated policy application with identical normalized state.

**Aceptación humana:** T7.03 fue revisada visualmente y aprobada por una
persona junto con la política de presentación; la legibilidad no se aceptó por
inferencia automática únicamente.

**Evidencia de implementación:** `architectural_visual_materials.py` produce
un plan puro determinista con 4 materiales y 16 assignments; el adaptador
Blender actualiza exactamente los cuatro datablocks owned y asigna un slot por
mesh, sin borrar materiales ajenos. Las dos pasadas GUI/MCP conservaron la
huella geométrica `11632:642518`, los 22 objetos visuales, las 12 collections
de escena y `FixedElementVisual` vacío. Blender 5.2.1 LTS confirmó GUI visible,
`bpy.app.background=false` y engine `BLENDER_EEVEE`. Las vistas
`WINDOW_MATERIAL_CLOSEUP_T7_03` y `DOOR_MATERIAL_CLOSEUP_T7_03` están preparadas
para el STOP VISUAL; en ese punto T7.03 seguía `[ ] IMPLEMENTED — AWAITING
HUMAN VISUAL ACCEPTANCE`, estado que posteriormente fue cerrado mediante
aceptación humana.

La politica adicional esta implementada en
`architectural_visual_visibility.py` y
`materialize_architectural_visual_visibility.py`, con cobertura en
`test_architectural_visual_visibility.py` (18/18). La aplicacion GUI/MCP se
ejecuto dos veces sobre la derivada existente: los seis proxies contractuales
siguen presentes en `Openings`, con geometria, transforms, materiales y
metadata iguales; solo `hide_viewport=True` y `hide_render=True` cambiaron en
la derivada. Los 22 objetos HSARCH, 16 meshes y `FixedElementVisual` vacio se
conservaron, y no hubo cambios de visibilidad fuera de los seis proxies. La
politica quedó posteriormente aprobada junto con la aceptación visual humana de
T7.03.

## T7.04 — Scene integration & visual review

**Objetivo:** materializar el contrato en una nueva derivada y comprobar su
lectura visual mediante Blender GUI/MCP.

**Entradas:** contrato y componentes T7.01–T7.03; Slice 006 derived read-only.

**Outputs:**

- `blender/scenes/review/2026-09-10-living-room-main-slice-007-architectural-visual-v1.blend`;
- root `HSARCH_VISUAL_living-room-main_slice-007_v1`;
- collections `ArchitecturalVisual`, `OpeningVisual` y `FixedElementVisual`;
- captura viewport y, si procede, un único review PNG de 960×720.

**Invariantes:**

- source SHA y Slice 006 derived SHA sin cambios;
- `HS3D_ROOM_*`, proxies técnicos, Furniture, FurnitureVisual y
  ReviewPresentation sin cambios;
- no cámara o luz nueva; se reutiliza ReviewPresentation existente;
- no objects fuera de la capa nueva.

**Tests/gates:**

- Blender GUI `5.2.1 LTS`, `bpy.app.background=false`, `VIEW_3D`, MCP localhost;
- numeric envelope comparison for six openings;
- scene inventory and ownership validation;
- visual review of frame/leaf/glass/sill and no functional clipping.

**Aceptación humana:** STOP VISUAL explícito: una persona debe aprobar que
las puertas/ventanas sean reconocibles, que la arquitectura siga legible y que
no haya clipping funcional invalidante.

**Estado:** `HUMAN VISUAL ACCEPTANCE — APPROVED`.

**Evidencia:** se inspeccionó la derivada existente en Blender GUI/MCP con
`bpy.app.background=false`, `VIEW_3D` y `BLENDER_EEVEE`. El inventario conserva
6 roots, 16 meshes, 22 objetos visuales, 0 fixed objects y los seis proxies
técnicos intactos en `Openings` con la política de presentación aplicada.
ReviewPresentation mantiene una cámara y dos luces existentes. Se obtuvieron
capturas de viewport para el contexto de habitación, ventanas y puertas; no se
generó un render nuevo porque no era necesario para este checkpoint. La
aceptación humana explícita confirmó reconocimiento conjunto, legibilidad de
arquitectura, integración con FurnitureVisual y ausencia de clipping funcional
evidente. T7.04 queda congelado; no se requieren cambios adicionales de
geometría, materiales, visibilidad de proxies ni integración visual. No se
modificaron contratos arquitectónicos, FurniturePlan, FurnitureVisual ni
ReviewPresentation.

## T7.05 — Reproducibility / mutation / privacy validation

**Objetivo:** demostrar que la capa se puede reconstruir lógicamente sin
duplicados, mutación arquitectónica ni metadata privada.

**Entradas:** derivada aprobada, contrato, hashes y preview si existe.

**Outputs:** inventario lógico normalizado, comparación de dos lecturas,
reporte de mutación/privacy/hygiene y decisión de evidencia.

**Invariantes:**

- inventories idénticos en dos lecturas;
- fixed channel vacío;
- source y Slice 006 derived unchanged;
- no `.001/.002`, collections/materials/objects/lights/cameras residuales;
- PNG sin `eXIf`, `tEXt`, `iTXt`, `zTXt` ni rutas locales;
- no golden binary `.blend`/PNG.

**Tests/gates:**

- pure contract and idempotence tests;
- room, room-to-plan, furniture and historical validators aplicables;
- Python/JSON syntax;
- privacy text/binary and hygiene/temp audit;
- `git diff --check`.

**Aceptación humana:** T7.05 no sustituye la aprobación visual de T7.04; solo
valida la reproducibilidad y seguridad de lo ya observado.

**Estado:** `REPRODUCIBILITY / MUTATION / PRIVACY / VALIDATION — PASS`.

**Evidencia:** las suites relevantes invocadas explícitamente sumaron
`555/555 PASS`: arquitectura `92/92`, measurements `230/230`, furniture
`233/233`, validators/generation plan/`room_to_plan`/spatial/golden, Python AST
`42/42`, JSON `11/11`, privacy/hygiene y whitespace. La discovery genérica del
repositorio devolvió `0 tests`; no se considera PASS y permanece como deuda
conocida. Los runners Blender históricos que regeneran o mutan escenas se
omitieron deliberadamente. El inventario normalizado se leyó dos veces con
igual resultado y el contrato puro se ejecutó dos veces con salida lógica
idéntica. Blender GUI/MCP live funcionó con Blender 5.2.1 LTS,
`bpy.app.background=False`, `VIEW_3D` y `bpy.data.is_dirty=False`; el error
histórico de `get_addon_status` (`No module named 'blender_mcp.config'`) queda
como deuda no bloqueante. No se cambió producción para resolverlo. No se
generó PNG Slice 007: no existe artefacto contractual nuevo que auditar.

**Aceptación visual:** no requerida adicionalmente; T7.04 ya estaba aprobado y
congelado.

## T7.06 — Documentation & final audit

**Objetivo:** registrar únicamente evidencia real y dejar la rama lista para
revisión, sin integrar ni publicar.

**Entradas:** resultados T7.01–T7.05 y feedback humano.

**Outputs:** spec/plan/tasks coherentes y auditoría final de alcance.

**Invariantes:**

- solo se marcan `[x]` tareas con evidencia;
- las limitaciones aceptadas no se convierten en bugs;
- no se introducen README/PROJECT_CONTEXT cambios amplios ni Slice 008;
- no se documentan rutas privadas ni hashes como goldens no aprobados.

**Tests/gates:**

- revisión de diff completo, incluyendo binarios;
- coherencia spec/plan/tasks;
- privacidad, provenance y hygiene;
- `git diff --check`.

**Aceptación humana:** revisión del cierre documental antes de cualquier
commit/PR posterior.

**Estado:** `FINAL DOCUMENTATION & AUDIT — PASS`.

**Evidencia:** spec, plan y tasks cuentan la misma historia que la
implementación real y los contratos heredados. El alcance queda limitado a la
capa `HSARCH_VISUAL_*`: 6 roots, 16 meshes, 6 frames, 4 glass, 2 neutral door
infills, 4 sill bands, 0 fixed visual objects y 22 objetos gestionados. Los
cuatro materiales son `procedural_synthetic` y conservan la calibración de
glass aprobada: Base Color `(0.88, 0.90, 0.92, 1.0)`, Roughness `0.06`,
Metallic `0.0`, Alpha `0.16`, Transmission Weight `0.88`, IOR `1.5`,
`surface_render_method=DITHERED` y `blend_method=HASHED` según la API observada
de Blender 5.2.1. `Openings` sigue siendo la autoridad técnica: los seis proxies
permanecen intactos y la derivada aplica únicamente `hide_viewport=True` y
`hide_render=True`; `hide_set/hide_get` no sustituye esa política. Architecture,
FurniturePlan, FurnitureVisual, ReviewPresentation, cámara, luces, source y
Slice 006 derived permanecen intactos. No se detectaron rutas privadas, nuevos
backups `.blend1` generados por Slice 007, temporales, capturas accidentales,
Slice 008 ni scope creep. El único `.blend1` observado es el fixture
histórico/preexistente `blender/scenes/tests/001-foundation-room.blend1`,
ignorado y fuera del scope de Slice 007.
La aceptación humana se registra explícitamente para T7.02, T7.03 y T7.04;
no se inventa una aceptación visual nueva para T7.05 o T7.06.

## Estado actual

T7.01 está `[x]`; T7.02 está `[x] HUMAN VISUAL ACCEPTANCE — APPROVED`; T7.03
está `[x] HUMAN VISUAL ACCEPTANCE — APPROVED`; T7.04 está `[x] HUMAN VISUAL
ACCEPTANCE — APPROVED`; T7.05 está `[x] REPRODUCIBILITY / MUTATION / PRIVACY /
VALIDATION — PASS`; T7.06 está `[x] FINAL DOCUMENTATION & AUDIT — PASS`. Slice
007 queda en `SLICE 007 FINAL AUDIT PASSED — READY FOR PRECOMMIT REVIEW`.
No se realizó commit, staging, push, PR, merge, rebase, squash ni force push.
