# Tareas: Real-room Scene Comparison and Validation v1

> Clasificación: T2
> Estado: T3.01, T3.02, T3.03 y T3.04 implementadas y validadas; el adapter
> Blender y las fases posteriores siguen pendientes.
> El slice 002 permanece cerrado e integrado en `main`; las tareas completadas
> aquí se limitan al contrato, la política matemática y la comparación pura de
> T3.01–T3.04.

Estados: `[ ]` pendiente · `[~]` en curso · `[x]` validada · `[!]` bloqueada.

La ejecución futura debe mantener `measurements/` como autoridad, separar el
core puro del adapter Blender y detenerse ante cualquier discrepancia no
explicada. No se deben convertir estas tareas en cambios de schemas, nuevas
capturas reales o geometría constructiva sin una autorización independiente.

## T3.01 — Aprobar contrato y modelo de autoridad

- **Estado:** `[x]`
- **Objetivo:** aprobar la jerarquía room → generation plan → scene y el
  contrato de la representación normalizada.
- **Archivos previstos:** `spec.md`, `plan.md`, pruebas de contrato futuras.
- **Evidencia:** `compare_room_scene.py` fija la autoridad
  `measurements/` → generation plan → scene mediante `SourceContext` y
  `Provenance`, sin importar `bpy`, leer `.blend` ni promover scene a
  measurement. Los tests de contrato cubren estados, fallback,
  reconciliación representable y separación de contextos.
- **Validación:** revisión humana de authority model, estados, provenance,
  fallback, reconciliación y límites scene → measurement.
- **Rollback:** retirar solo la documentación del slice 003.
- **Fuera:** cambios en JSON, schema o escena.

## T3.02 — Definir `ComparisonReport` y findings

- **Estado:** `[x]`
- **Objetivo:** fijar `report_version`, `valid`, room/schema/generator
  versions, `scene_adapter_version`, `comparison_stage`,
  `source_context`, discrepancies, warnings, info y summary.
- **Archivos previstos:** `blender/scripts/measurements/compare_room_scene.py`,
  `tests/measurements/test_room_scene_comparison.py`.
- **Evidencia:** el módulo y `test_room_scene_comparison.py` fijan el
  contrato serializable de reportes, findings, severidades, stages,
  versiones independientes, tolerancias lineales/areales/exactas y orden
  determinista; 13 tests puros pasan sin Blender.
- **Validación:** serialización estable, sin timestamps variables, contexto
  observed/effective_geometry/scene, listas ordenadas y códigos documentados.
- **Rollback:** eliminar el módulo y sus pruebas sin tocar el generator.
- **Fuera:** UI o formato de reporte externo.

## T3.03 — Fijar tolerancias y reglas de estados

- **Estado:** `[x]`
- **Objetivo:** aplicar `1e-6 m` como tolerancia computacional inicial y
  separar incertidumbre física de representación plan → escena; definir la
  tolerancia de áreas en `m²` mediante propagación desde coordenadas.
- **Archivos previstos:** core de comparación y tests de tolerancia.
- **Validación:** casos dentro/fuera de tolerancia; magnitudes lineales,
  vectores y áreas dimensionalmente correctas; estados exactos; `unknown` no
  se convierte en valor; fallback y derived conservan contexto.
- **Evidencia:** `compare_room_scene.py` centraliza `MATH_TOLERANCE_M = 1e-6`
  para magnitudes lineales y expone comparadores puros para valores lineales,
  áreas y estados exactos. `area_tolerance_from_polygon` aplica el bound
  determinista de Shoelace en `m²`, recentrado en el bounding box expected para
  invariancia ante traslación; la incertidumbre observacional no relaja la
  tolerancia computacional. Hay 21 tests puros específicos para esta tarea.
- **Rollback:** revertir solo las reglas del comparador.
- **Fuera:** cambiar `MATH_TOLERANCE_M` global del validator existente.

## T3.04 — Implementar comparación room ↔ plan

- **Estado:** `[x]`
- **Objetivo:** comprobar que el plan refleja valores observados, geometría
  efectiva, reconciliaciones, fallbacks, estados y provenance del room.
- **Archivos previstos:** `compare_room_scene.py`, tests puros.
- **Validación:** wall-05, wall-16, V2, espesores medidos/unknown y altura real.
- **Evidencia:** `compare_room_to_plan(room, plan)` implementa la transición
  pura sin `bpy`, archivos ni mutación de entradas. Compara por IDs la
  identidad, unidades, coordenadas, suelo, altura, paredes, openings y
  elementos fijos; conserva `observed`/`effective_geometry`/`scene=null` en los
  findings; distingue reconciliaciones, estados y fallbacks; y usa la
  tolerancia lineal y de área versionadas. Las constantes de fallback y el
  cálculo Shoelace proceden de `generation_policy.py`, sin duplicar la política
  del generator. Hay tests específicos, incluido el acceptance case
  `living-room-main`.
- **Compatibilidad:** room-v1 no exige campos v1.1. El `height_status` superior
  del plan v1 histórico no se usa como autoridad porque puede quedar
  sobrescrito por metadata de elementos fijos; se verifican `height_m` y los
  estados de altura de las paredes. La provenance no expuesta por el plan queda
  marcada como `not verifiable at room_to_plan with generation-plan contract
  current version`; no se reconstruye ni se simula. No se modifica la forma del
  plan, room-v1 ni la golden.
- **Rollback:** eliminar la comparación room/plan; conservar `build_generation_plan`.
- **Fuera:** inferencia o corrección automática del room.

## T3.05-P — Ampliar provenance del generation plan antes de cerrar plan→scene

- **Estado:** `[ ]`
- **Objetivo:** transportar explícitamente provenance por campo cuando el
  contrato final requiera validar su conservación hasta la escena.
- **Alcance futuro:** method, uncertainty, formula, depends_on, reason,
  reconciliation_id y source IDs individuales; sin reconstruirlos desde
  agregados.
- **Dependencia:** debe resolverse y validarse antes de afirmar provenance
  completa en `plan_to_scene`. No forma parte de T3.04 ni inicia T3.05.
- **Fuera:** cambios en esta corrección, schemas, datos reales, Blender y
  adapter.

## T3.05 — Definir representación normalizada y adapter Blender

- **Estado:** `[ ]`
- **Objetivo:** extraer en modo solo lectura unidades, colecciones, IDs,
  geometría y custom properties sin depender del orden de objetos, usando el
  dominio gestionado existente de `HS3D_ROOM_<room_id>`.
- **Archivos previstos:** adapter Blender junto a los scripts de medición,
  `validate_generated_room.py` y tests de contrato.
- **Validación:** objetos ausentes/inesperados, unidades incorrectas,
  metadata crítica ausente, duplicate managed entity ID, entidades
  normalizadas malformadas, versiones incompatibles, auxiliares no gestionados
  permitidos y orden alternativo producen resultados definidos.
- **Rollback:** retirar el adapter sin alterar escenas.
- **Fuera:** guardar, regenerar, reparar o modificar `.blend`.

## T3.06 — Implementar comparación plan ↔ escena

- **Estado:** `[ ]`
- **Objetivo:** verificar geometría, dimensiones, posiciones, metadata,
  signatures, statuses y flags contra el generation plan.
- **Archivos previstos:** core, adapter y `validate_generated_room.py`.
- **Validación:** tolerancia computacional, IDs canónicos, expected/actual y
  severity correctos para walls, openings, floor y fixed elements.
- **Rollback:** conservar la validación de escena histórica si la integración
  nueva debe retirarse.
- **Fuera:** booleanos, openings constructivos y nuevas reglas artísticas.

## T3.07 — Añadir mutaciones y regresiones

- **Estado:** `[ ]`
- **Objetivo:** cubrir todos los fallos contractuales definidos en la spec.
- **Archivos previstos:** `tests/measurements/test_room_scene_comparison.py`,
  fixtures normalizados si son necesarios.
- **Validación:** wall/opening missing, unexpected object, longitudes,
  altura, espesor, width, height, sill, depth, offset, measured→derived,
  unknown→measured, fallback, fallback provenance, reconciliación y metadata
  ausente, flags y provenance; duplicate managed ID, normalized entity
  malformed, wrong units, wrong report/adapter/plan version, auxiliares no
  gestionados permitidos y ordering diferente semánticamente equivalente.
- **Rollback:** retirar únicamente las pruebas y fixtures nuevos.
- **Fuera:** modificar tests históricos para relajar expectativas.

## T3.08 — Validar `living-room-main`

- **Estado:** `[ ]`
- **Objetivo:** ejecutar el comparador contra el JSON real y el artefacto
  `.blend` ya versionado, sin regenerarlo.
- **Archivos previstos:** `docs/setup/003-room-scene-comparison-validation.md`
  y evidencia de ejecución fuera del JSON canónico.
- **Validación:** 22 segmentos, 6 openings, reconciliaciones, V2 derived,
  seis espesores measured, dieciséis fallbacks, cero proxies verticales,
  `proxy_only=true` y `constructive_geometry=false`.
- **Rollback:** retirar evidencia documental, no el artefacto canónico.
- **Autorización:** requiere autorización explícita para abrir Blender si la
  integración no puede ejecutarse fuera de Blender.

## T3.09 — Documentar gates, privacidad y reproducibilidad

- **Estado:** `[ ]`
- **Objetivo:** registrar comandos, resultados, límites de infraestructura,
  provenance, hashes y ausencia de datos personales.
- **Archivos previstos:** `docs/setup/003-room-scene-comparison-validation.md`,
  `spec.md`, `plan.md` si se descubre una decisión contractual nueva.
- **Validación:** revisión contra `.quality/QUALITY.md`, `CONTRIBUTING.md` y
  `AGENTS.md`; no afirmar PASS sin evidencia.
- **Rollback:** revertir documentación del slice 003.
- **Fuera:** limpieza amplia de snapshots históricos de slices anteriores.

## T3.10 — Auditoría final del slice 003

- **Estado:** `[ ]`
- **Objetivo:** verificar scope, compatibilidad v1, privacidad, determinismo,
  binarios, tests y preparación de PR.
- **Archivos previstos:** diff completo del slice y sus gates.
- **Validación:** validators, suite `tests/measurements`, golden
  `1105946a0dfe0088f5ad59da4178939644305b0d09b94022bfe5c87d9dde36f0`,
  syntax y `git diff --check`.
- **Rollback:** no cerrar ni publicar el slice si existe una discrepancia.
- **Fuera:** merge, PR, nuevo slice o geometría constructiva.

## Deudas explícitamente fuera del slice 003

- 16 espesores no medidos.
- `opening_direction` desconocido.
- Booleanos y geometría constructiva.
- Nuevas habitaciones o sesiones de captura.
- Mobiliario, decoración, materiales e iluminación artística.
- Fotografías, EXIF, LiDAR y fotogrametría.
- Cambios en MCP o `get_addon_status`.

T3.05 y posteriores permanecen `[ ]` hasta que una implementación posterior
sea autorizada y validada. T3.01–T3.04 cubren únicamente el contrato, la
política matemática y la comparación pura room → plan; esta fase no inicia el
adapter ni la integración Blender.
