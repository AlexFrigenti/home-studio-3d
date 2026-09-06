# Tareas: Room Measurement and Reconstruction

> Clasificación: T2
> Rama: `spec/002-room-measurement-and-reconstruction`
> Estado: schema JSON v1, fixture sintético, validador y primer generador Blender implementados; no se han ejecutado tareas de datos reales.

Estados: `[ ]` pendiente · `[~]` en curso · `[x]` validada · `[!]` bloqueada.

La ejecución será proporcional y no convertirá microtareas en subagentes. Cada
tarea deberá conservar la autoridad de `measurements/`, registrar evidencia real
y detenerse ante una discrepancia no resuelta.

## T2.01 — Confirmar alcance y autoridad

- **Estado:** `[x]`
- **Objetivo:** aprobar que el slice define contrato de medidas y no modela todavía el salón real.
- **Archivos:** `spec.md`, `plan.md`, `tasks.md`.
- **Validación:** revisión humana de alcance, exclusiones, `measurements/` como fuente de verdad e invariantes.
- **Rollback:** revertir solo los artefactos documentales.
- **Autorización:** aprobación explícita del alcance documental T2 recibida.

## T2.02 — Evaluar YAML frente a JSON

- **Estado:** `[x]`
- **Objetivo:** elegir un único formato canónico y fijar reglas de serialización determinista.
- **Archivos:** `spec.md` y, si cambia la decisión, `plan.md`.
- **Validación:** comparar parseo, ambigüedad, diffs, dependencias y compatibilidad futura.
- **Rollback:** documentar la decisión alternativa antes de crear datos; no migrar archivos inexistentes.
- **Autorización:** aprobación humana de JSON v1 recibida; YAML queda fuera del formato canónico v1.

## T2.03 — Definir schema v1

- **Estado:** `[x]`
- **Objetivo:** fijar campos mínimos, tipos, estados de incertidumbre, referencias de evidencia y reglas de evolución.
- **Archivos:** `measurements/schema/room-v1.schema.json`, `spec.md`.
- **Validación:** schema JSON estricto parseable, contrato v1 declarado, estados condicionales, `unknown` sin valor y `derived` con fórmula/dependencias.
- **Rollback:** subir una nueva `schema_version` o revertir el documento; no reinterpretar datos publicados.
- **Autorización:** contrato implementado solo para datos sintéticos; cualquier medida real requiere una decisión posterior.

## T2.04 — Fijar coordenadas, unidades y tolerancias

- **Estado:** `[x]`
- **Objetivo:** definir origen, ejes, winding, metros, precisión almacenada, incertidumbre física y tolerancias de cálculo/visualización.
- **Archivos:** `spec.md`, `plan.md`.
- **Validación:** ejemplos con rectángulo, ángulo no recto, retranqueo y estimación; verificar que `1e-6 m` no se use como precisión doméstica.
- **Rollback:** revisar la propuesta antes de materializar JSON o escenas; mantener `measurements/` intacto.
- **Autorización:** baseline inicial de cinta y láser aprobado; cada medida real deberá conservar su incertidumbre explícita.

## T2.05 — Definir fixture sintético 002

- **Estado:** `[x]`
- **Objetivo:** describir y después materializar una habitación con retranqueo/pilar, puerta, ventana, `estimated` y `derived`.
- **Archivos:** `measurements/fixtures/room-v1-synthetic.json`.
- **Validación:** fixture parseable y válido, frontera conectada/cerrada, retranqueo, puerta, ventana, enchufe opcional, estados, fórmula/dependencias derivadas y canonización estable; sin decoración/datos personales.
- **Rollback:** eliminar únicamente el fixture sintético; nunca borrar medidas reales.
- **Autorización:** fixture sintético autorizado; no contiene datos reales.

## T2.06 — Diseñar e implementar el validador

- **Estado:** `[x]`
- **Objetivo:** producir un `ValidationReport` con errores/warnings trazables sin modificar la entrada.
- **Archivos:** `blender/scripts/measurements/validate_measurements.py`, `tests/measurements/test_room_v1_validation.py`.
- **Validación:** JSON/schema declarado, unidades, versión, referencias de pared, conexión/cierre, límites laterales y altura máxima de huecos, estados/incertidumbre, `derived`, `unknown` y canonización estable; `python -m unittest discover -s tests/measurements -p test_room_v1_validation.py -v` pasa 8/8; auto-intersecciones y reglas Blender avanzadas quedan pendientes.
- **Rollback:** revertir script/pruebas; no ajustar datos para satisfacer el validador.
- **Autorización:** implementación mínima con biblioteca estándar; no se instalaron dependencias.

## T2.07 — Diseñar e implementar el generador Blender

- **Estado:** `[x]`
- **Objetivo:** convertir un `Room` validado en arquitectura derivada 1:1 con colecciones y source IDs claros.
- **Archivos:** `blender/scripts/measurements/generate_room.py`, `tests/measurements/test_room_generation.py` y `blender/scenes/tests/002-room-v1-generated.blend`.
- **Validación:** input validado antes de generar, `METRIC`/`scale_length=1.0`, colección raíz `HS3D_ROOM_<room_id>`, paredes desde segmentos ordenados, suelo poligonal, proxies de openings/fixed elements, transformaciones aplicadas, metadata de estados y no sobrescritura de una salida existente.
- **Rollback:** snapshot/variante separable; retirar solo la salida de prueba.
- **Autorización:** explícita recibida para ejecutar `bpy` y guardar la escena sintética de prueba.

## T2.08 — Probar regeneración determinista

- **Estado:** `[x]`
- **Objetivo:** demostrar que el mismo JSON v1 y versión del generador producen la misma firma de geometría/informe.
- **Archivos:** `generate_room.py`, `tests/measurements/test_room_generation.py` y la escena derivada.
- **Validación:** dos generaciones controladas en la misma escena, comparación de nombres, puntos, dimensiones, metadata y firma lógica; cero duplicados residuales y ningún ajuste manual oculto.
- **Rollback:** eliminar solo salidas temporales; conservar el JSON de entrada y su hash.
- **Autorización:** fixture y destino de pruebas aprobados.

## T2.09 — Validar representación en Blender

- **Estado:** `[x]`
- **Objetivo:** comprobar `METRIC`, `scale_length=1.0`, geometría, huecos, alturas y correspondencia datos ↔ Blender.
- **Archivos:** `blender/scripts/measurements/validate_generated_room.py`, escena derivada y preview técnico.
- **Validación:** comparación numérica con `1e-6 m` para geometría derivada, unidades, boundary, altura, posiciones de huecos, fixed element, metadata, ausencia de duplicados y apertura controlada; sin modificar input ni modelar el salón real.
- **Rollback:** cerrar sin sobrescribir escenas canónicas y eliminar/isolar la variante creada.
- **Autorización:** autorización explícita recibida para iniciar Blender y ejecutar `bpy` en la escena de prueba.

## T2.10 — Documentar el procedimiento de toma de medidas

- **Estado:** `[ ]`
- **Objetivo:** describir orden de captura, repetición, origen, segmentos, huecos, incertidumbre y evidencia.
- **Archivos:** futuro `docs/setup/room-measurement-procedure.md`.
- **Validación:** otra persona puede seguirlo con cinta métrica sin depender de rutas o herramientas propietarias.
- **Rollback:** revertir el documento; mantener fuera del repo fotos y originales personales no aprobados.
- **Autorización:** aprobación del procedimiento antes de la primera sesión real.

## T2.11 — Definir política de fotos y referencias

- **Estado:** `[ ]`
- **Objetivo:** establecer cómo las fotos apoyan la referencia visual sin convertirse en medidas sin escala.
- **Archivos:** sección documental y futuras referencias bajo `assets/references/<room_id>/` solo si se aprueban.
- **Validación:** escala conocida, privacidad, EXIF, procedencia y relación con `source_id`.
- **Rollback:** retirar solo referencias atribuibles y conservar originales fuera del repo.
- **Autorización:** autorización explícita para versionar cualquier foto o plano.

## T2.12 — Preparar el primer salón real

- **Estado:** `[ ]`
- **Objetivo:** preparar, sin ejecutar ahora, la primera captura real y decidir más adelante su archivo bajo `measurements/`.
- **Archivos:** nombre y ubicación del primer archivo real pendientes de decisión específica; derivados aislados.
- **Validación:** schema, procedimiento, incertidumbres, privacidad, trazabilidad y plan de rollback aprobados.
- **Rollback:** conservar el registro original; revertir solo representaciones derivadas.
- **Autorización:** aprobación específica posterior del room ID, nombre/ubicación, captura y uso de Blender.

## T2.13 — Cerrar el slice y preparar PR

- **Estado:** `[ ]`
- **Objetivo:** revisar scope, documentación, riesgos, invariantes y gates; dejar la PR lista sin empezar el siguiente slice.
- **Archivos:** solo los artefactos aprobados de este checkpoint, sin ampliar el alcance.
- **Validación:** `git diff --check`, `git status --short`, diff completo, ausencia de secretos, ausencia de datos reales nuevos bajo `measurements/`, revisión de los binarios/preview derivados y revisión contra `.quality/QUALITY.md`/`CONTRIBUTING.md`.
- **Rollback:** revertir el commit documental si el contrato requiere cambios antes de aprobarse.
- **Autorización:** autorización explícita para commit/push/PR; el merge queda fuera de esta tarea.
