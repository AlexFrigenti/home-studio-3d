# Tareas: Room Measurement and Reconstruction

> Clasificación: T2
> Rama: `spec/002-room-measurement-and-reconstruction`
> Estado: schema JSON v1, fixture sintético, validador y primer generador Blender implementados; la altura general y las medidas verticales de los seis openings de `living-room-main` ya están registradas como medidas reales, y los espesores de pared siguen abiertos.

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

- **Estado:** `[x]`
- **Objetivo:** describir orden de captura, repetición, origen, segmentos, huecos, incertidumbre y evidencia.
- **Archivos:** `docs/setup/002-real-room-measurement-procedure.md`.
- **Validación:** procedimiento documentado para que otra persona pueda seguirlo con cinta métrica sin depender de rutas o herramientas propietarias; revisión humana independiente completada y aprobación explícita del propietario registrada antes de la primera sesión real.
- **Evidencia:** `docs/setup/002-real-room-measurement-procedure.md`, revisado y aprobado explícitamente por el propietario.
- **Rollback:** revertir el documento; mantener fuera del repo fotos y originales personales no aprobados.
- **Autorización:** aprobación del procedimiento antes de la primera sesión real.

## T2.11 — Definir política de fotos y referencias

- **Estado:** `[x]`
- **Objetivo:** establecer cómo las fotos apoyan la referencia visual sin convertirse en medidas sin escala.
- **Archivos:** sección documental y futuras referencias bajo `assets/references/<room_id>/` solo si se aprueban.
- **Validación:** escala conocida, privacidad, EXIF, procedencia y relación con `source_id`.
- **Rollback:** retirar solo referencias atribuibles y conservar originales fuera del repo.
- **Autorización:** autorización explícita para versionar cualquier foto o plano.
- **Evidencia:** el propietario aprobó explícitamente la política para una captura futura como referencia visual. Los originales permanecerán fuera del repositorio; el EXIF podrá conservarse únicamente en esos originales privados; cualquier imagen propuesta para Git deberá revisarse, sanearse y autorizarse de forma explícita posteriormente. Las notas podrán usar `source_id` neutros, sin rutas personales. Las fotografías no sustituyen medidas físicas salvo con escala conocida y documentación expresa. Se evitarán personas, documentos, pantallas, direcciones y otros elementos identificativos. Esta aprobación no afirma que existan fotografías reales ni autoriza su versionado.

## T2.12 — Preparar el primer salón real

- **Estado:** `[~]`
- **Objetivo:** preparar y avanzar la primera captura real manteniendo sus medidas canónicas y derivados aislados bajo `measurements/`.
- **Archivos:** `measurements/rooms/living-room-main.json`; cualquier `.blend` derivado conserva ubicación y snapshot explícitos.
- **Validación:** schema, procedimiento, incertidumbres, privacidad, trazabilidad y plan de rollback aprobados.
- **Rollback:** conservar el registro original; revertir solo representaciones derivadas.
- **Autorización:** aprobación específica recibida para registrar la altura general medida y transcribir las lecturas verticales de P1, P2, V1, V2, V3 y V4; el uso de Blender sigue pendiente de autorización/captura según proceda.
- **Evidencia actual:** `docs/setup/002-real-room-measurement-field-sheet.md` y `measurements/rooms/living-room-main.json`. El JSON contiene la altura suelo-techo `2.50 m ±0.01 m`, `measured` mediante `manual_tape` en la sesión vertical `2026-09-07`; esta segunda comprobación corrige la lectura previa de `3.00 m`, que queda superseded. También contiene las lecturas medidas de P1 (`2.00 m` de altura, `0.08 m` de profundidad), P2 (`2.30 m`, `0.05 m`), V1 y V2 (`0.92 m` de alféizar, `1.39 m` de altura y `0.08 m` de profundidad en ambos casos), y V3/V4 (`0.86 m` de alféizar, `1.25 m` de altura y `0.06 m` de profundidad en ambos casos).
- **Decisiones previas aprobadas:** `room_id`=`living-room-main`; nombre humano=`Salón principal`; `session_id`=`2026-09-06-session-01`; instrumento principal=cinta métrica; soporte auxiliar=croquis manual en papel; unidad canónica=`m`; incertidumbre base para una lectura directa normal y accesible con cinta=`±0.01 m`; ruta del JSON=`measurements/rooms/living-room-main.json`; sesión vertical adicional=`2026-09-07`.
- **Regla de incertidumbre aprobada:** `±0.01 m` no redondea automáticamente las lecturas; accesos peores, geometría difícil o menor confianza requieren una incertidumbre mayor adecuada; `estimated` debe identificarse y conservar una incertidumbre acorde con la estimación; si un dato no puede medirse o estimarse con confianza suficiente, usar `unknown`; no inventar precisión ni inferir valores silenciosamente.
- **Instancia de sesión:** no se crea una copia específica; la hoja canónica permanece reutilizable porque el contrato actual no define una ubicación ni convención para instancias documentales de sesiones. El JSON canónico conserva la trazabilidad de la altura y de las seis lecturas verticales.
- **Bloqueo restante:** los espesores accesibles siguen pendientes de captura o transcripción; no se ha regenerado Blender tras las nuevas medidas. T2.12 permanece `[~]`.
- **Pendiente antes de cerrar:** revisar las evidencias, resolver los espesores que puedan medirse con fiabilidad y ejecutar los derivados autorizados cuando se autorice la regeneración.

## T2.12-V — Preparar captura de geometría vertical real

- **Estado:** `[~]` — altura general y los seis openings capturados y registrados; quedan pendientes los espesores de pared donde puedan medirse con fiabilidad.
- **Objetivo:** definir una captura gradual de alturas, alféizares, profundidades y espesores reales para sustituir proxies/fallbacks solo cuando exista evidencia suficiente.
- **Instrumento y registro:** para cada lectura futura anotar instrumento, valor y unidad, `status` (`measured`, `estimated`, `derived` o `unknown`), incertidumbre y una nota sobre accesibilidad o dificultad. No exigir mediciones que requieran desmontar elementos.
- **Habitación:** la segunda comprobación de altura suelo → techo quedó capturada en la sesión vertical `2026-09-07` con `value=2.50`, `status=measured`, `uncertainty=0.01` y `method=manual_tape`; corrige la lectura previa de `3.00 m`. La geometría efectiva es `2.50 m` `measured` y el fallback de altura general no se aplica a `living-room-main`.
- **Puertas:** P1 y P2 tienen altura y profundidad `measured` transcritas; el sentido de apertura queda como dato opcional futuro.
- **Ventanas:** V1, V2, V3 y V4 tienen altura de hueco, alféizar y profundidad `measured` transcritas.
- **Paredes:** espesor real solo donde pueda medirse de forma fiable; mantener el fallback `0.10 m` mientras permanezca `unknown`.
- **Checklist breve de campo:**
  1. altura suelo → techo;
  2. P1: altura y profundidad si es accesible;
  3. P2: altura y profundidad si es accesible;
  4. V1: altura de hueco, alféizar y profundidad si es accesible;
  5. V2: altura de hueco, alféizar y profundidad si es accesible;
  6. V3: altura de hueco, alféizar y profundidad si es accesible;
  7. V4: altura de hueco, alféizar y profundidad si es accesible;
  8. espesores de pared únicamente en puntos fiables.
- **Regla de no inventar:** una altura o profundidad que no pueda medirse permanece `unknown`; Blender puede continuar mostrando el proxy y el pipeline puede continuar usando fallbacks documentados. Una aproximación visual nunca se convierte en `measured`.
- **Pipeline:** cualquier actualización futura seguirá JSON canónico → validator → generation plan → Blender. No se corrige la escena manualmente ni se promocionan estados de forma implícita.
- **Validación realizada:** diff y trazabilidad del JSON, validator, suite Python y generation plan revisados; no se ha regenerado Blender tras incorporar las nuevas medidas verticales.
- **Decisiones pendientes:** espesores realmente accesibles, sentido de apertura opcional y autorización específica para regenerar una variante derivada.

## T2.13 — Cerrar el slice y preparar PR

- **Estado:** `[ ]`
- **Objetivo:** revisar scope, documentación, riesgos, invariantes y gates; dejar la PR lista sin empezar el siguiente slice.
- **Archivos:** solo los artefactos aprobados de este checkpoint, sin ampliar el alcance.
- **Validación:** `git diff --check`, `git status --short`, diff completo, ausencia de secretos, ausencia de datos reales nuevos bajo `measurements/`, revisión de los binarios/preview derivados y revisión contra `.quality/QUALITY.md`/`CONTRIBUTING.md`.
- **Rollback:** revertir el commit documental si el contrato requiere cambios antes de aprobarse.
- **Autorización:** autorización explícita para commit/push/PR; el merge queda fuera de esta tarea.
