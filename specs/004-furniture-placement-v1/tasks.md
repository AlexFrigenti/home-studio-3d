# Tareas: Furniture Placement v1

> Clasificación: T2
> Estado del checkpoint actual: T4.01, T4.02 y T4.03 implementadas y
> validadas; T4.04–T4.06 no iniciadas.
> Rama: `spec/004-furniture-placement-v1`

Estados: `[ ]` pendiente · `[~]` en curso · `[x]` validada · `[!]` bloqueada.

Furniture Placement v1 debe conservar `measurements/` como autoridad
arquitectónica y separar el dominio de layouts, planes y overlays. Estas tareas
son la descomposición aprobada; T4.01–T4.03 están cerradas en este checkpoint
y T4.04–T4.06 siguen pendientes.

## T4.01 — Fijar autoridad y contrato `furniture-layout-1`

- **Estado:** `[x]`
- **Objetivo:** materializar el contrato de entrada fuera de `measurements/`
  y fijar la política de campos, IDs, unidades, estados y provenance mínima.
- **Archivos previstos:**
  `layouts/schema/furniture-layout-v1.schema.json`,
  `blender/scripts/furniture/validate_furniture_layout.py`,
  `tests/furniture/test_furniture_layout.py`.
- **Invariantes:** `room_id` referencia el room sin copiar su geometría;
  `units=m`; `coordinate_system=canonical_room`;
  `placement_method=manual`; `anchor=bottom_center`; dimensions ordenadas
  `[width, depth, height]`, positivas y finitas; IDs únicos con sintaxis slug;
  unknown fields rechazados; `dimensions_status` explícito; `unknown` no
  aceptado para generar proxies; cualquier yaw finito en grados es válido y
  T4.02 se encargará de normalizarlo.
- **Tests:** documento válido mínimo; tipos admitidos; campos ausentes;
  campos desconocidos; IDs inválidos/duplicados; unidades y coordenadas
  incorrectas; placement method incorrecto; dimensiones inválidas o no
  finitas; statuses válidos e `unknown` rechazado; yaw no finito y posición
  inválida; determinismo y no mutación.
- **Gates:** tests de `tests/furniture/`, JSON syntax, `git diff --check` y
  suite existente de measurements.
- **Blender:** No.
- **Cierre:** schema y validador emiten el mismo contrato versionado, sin tocar
  room schemas, measurements ni un layout de acceptance.
- **Evidencia:** schema, validator puro, fixture sintético y `26/26 PASS` en
  `tests/furniture/test_furniture_layout.py`; no se usó Blender.

## T4.02 — Construir el furniture plan puro

- **Estado:** `[x]`
- **Objetivo:** producir un plan Blender-independent ligado a un room plan
  concreto.
- **Archivos implementados:**
  `blender/scripts/furniture/build_furniture_plan.py`,
  `tests/furniture/test_furniture_plan.py`.
- **Interfaces:**
  `canonicalize_layout(layout) -> canonical_layout` y
  `build_furniture_plan(layout, room_plan) -> furniture_plan`.
- **Invariantes:** versión `furniture-placement-generator-1`; identidad,
  versión y firma del room plan transportadas; items ordenados por ID; yaw
  normalizado a `[0,360)`; geometry efectiva de proxy derivada con
  `bottom_center`; provenance limitada a datos del layout; inputs intactos;
  spatial validation reservada para T4.03; solo se soporta
  `room-v1.1-generator-2`.
- **Tests:** mismatch de room, units, coordinate system, version y firma;
  input en orden alternativo; yaw equivalente; footprint con rotación;
  firma distinta al alterar cada campo contractual; serialización repetida
  idéntica; provenance, no mutación de layout y room plan; `30/30 PASS`.
- **Gates:** tests puros de furniture, Python/JSON syntax y diff check.
- **Blender:** No.
- **Cierre:** `[x]` La misma serialización canónica del layout y el mismo room
  plan producen el mismo plan y `logical_signature` sin importar `bpy`.
- **Evidencia:** yaw canónico, ordering por ID, footprint/OBB 2D, provenance,
  firma SHA-256 y defensas de identidad/versiones; no spatial validation ni
  Blender.

## T4.03 — Validar spatial validity

- **Estado:** `[x]`
- **Objetivo:** separar los errores espaciales demostrables de las reglas de
  diseño que solo pueden ser warnings.
- **Archivos previstos:**
  `blender/scripts/furniture/validate_furniture_spatial.py`,
  `tests/furniture/test_furniture_spatial.py`.
- **Invariantes:** se usan floor polygon, wall proxies, opening proxies y
  footprints/OBB efectivos del room plan; thickness unknown/fallback,
  `opening_direction=unknown`, `proxy_only=true` y
  `constructive_geometry=false` se conservan como límites explícitos. El
  binding de room/version/firma/units/coordinate system bloquea la geometría;
  openings usan XY+Z cuando los rangos están disponibles y `fixed_elements=[]`
  no infiere obstáculos.
- **Errores contractuales:** dimensiones inválidas; duplicate ID; proxy fuera
  de floor; wall proxy intersection; opening proxy intersection; overlap de
  proxies de suelo no apilables; plan malformado.
- **Warnings:** clearance humano, paso, swing de puerta, ergonomía, reglas de
  uso frente a muebles o ventanas y cualquier claim constructivo no demostrable.
- **Tests:** `54/54 PASS`; posiciones dentro/fuera del floor; contacto límite bajo la
  tolerancia; footprint rotado; wall/opening intersection; overlap;
  no-overlap; fixed element con geometría efectiva cuando exista;
  fixed element sin geometría no inferido; consistency OBB↔footprint;
  footprints/OBBs degenerados; room entities malformadas; orientación
  collinear a distintas escalas; ordering estable; warnings no convertidos en
  errores; límites de fallback presentes en la salida.
- **Gates:** tests puros, suite measurements y diff check.
- **Blender:** No.
- **Cierre:** `[x]` El resultado `furniture-spatial-validation-1` identifica
  entidades implicadas, es determinista, no muta inputs y no presenta una
  heurística como medición física. Las limitations se agregan sin ruido.

## T4.04 — Generar overlay Blender reversible

- **Estado:** `[ ]`
- **Objetivo:** añadir proxies furniture a una copia derivada de la escena
  arquitectónica sin modificar su ownership.
- **Archivos previstos:**
  `blender/scripts/furniture/generate_furniture.py`,
  `tests/furniture/test_furniture_generation_contract.py`.
- **Invariantes:** root `HSLAYOUT_<room_id>_<layout_id>`; collection `Furniture`;
  objetos `HSLAYOUT_FURNITURE_<item_id>`; metadata `hs3d_layout_*`; no
  `read_factory_settings`; no delete de `HS3D_ROOM_*`; source `.blend` nunca
  sobrescrito; output existente rechazado por defecto; externos fuera de
  ownership; regenerar un layout no elimina otro.
- **Tests:** path protection; namespace; metadata; dimensions y transforms;
  same plan twice; dos layouts aislados; snapshot architecture before/after;
  source SHA estable; collections y entidades room intactas; parent policy.
- **Gates:** tests de contrato y una ejecución Blender CLI read/write
  autorizada únicamente sobre una copia derivada y una ruta nueva.
- **Blender:** Sí para la integración real; no para la mayor parte de los
  tests de ownership.
- **Cierre:** existe un `.blend` derivado reproducible, la arquitectura antes
  y después es equivalente y el `.blend` fuente no cambia.

## T4.05 — Normalizar y comparar furniture scene

- **Estado:** `[ ]`
- **Objetivo:** crear un adapter y un ComparisonReport de furniture
  independientes de los contratos room.
- **Archivos previstos:**
  `blender/scripts/furniture/normalize_furniture_scene.py`,
  `blender/scripts/furniture/compare_furniture_scene.py`,
  `tests/furniture/test_normalize_furniture_scene.py`,
  `tests/furniture/test_furniture_scene_comparison.py`.
- **Invariantes:** solo se gestiona el root HSLAYOUT solicitado; entities
  ordenadas por `(entity_type, entity_id)`; unidades métricas; parent transforms
  no soportados; paths excluidos; provenance solo materializada; arquitectura
  no entra en el normalized furniture scene.
- **Tests:** root/collection ausente o duplicado; duplicate ID; entity
  malformed; units/roles/versiones incorrectas; missing/unexpected; type,
  dimensions, position, yaw, anchor, geometry, metadata, provenance,
  ownership y signature mutations; ordering equivalente; serialización estable;
  geometry-vs-metadata anti-false-pass; entidades `HS3D_ROOM_*` rechazadas como
  furniture.
- **Gates:** tests furniture y room gates sin modificar sus resultados.
- **Blender:** No para el core sintético; read-only/integración sobre el
  derivado se ejecuta en T4.06.
- **Cierre:** `furniture-scene-adapter-1` y
  `furniture-scene-comparison-1` producen findings estables y no extienden
  `room-scene-adapter-1` ni `room-scene-comparison-1`.

## T4.06 — Acceptance real, artefactos y documentación

- **Estado:** `[ ]`
- **Objetivo:** cerrar la primera acceptance de Furniture Placement v1 sobre
  `living-room-main` con evidencia reproducible.
- **Archivos previstos:** un layout bajo
  `layouts/living-room-main/<layout-id>.json`, un `.blend` derivado, un
  preview técnico, `docs/setup/004-furniture-placement-validation.md` y el
  runner de acceptance estrictamente necesario.
- **Datos de acceptance:** dos o tres proxies, preferentemente `sofa`,
  `coffee_table` y `armchair`; todos `dimensions_status=synthetic` y
  `source_id` con prefijo `slice-004-acceptance-`.
- **Invariantes:** room plan `room-v1.1-generator-2`; firma room
  `182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a`;
  fuente generator-2 preservada; architecture before == after; fuente SHA
  inmutable; mismo plan produce mismo report; dimensiones no presentadas como
  reales; no assets externos.
- **Tests/gates:** todos los tests furniture; suite measurements 230/230 y
  historical 37/37; validators v1/v1.1/real; generation plan y room→plan;
  golden v1 exacta; Python/JSON syntax; diff check; privacy/provenance review;
  acceptance Blender CLI y preview técnico.
- **Blender:** Sí, CLI background preferido; MCP no necesario.
- **Cierre:** layout, plan, spatial validation, overlay, normalized scene,
  comparison, determinismo, anti-false-pass, arquitectura protegida,
  artefactos y documentación pasan con hashes registrados.

## Dependencias y checkpoints

| Tarea | Depende de | Checkpoint revisable |
| --- | --- | --- |
| T4.01 | diseño aprobado | contrato y validator puros |
| T4.02 | T4.01 | plan y firma puros |
| T4.03 | T4.02 | spatial findings y límites |
| T4.04 | T4.01, T4.02 | overlay derivado y arquitectura intacta |
| T4.05 | T4.01, T4.02, T4.04 | normalized furniture y report |
| T4.06 | T4.01–T4.05 | acceptance completa y setup doc |

T4.01–T4.03 deben formar un primer bloque puro y reversible. T4.04 debe
tener revisión independiente porque es el primer punto que escribe una escena.
T4.05 puede revisarse con escenas sintéticas antes de conectar el artefacto
real. T4.06 es el único bloque que versiona layout/`.blend`/preview de
acceptance y no debe mezclarse con tareas posteriores de assets o UI.

## Checklist de cierre futuro

- [ ] El contrato `furniture-layout-1` está validado y no contamina room data.
- [ ] El plan y su firma son deterministas y no mutan inputs.
- [x] La spatial validity distingue errores geométricos y warnings.
- [ ] El overlay HSLAYOUT es reversible, idempotente y ownership-safe.
- [ ] La arquitectura antes/después es equivalente por evidencia estructural.
- [ ] Normalizer y comparator furniture tienen contratos y findings estables.
- [ ] Anti-false-pass cubre geometry correcta/metadata corrupta y viceversa.
- [ ] Acceptance real de `living-room-main` pasa con dimensiones synthetic.
- [ ] Artefacto derivado y preview tienen hashes y no sobrescriben la fuente.
- [ ] Slices 001–003 siguen pasando sus gates.
- [ ] Privacidad, provenance parcial, rollback y límites están documentados.
- [ ] No se han añadido assets reales, UI, booleans, optimización ni multi-room.

## Estado del slice en este checkpoint

T4.01, T4.02 y T4.03 están `[x]`. T4.04–T4.06 permanecen `[ ]`. Este
checkpoint no crea overlay Blender, normalizer, comparator, escena, preview ni
artefacto Blender.
