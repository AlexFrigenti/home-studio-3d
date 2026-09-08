# Tareas: Real-room Scene Comparison and Validation v1

> Clasificación: T2
> Estado: T3.01, T3.02, T3.03, T3.04, T3.05-P, T3.05, T3.06 y T3.07
> implementadas y validadas; T3.08 y las fases posteriores siguen pendientes.
> El slice 002 permanece cerrado e integrado en `main`; las tareas completadas
> aquí se limitan al contrato, la política matemática, la comparación pura de
> T3.01–T3.04, la extensión de provenance T3.05-P y la normalización
> read-only de escena de T3.05.

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

- **Estado:** `[x]`
- **Objetivo:** transportar explícitamente provenance por campo en el plan
  v1.1 sin duplicar los valores físicos que ya contiene la geometría del plan.
- **Versión:** los planes schema `1.1` pasaron de
  `room-v1.1-generator-1` a `room-v1.1-generator-2`; el bump identifica el
  cambio aditivo de contrato. `room-v1-generator-1` y su golden permanecen
  intactos.
- **Evidencia:** `build_generation_plan` añade únicamente para v1.1 un bloque
  top-level `provenance` con metadata `observed` y `effective_geometry` para
  room height, floor area, longitudes y reconciliaciones de pared, thickness,
  campos individuales de opening y fixed elements soportados, ademas de
  `measurement_method` y `measured_at` bajo `provenance.room`. El bloque no
  contiene `value`, `value_m`, coordenadas ni duplicados geométricos.
- **Comparación:** `compare_room_to_plan` valida esa provenance solo para
  `room-v1.1-generator-2`, por IDs y por campo, con findings estructurados para
  metadata, source IDs, reconciliaciones y fallbacks. No reconstruye campos
  ausentes ni acepta silenciosamente `room-v1.1-generator-1`.
- **Validación:** tests RED→GREEN, provenance determinista, no mutación,
  geometry projection estable, validators, acceptance `living-room-main` y
  golden v1 exacta.
- **Dependencia:** esta tarea queda resuelta antes de cualquier afirmación de
  provenance completa en `plan_to_scene`; no inicia T3.05.
- **Fuera:** schemas, datos reales, Blender, adapter, `.blend`, previews y
  nuevas mediciones.

## T3.05 — Definir representación normalizada y adapter Blender

- **Estado:** `[x]`
- **Objetivo:** extraer en modo solo lectura unidades, colecciones, IDs,
  geometría y custom properties sin depender del orden de objetos, usando el
  dominio gestionado existente de `HS3D_ROOM_<room_id>`.
- **Archivos modificados:** `blender/scripts/measurements/normalize_room_scene.py`
  y `tests/measurements/test_normalize_room_scene.py`.
- **Validación:** objetos ausentes/inesperados, unidades incorrectas,
  metadata crítica ausente, duplicate managed entity ID, entidades
  normalizadas malformadas, auxiliares no gestionados permitidos y orden
  alternativo producen resultados definidos en el core puro/sintético. El
  contrato emite `scene_adapter_version` de forma estable; la compatibilidad
  entre versiones para comparar pertenece a la fase posterior. La verificación
  read-only contra el `.blend` versionado confirmó el contrato, las 31
  entidades esperadas, determinismo y ausencia de mutación.
- **Evidencia:** contrato `room-scene-adapter-1`, normalización por IDs,
  unidades métricas, orden estable, finite floats, exclusión de rutas locales,
  ownership managed/unmanaged y adapter duck-typed read-only cubiertos por
  tests puros y verificación Blender real. La normalización real produjo 1
  floor, 22 walls, 6 opening proxies, 1 preview camera y 1 preview light;
  dos serializaciones fueron idénticas, sin errores estructurales ni mutación.
  El SHA-256 del `.blend` permaneció
  `79D9ECCFE874A0DFA507638871462F260C6BD678C8A5E78860461B3A71911DC5`.
  La provenance de escena sigue siendo parcial y solo se extrae la metadata
  materializada; no se importa `bpy` al cargar el módulo, no se escribe una
  escena y no se ejecuta `plan_to_scene`.
- **Rollback:** retirar el adapter sin alterar escenas.
- **Fuera:** guardar, regenerar, reparar o modificar `.blend`.

## T3.06 — Implementar comparación plan ↔ escena

- **Estado:** `[x]`
- **Objetivo:** verificar geometría, dimensiones, posiciones, metadata,
  signatures, statuses y flags contra el generation plan.
- **Implementación actual:** `compare_plan_to_scene(plan, normalized_scene)` es
  un core puro y determinista que compara el plan recibido con evidencia de la
  escena normalizada; no lee el room, importa `bpy` ni regenera geometría.
- **Archivos modificados:** `compare_room_scene.py` y
  `test_room_scene_comparison.py`.
- **Validación:** tolerancia computacional, IDs canónicos, expected/actual y
  severity correctos para walls, openings, floor y fixed elements. La
  acceptance real se ejecutó contra una escena nueva generada por el pipeline
  actual, preservando sin cambios el artefacto histórico generator-1.
  `GENERATION_VALID`, `SCENE_VALID` y `compare_plan_to_scene` pasaron con
  `room-v1.1-generator-2`, `room-scene-adapter-1`, `errors=0`,
  `warnings=0`, `info=0` y `checked_entities=29`.
- **Evidencia real:** el nuevo artefacto es
  `blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend`,
  con SHA-256
  `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.
  Su preview técnico fue generado por el pipeline en
  `renders/previews/2026-09-08-living-room-main-v1.1-generator-2/`.
  La escena normalizada contiene 31 entidades gestionadas: 22 walls, 6
  opening proxies, 1 floor, 1 preview camera y 1 preview light.
- **Equivalencia:** la proyección geométrica semántica histórico generator-1
  frente a nuevo generator-2 pasó sin diferencias inesperadas; el hash común
  es `31c7a1698c0479a34bdd8e276b6e06fbd0c1dbf2ab90378dfcb3d2a2583cd82f`.
  Solo cambiaron metadata contractual de versión y firma lógica.
- **Robustez:** las mutaciones reales de traslación, mesh, thickness metadata,
  `proxy_only` y `source_id` produjeron findings bloqueantes estables; los
  casos independientes geometry-vs-metadata, determinismo y no mutación también
  pasaron. El histórico conserva el SHA-256
  `79D9ECCFE874A0DFA507638871462F260C6BD678C8A5E78860461B3A71911DC5`.
- **Rollback:** conservar la validación de escena histórica si la integración
  nueva debe retirarse.
- **Fuera:** booleanos, openings constructivos y nuevas reglas artísticas.

## T3.07 — Añadir mutaciones y regresiones

- **Estado:** `[x]`
- **Objetivo:** cubrir todos los fallos contractuales definidos en la spec.
- **Archivos previstos:** `tests/measurements/test_room_scene_comparison.py`,
  fixtures normalizados si son necesarios.
- **Validación:** wall/opening missing, unexpected object, longitudes,
  altura, espesor, width, height, sill, depth, offset, measured→derived,
  unknown→measured, fallback, fallback provenance, reconciliación y metadata
  ausente, flags y provenance; duplicate managed ID, normalized entity
  malformed, wrong units, wrong report/adapter/plan version, auxiliares no
  gestionados permitidos y ordering diferente semánticamente equivalente.
- **Evidencia:** la suite de comparación cubre directamente las mutaciones de
  geometría, estados, fallback, reconciliación, flags, provenance, versiones,
  entidades ausentes/inesperadas, metadata materializada ausente y escenas
  normalizadas no mutadas. La suite de normalización cubre duplicate managed
  ID, entidades malformadas, unidades, ownership y ordering. Ambos entrypoints
  producen `report_version=room-scene-comparison-1`; la incompatibilidad de
  reportes queda reservada a una futura capa de consumo/deserialización. La
  provenance no materializada por Blender (`method`, `uncertainty`,
  `reconciliation_id` y `delta_m`) permanece permitida.
- **Validación:** comparison `137/137 PASS`; normalize `22/22 PASS`; suite
  completa `230/230 PASS`. No hubo cambios de producción: la cobertura nueva
  fue de regresión sobre el comportamiento ya implementado.
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

T3.05 queda `[x]` tras la verificación read-only contra Blender real.
T3.06 queda `[x]` tras la acceptance real contra el artefacto generator-2 y
la equivalencia geométrica con el histórico. T3.07 queda `[x]` tras completar
la matriz de mutaciones y regresiones sin cambios de producción; T3.08 y
posteriores permanecen `[ ]`. T3.01–T3.04 y T3.05-P cubren el
contrato, la política matemática, la comparación pura room → plan y la
provenance aditiva v1.1; T3.05 añade el contrato y adapter read-only verificado
contra la escena real, pero no inicia `plan_to_scene` ni la integración
funcional posterior. T3.06 añade y valida el core plan → normalized scene
contra una escena generator-2 separada, sin sobrescribir el histórico.
