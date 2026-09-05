# Room Measurement and Reconstruction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Definir y después implementar un contrato JSON versionado para convertir medidas reales en una representación Blender 1:1 reproducible, sin capturar todavía el salón real.

**Architecture:** Un archivo JSON por habitación será la fuente estructurada. Un parser/validador separado comprobará schema, unidades, topología e incertidumbre antes de que un generador `bpy` produzca una escena derivada en colecciones controladas; la decoración quedará separada de la arquitectura.

**Tech Stack:** JSON UTF-8 v1 aprobado, Python estándar para parser/validador futuro, Blender 5.2.1 LTS y `bpy` solo cuando exista autorización explícita, Git/GitHub para trazabilidad.

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
- No se instalarán herramientas, no se modificará `measurements/` y no se crearán `.blend` en el cierre documental actual.
- Todas las rutas versionadas deben ser relativas al repo o expresadas mediante variables, nunca rutas personales absolutas.

---

## Archivos y áreas afectadas

### Artefactos de este slice

- Crear: `specs/002-room-measurement-and-reconstruction/spec.md`.
- Crear: `specs/002-room-measurement-and-reconstruction/plan.md`.
- Crear: `specs/002-room-measurement-and-reconstruction/tasks.md`.
- Modificar: ninguno.
- Escenas/assets/medidas: `No aplica`; no se crean `.blend`, fotos ni archivos bajo `measurements/`.

### Archivos previstos para fases posteriores

- Crear: `measurements/fixtures/002-room-measurement.json` para materializar el fixture conceptual después de aprobar el schema.
- Crear: `blender/scripts/measurements/validate_measurements.py`, `tests/measurements/test_schema.py` y `tests/measurements/test_validator.py`.
- Crear: `blender/scripts/measurements/generate_room.py` y `tests/measurements/test_generation_signature.py`.
- Crear: `docs/setup/room-measurement-procedure.md` para el procedimiento real de captura.
- Crear: un informe de validación y, solo si se autoriza, una escena/preview de prueba en áreas separadas.

Estos archivos son planificación, no entregables de la ejecución actual.

## Fases

### Fase 1 — Diseño y aprobación del schema

**Objetivo:** fijar JSON v1, el objeto de medida, versionado, unidades, estados e invariantes.

**Archivos:** revisar `spec.md`; en esta fase del slice solo se crean los tres artefactos documentales indicados arriba.

**Validaciones:** revisión humana del modelo, ejemplos JSON válidos, ausencia de `TBD`/`TODO`, comprobación de que `unknown` no se interpreta como cero y revisión de compatibilidad con el slice 001.

**Rollback:** revertir el commit documental de la especificación; no tocar `measurements/` ni escenas.

**Autorización:** aprobación humana explícita de JSON v1 recibida; el schema completo aún debe cerrarse antes de crear el fixture.

### Fase 2 — Fixture sintético de medidas

**Objetivo:** materializar el fixture conceptual 002 con habitación no rectangular, retranqueo o pilar, puerta, ventana, una medida `estimated` y otra `derived`.

**Archivos:** crear `measurements/fixtures/002-room-measurement.json`; no modificar el fixture 001 ni datos reales.

**Validaciones:** parseo JSON, schema v1, IDs únicos, cierre de segmentos, área derivada reproducible, clasificación de estados y ausencia de datos personales.

**Rollback:** eliminar únicamente el fixture sintético o revertir su commit; conservar intactos `measurements/rooms/` y las escenas canónicas.

**Autorización:** aprobación del schema; no requiere instalar herramientas, pero requiere autorización antes de introducir la primera estructura bajo `measurements/`.

### Fase 3 — Validador de medidas

**Objetivo:** implementar un validador que rechace schema/unidades/topología/estados inválidos y devuelva warnings/fails trazables.

**Archivos:** crear `blender/scripts/measurements/validate_measurements.py`, `tests/measurements/test_schema.py` y `tests/measurements/test_validator.py`; no tocar Blender durante la primera versión del parser.

**Validaciones:** tests deterministas para schema, estados, IDs, segmentos conectados, cierre, auto-intersecciones evidentes, huecos dentro de paredes, alturas e incertidumbre; `1e-6 m` solo para matemática.

**Rollback:** revertir el script y las pruebas; no cambiar ningún JSON real para hacer pasar un test.

**Autorización:** aprobación del schema y de la interfaz del validador; no se permite acceso a rutas externas.

### Fase 4 — Generador Blender

**Objetivo:** generar arquitectura 1:1 a partir de un objeto ya validado, con origen/ejes explícitos y colecciones separadas.

**Archivos:** crear `blender/scripts/measurements/generate_room.py`; cualquier escena de salida debe vivir en un destino de pruebas separado.

**Validaciones:** entrada validada obligatoria, nombres estables, transformaciones aplicadas, dimensiones comparadas con incertidumbre, no sobrescritura canónica y reporte de source IDs.

**Rollback:** generar en una variante o archivo desechable, guardar snapshot antes de operaciones destructivas y retirar solo la salida de prueba verificada.

**Autorización:** autorización explícita para ejecutar `bpy`, abrir/guardar escenas y modificar cualquier archivo Blender.

### Fase 5 — Validación numérica datos ↔ Blender

**Objetivo:** comprobar que la representación coincide con medidas y derivaciones sin silenciar discrepancias.

**Archivos:** crear `tests/measurements/test_data_blender_comparison.py` y un informe bajo `docs/validation/` solo después de aprobar la ubicación; no cambiar los datos de entrada.

**Validaciones:** unidades, puntos de pared, longitudes, área/altura derivadas, offsets de huecos, alturas, incertidumbre y reglas warning/fail; repetir la regeneración con el mismo input.

**Rollback:** conservar los datos y eliminar solo informes o variantes generadas; una discrepancia se corrige en la captura/contrato, no en el generador.

**Autorización:** aprobación de los umbrales físicos y autorización para ejecutar Blender si la comparación requiere `bpy`.

### Fase 6 — Validación visual

**Objetivo:** confirmar que un preview técnico hace visibles las paredes, huecos, retranqueos/pilares y ausencia de artefactos graves.

**Archivos:** si se conserva evidencia, crear un preview bajo `renders/previews/002-room-measurement/` y un informe asociado; no sustituir el preview del slice 001.

**Validaciones:** cámara/resolución registradas, inspección visual explícita y contraste con validación numérica. No usar la imagen para cambiar medidas.

**Rollback:** eliminar únicamente preview/informe de prueba con procedencia inequívoca; no eliminar fotos o escenas ajenas.

**Autorización:** autorización para iniciar Blender, ejecutar `bpy` y conservar una captura/render.

### Fase 7 — Procedimiento real de medición

**Objetivo:** documentar cómo medir una habitación real con cinta como mínimo, contrastar con láser/plano/fotos/escaneo y registrar incertidumbre.

**Archivos:** crear `docs/setup/room-measurement-procedure.md`; los originales fotográficos personales permanecen fuera del repo.

**Validaciones:** otra persona puede seguir el orden de captura, elegir el origen, repetir medidas críticas, registrar evidencia y producir JSON sin rutas locales.

**Rollback:** revertir solo el documento o retirar referencias no versionadas; no borrar datos reales sin identificar su procedencia.

**Autorización:** aprobación del procedimiento antes de una sesión real y autorización explícita para guardar medidas bajo `measurements/`.

### Fase 8 — Preparación del primer salón real

**Objetivo:** preparar una primera captura real únicamente después de cerrar y aprobar el contrato, sin mezclar decoración.

**Archivos:** decidir en una tarea posterior el nombre y la ubicación del primer archivo real bajo `measurements/`; cualquier `.blend` derivado tendrá ubicación y snapshot explícitos.

**Validaciones:** checklist de captura, revisión de privacidad, schema/validador, trazabilidad, comparación numérica y preview proporcional.

**Rollback:** conservar el original de medidas, crear variantes, revertir únicamente derivados; nunca reescribir el dato real para ajustar la escena.

**Autorización:** aprobación humana específica posterior del room ID, nombre/ubicación del archivo, medidas, fotos y primera ejecución del generador; esta fase no se ejecuta ahora.

## Interfaz futura propuesta

El límite entre componentes será explícito:

- `parse_room(path) -> Room`: carga un JSON v1 y normaliza solo la representación,
  sin corregir valores.
- `validate_room(room) -> ValidationReport`: devuelve errores y warnings con
  `source_id`, regla y residual; no modifica `room`.
- `generate_room(room, output_target) -> GenerationReport`: recibe solo un
  `Room` validado, crea arquitectura derivada y devuelve objetos/dimensiones
  comprobados.
- `compare_room_to_blender(room, scene) -> ComparisonReport`: compara datos con
  Blender usando incertidumbre física y registra discrepancias.

Los nombres son contrato de planificación; cualquier cambio requiere actualizar
`spec.md`, pruebas y tareas antes de implementarse.

## Validaciones transversales

- `git diff --check` y `git status --short` en cada cambio documental.
- Revisión completa del diff y confirmación de tres archivos únicamente en este slice.
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
