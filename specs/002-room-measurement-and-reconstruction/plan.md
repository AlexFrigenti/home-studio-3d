# Room Measurement and Reconstruction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Definir y después implementar un contrato JSON versionado para convertir medidas reales en una representación Blender 1:1 reproducible, sin capturar todavía el salón real.

**Architecture:** Un archivo JSON por habitación será la fuente estructurada. Un parser/validador separado comprobará schema, unidades, topología e incertidumbre antes de que un generador `bpy` produzca una escena derivada en colecciones controladas; la decoración quedará separada de la arquitectura.

**Tech Stack:** JSON UTF-8 v1 aprobado, Python estándar para validación y plan lógico, Blender 5.2.1 LTS y `bpy` solo cuando exista autorización explícita, Git/GitHub para trazabilidad.

**Spec:** `specs/002-room-measurement-and-reconstruction/spec.md`

## Global Constraints

- `measurements/` es la fuente de verdad; Blender es representación derivada.
- JSON v1 es el formato canónico aprobado; YAML queda fuera del formato canónico y solo podrá ser un export opcional futuro.
- Unidad canónica: metros; Blender usa `METRIC` y `scale_length = 1.0`.
- Cada medida usa `measured`, `estimated`, `derived` o `unknown`.
- `1e-6 m` queda reservado a aritmética matemática, no a precisión física de una vivienda.
- La geometría debe soportar paredes no paralelas, L, retranqueos, pilares y segmentos múltiples.
- Las puertas y ventanas se anclan a `wall_id` y offset desde el inicio del segmento.
- No se corregirán medidas reales para hacer que Blender encaje.
- No se capturarán medidas reales ni se modelará el salón en las fases documentales de este slice.
- No se instalarán herramientas ni se modificarán medidas reales o escenas canónicas; la escena sintética derivada de esta fase tiene destino de prueba explícito.
- Todas las rutas versionadas deben ser relativas al repo o expresadas mediante variables, nunca rutas personales absolutas.

---

## Archivos y áreas afectadas

### Artefactos de este slice

- Crear: `specs/002-room-measurement-and-reconstruction/spec.md`.
- Crear: `specs/002-room-measurement-and-reconstruction/plan.md`.
- Crear: `specs/002-room-measurement-and-reconstruction/tasks.md`.
- Crear: `measurements/schema/room-v1.schema.json`.
- Crear: `measurements/fixtures/room-v1-synthetic.json`.
- Crear: `blender/scripts/measurements/validate_measurements.py` y
  `tests/measurements/test_room_v1_validation.py`.
- Crear: `blender/scripts/measurements/generate_room.py` y
  `blender/scripts/measurements/validate_generated_room.py`.
- Crear: `tests/measurements/test_room_generation.py`,
  `blender/scenes/tests/002-room-v1-generated.blend` y
  `renders/previews/002-room-v1-generated/viewport-overview.png`.
- Crear: `docs/setup/002-room-generation-validation.md`.
- Modificar: ningún dato real, escena, asset ni configuración existente.
- Escenas/assets/medidas reales: `No aplica`; el único `.blend` de esta fase es la escena sintética indicada y no se crean fotos ni datos reales bajo `measurements/`.

### Archivos previstos para fases posteriores

- Crear: `docs/setup/002-real-room-measurement-procedure.md` para el procedimiento real de captura.
- Crear: futuras pruebas de comparación completa datos ↔ Blender y un informe de validación para el primer salón real.

Estos archivos son planificación, no entregables de la ejecución actual.

## Fases

### Fase 1 — Diseño y aprobación del schema

**Objetivo:** fijar JSON v1, el objeto de medida, versionado, unidades, estados e invariantes.

**Estado:** implementación documental y contrato JSON v1 completados en este slice.

**Archivos:** `measurements/schema/room-v1.schema.json` y documentación del slice.

**Validaciones:** revisión humana del modelo, ejemplos JSON válidos, ausencia de `TBD`/`TODO`, comprobación de que `unknown` no se interpreta como cero y revisión de compatibilidad con el slice 001.

**Rollback:** revertir el commit documental de la especificación; no tocar datos reales de `measurements/` ni escenas.

**Autorización:** aprobación humana explícita de JSON v1 recibida; el schema estricto queda materializado en el archivo indicado.

### Fase 2 — Fixture sintético de medidas

**Objetivo:** materializar el fixture conceptual 002 con habitación no rectangular, retranqueo o pilar, puerta, ventana, una medida `estimated` y otra `derived`.

**Estado:** fixture sintético implementado; no representa una vivienda real.

**Archivos:** `measurements/fixtures/room-v1-synthetic.json`; no modificar el fixture 001 ni datos reales.

**Validaciones:** parseo JSON, schema v1, IDs únicos, cierre de segmentos, declaración de fórmula/dependencias derivadas, clasificación de estados y ausencia de datos personales; el recálculo geométrico completo queda para una fase posterior.

**Rollback:** eliminar únicamente el fixture sintético o revertir su commit; conservar intactos `measurements/rooms/` y las escenas canónicas.

**Autorización:** aprobación del schema recibida; la estructura bajo `measurements/` se limita al schema y fixture sintéticos de este slice.

### Fase 3 — Validador de medidas

**Objetivo:** implementar un validador que rechace schema/unidades/topología/estados inválidos y devuelva warnings/fails trazables.

**Estado:** validación mínima estructural y determinista implementada; las reglas geométricas avanzadas quedan para una fase posterior.

**Archivos:** `blender/scripts/measurements/validate_measurements.py` y `tests/measurements/test_room_v1_validation.py`; no tocar Blender durante esta fase.

**Validaciones:** JSON/schema estricto declarado, unidades, versión, referencias de pared, conexión y cierre de segmentos, límites laterales y altura máxima de huecos, estados/incertidumbre, `derived`, `unknown` y canonización estable; `1e-6 m` solo para matemática.

**Rollback:** revertir el script y las pruebas; no cambiar ningún JSON real para hacer pasar un test.

**Autorización:** aprobación del schema y de la interfaz del validador; no se permite acceso a rutas externas.

### Fase 4 — Generador Blender

**Objetivo:** generar arquitectura 1:1 a partir de un objeto ya validado, con origen/ejes explícitos y colecciones separadas.

**Estado:** generador v1 implementado para el fixture sintético; no consume datos reales.

**Archivos:** `blender/scripts/measurements/generate_room.py`,
`tests/measurements/test_room_generation.py` y la escena derivada de prueba.

**Estrategia:** validar primero el JSON, reiniciar solo la escena de prueba,
crear una colección raíz `HS3D_ROOM_<room_id>` con subcolecciones separadas,
usar paredes prismáticas desde segmentos ordenados, suelo poligonal, proxies
de openings y proxy del elemento fijo. El espesor `unknown` usa solo un
fallback de proxy explícito, no cambia el dato canónico.

**Validaciones:** entrada validada obligatoria, nombres estables, transformaciones aplicadas, dimensiones comparadas con `1e-6 m`, metadata de estados/source IDs, no duplicación y no sobrescritura de una salida existente.

**Rollback:** generar en una variante o archivo desechable, guardar snapshot antes de operaciones destructivas y retirar solo la salida de prueba verificada.

**Autorización:** autorización explícita para ejecutar `bpy`, abrir/guardar escenas y modificar cualquier archivo Blender.

### Fase 5 — Validación numérica datos ↔ Blender

**Objetivo:** comprobar que la representación coincide con medidas y derivaciones sin silenciar discrepancias.

**Estado:** validación Blender específica implementada para la escena sintética; la comparación ampliada del primer salón real queda posterior.

**Archivos:** `blender/scripts/measurements/validate_generated_room.py`; no cambiar los datos de entrada.

**Validaciones:** unidades, puntos de pared, longitudes, área/altura derivadas, offsets de huecos, alturas, metadata, ausencia de duplicados y reglas de determinismo; repetir la regeneración con el mismo input.

**Rollback:** conservar los datos y eliminar solo informes o variantes generadas; una discrepancia se corrige en la captura/contrato, no en el generador.

**Autorización:** aprobación de los umbrales físicos y autorización para ejecutar Blender si la comparación requiere `bpy`.

### Fase 6 — Validación visual

**Objetivo:** confirmar que un preview técnico hace visibles las paredes, huecos, retranqueos/pilares y ausencia de artefactos graves.

**Estado:** preview técnico ligero generado e inspeccionado; no sustituye el preview del slice 001.

**Archivos:** `renders/previews/002-room-v1-generated/viewport-overview.png` y documentación de validación.

**Validaciones:** cámara/resolución registradas, inspección visual explícita y contraste con validación numérica. No usar la imagen para cambiar medidas.

**Rollback:** eliminar únicamente preview/informe de prueba con procedencia inequívoca; no eliminar fotos o escenas ajenas.

**Autorización:** autorización para iniciar Blender, ejecutar `bpy` y conservar una captura/render.

### Fase 7 — Procedimiento real de medición

**Objetivo:** documentar cómo medir una habitación real con cinta como mínimo, contrastar con láser/plano/fotos/escaneo y registrar incertidumbre.

**Archivos:** crear `docs/setup/002-real-room-measurement-procedure.md`; los originales fotográficos personales permanecen fuera del repo.

**Validaciones:** otra persona puede seguir el orden de captura, elegir el origen, repetir medidas críticas, registrar evidencia y producir JSON sin rutas locales.

**Rollback:** revertir solo el documento o retirar referencias no versionadas; no borrar datos reales sin identificar su procedencia.

**Autorización:** aprobación del procedimiento antes de una sesión real y autorización explícita para guardar medidas bajo `measurements/`.

### Fase 8 — Preparación del primer salón real

**Objetivo:** preparar una primera captura real únicamente después de cerrar y aprobar el contrato, sin mezclar decoración.

**Archivos:** decidir en una tarea posterior el nombre y la ubicación del primer archivo real bajo `measurements/`; cualquier `.blend` derivado tendrá ubicación y snapshot explícitos.

**Validaciones:** checklist de captura, revisión de privacidad, schema/validador, trazabilidad, comparación numérica y preview proporcional.

**Rollback:** conservar el original de medidas, crear variantes, revertir únicamente derivados; nunca reescribir el dato real para ajustar la escena.

**Autorización:** aprobación humana específica posterior del room ID, nombre/ubicación del archivo, medidas, fotos y primera ejecución del generador; esta fase no se ejecuta ahora.

### Siguiente fase propuesta — Geometría vertical real (en curso)

**Objetivo:** sustituir progresivamente los fallbacks y proxies verticales de
`living-room-main` por medidas reales aportadas por el usuario, conservando la
trazabilidad de cada cambio y sin introducir datos fuera de autorizaciones
específicas.

**Estado actual:** la segunda comprobación física de la altura suelo terminado
→ techo terminado de `living-room-main` está registrada como `2.50 m`, con
incertidumbre `±0.01 m`, `status=measured`, `method=manual_tape` y sesión
vertical `2026-09-07`. Corrige la lectura previa de `3.00 m`, que queda
superseded. El generation plan usa `2.50 m` como altura observada y geométrica
`measured`, sin fallback. P1, P2, V1, V2, V3 y V4 ya tienen medidas verticales
reales autorizadas y transcritas; ya no quedan proxies verticales activos para
`living-room-main`. Los datos horizontales canónicos no se reinterpretan.

**Captura realizada:** altura suelo-techo registrada en el JSON canónico con
`source_id=living-room-main-2026-09-07-vertical-session-02-height-floor-to-ceiling-correction`.

**Capturas verticales transcritas:** las sesiones autorizadas aportaron lecturas
de P1, P2, V1, V2, V3 y V4, registradas en el JSON canónico con
`status=measured`, `uncertainty=0.01` y `method=manual_tape`. V3 y V4 tienen
alféizar `0.86 m`, altura `1.25 m` y profundidad `0.06 m`.

**Espesores de pared transcritos:** la sesión vertical `2026-09-07` aportó
mediciones físicas en las jambas de P1/P2/V1/V2/V3/V4: `0.08 m`,
`status=measured`, `uncertainty=0.01` y `method=manual_tape`. Solo se actualizaron
`wall-00`, `wall-06`, `wall-07`, `wall-08`, `wall-14` y `wall-20`; los otros 16
segmentos permanecen `unknown` y conservan el fallback geométrico de `0.10 m`.
El espesor de muro no sustituye ni modifica la profundidad de un opening.

**Captura pendiente:** queda pendiente el espesor de pared de los segmentos
restantes solo donde pueda medirse con fiabilidad. Las capturas transcritas de
P1, P2, V1, V2, V3 y V4 requieren mantener revisión y trazabilidad antes de
usarse en derivados. El sentido de apertura de las puertas queda como dato
opcional futuro, no obligatorio para esta fase.

**Contrato de estados:** conservar estrictamente `measured`, `estimated`,
`derived` y `unknown`. Una medida no disponible permanece `unknown`; ningún
fallback o proxy se promociona silenciosamente a `measured`. Cuando se aporte
una medida real, se registra su instrumento, incertidumbre, evidencia y nota de
dificultad, manteniendo referencia al fallback sustituido.

**Pipeline y límites:** la evolución seguirá siendo JSON canónico → validator →
generation plan → Blender. Blender solo materializa datos validados y derivados;
no es fuente de verdad ni se permiten correcciones manuales de la escena. Si
una profundidad o espesor continúa desconocido, podrá seguir usándose su
fallback de generación documentado (`0.06 m` para profundidad de opening y
`0.10 m` para espesor de pared). Actualmente todas las profundidades verticales
de los openings de `living-room-main` están medidas; el fallback de profundidad
permanece disponible para otros datos `unknown`.
No se ha realizado una nueva generación Blender tras incorporar las nuevas
medidas verticales y espesores.

**Criterio de continuidad:** cada nueva captura o edición del JSON real necesita
autorización específica para la sesión, la evidencia y los campos a actualizar.
No se exige desmontar nada para obtener una medida; lo inaccesible permanece
`unknown`.

## Interfaz implementada y futura

El límite entre componentes será explícito:

- `parse_room(path) -> Room`: carga un JSON v1 y normaliza solo la representación,
  sin corregir valores.
- `validate_room(room) -> ValidationReport`: devuelve errores y warnings con
  `source_id`, regla y residual; no modifica `room`.
- `build_generation_plan(room) -> GenerationPlan`: valida un objeto ya cargado y
  calcula geometría lógica determinista sin tocar Blender.
- `generate_room(input_path, output_path, preview_path) -> GenerationReport`:
  carga y valida el JSON, crea arquitectura derivada en una escena de prueba,
  valida la escena dos veces y guarda un único `.blend`.
- `validate_generated_scene(room, root_collection) -> ValidationReport`:
  contrasta unidades, colecciones, geometría, metadata y conteos con `1e-6 m`.
- `compare_room_to_blender(room, scene) -> ComparisonReport`: compara datos con
  Blender usando incertidumbre física y registra discrepancias.

Los nombres son contrato de planificación; cualquier cambio requiere actualizar
`spec.md`, pruebas y tareas antes de implementarse.

## Validaciones transversales

- `git diff --check` y `git status --short` en cada cambio documental.
- Revisión completa del diff y confirmación de que solo aparecen los artefactos previstos de este slice.
- JSON/schema: parseo, versionado, IDs, unidades, estados y serialización determinista.
- Geometría: conexión, cierre, auto-intersecciones, huecos, alturas, ángulos y retranqueos.
- Blender: apertura, generación, dimensiones, unidades, transformaciones y preview cuando se autorice.
- Secretos/privacidad: escaneo de rutas, credenciales, EXIF, fotos y planos antes de versionar.
- Binarios/tamaños: revisión de cualquier `.blend`, PNG o cache antes de añadirlo.
- No usar tests artificiales, instalaciones nuevas ni renders pesados para fabricar PASS.

Los controles no disponibles se registran como `NO APLICA` o `PENDIENTE DE INFRAESTRUCTURA` según corresponda.

## Estrategia de reversión y compatibilidad

El contrato se versiona mediante `schema_version`; una versión incompatible
requiere migrador o nueva versión, no reinterpretación silenciosa. Los JSON
originales de medidas reales son inmutables después de publicados salvo una
corrección trazable con nueva revisión. Las escenas Blender son derivadas y se
regeneran en variantes separables. El generador no sobrescribe escenas
canónicas, no depende de rutas personales y conserva la separación entre
arquitectura y decoración.

## Dependencias externas

No se instalan dependencias en este slice. El futuro parser debe preferir Python
estándar para JSON; cualquier librería adicional, herramienta de captura,
LiDAR/escaneo, addon o servicio requiere revisión de procedencia, licencia,
seguridad y autorización explícita.
