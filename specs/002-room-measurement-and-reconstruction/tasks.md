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
- **Objetivo:** preparar, sin ejecutar ahora, la primera captura real y decidir más adelante su archivo bajo `measurements/`.
- **Archivos:** nombre y ubicación del primer archivo real pendientes de decisión específica; derivados aislados.
- **Validación:** schema, procedimiento, incertidumbres, privacidad, trazabilidad y plan de rollback aprobados.
- **Rollback:** conservar el registro original; revertir solo representaciones derivadas.
- **Autorización:** aprobación específica posterior del room ID, nombre/ubicación, captura y uso de Blender.
- **Evidencia parcial:** `docs/setup/002-real-room-measurement-field-sheet.md` preparada y aprobada explícitamente por el propietario para la primera sesión real. La hoja no contiene medidas reales y su aprobación no autoriza automáticamente la captura, la creación o el versionado del JSON, la ejecución del validator ni Blender/MCP.
- **Decisiones previas aprobadas:** `room_id`=`living-room-main`; nombre humano=`Salón principal`; `session_id`=`2026-09-06-session-01`; instrumento principal=cinta métrica; soporte auxiliar=croquis manual en papel; unidad canónica=`m`; incertidumbre base para una lectura directa normal y accesible con cinta=`±0.01 m`; ruta prevista del JSON=`measurements/rooms/living-room-main.json`.
- **Regla de incertidumbre aprobada:** `±0.01 m` no redondea automáticamente las lecturas; accesos peores, geometría difícil o menor confianza requieren una incertidumbre mayor adecuada; `estimated` debe identificarse y conservar una incertidumbre acorde con la estimación; si un dato no puede medirse o estimarse con confianza suficiente, usar `unknown`; no inventar precisión ni inferir valores silenciosamente.
- **Instancia de sesión:** no se crea una copia específica; la hoja canónica permanece reutilizable porque el contrato actual no define una ubicación ni convención para instancias documentales de sesiones. La ruta JSON queda prevista, pero el archivo no se crea.
- **Bloqueo restante:** falta únicamente la autorización específica para iniciar la captura real; T2.12 no se cierra con estas decisiones previas.
- **Pendiente antes de capturar:** autorización específica para iniciar la captura real.

## T2.12-V — Preparar captura de geometría vertical real

- **Estado:** `[ ]` — preparación documental únicamente; no iniciada y sin datos nuevos.
- **Objetivo:** definir una captura gradual de alturas, alféizares, profundidades y espesores reales para sustituir proxies/fallbacks solo cuando exista evidencia suficiente.
- **Instrumento y registro:** para cada lectura futura anotar instrumento, valor y unidad, `status` (`measured`, `estimated`, `derived` o `unknown`), incertidumbre y una nota sobre accesibilidad o dificultad. No exigir mediciones que requieran desmontar elementos.
- **Habitación:** capturar altura suelo → techo. El estado actual sigue siendo `observed=unknown`/`value=null`; la geometría `3.00 m` sigue siendo `derived` con fallback explícito y debe quedar trazable si se sustituye.
- **Puertas:** P1 y P2: altura real y profundidad/grosor si es accesible; sentido de apertura solo como dato opcional futuro.
- **Ventanas:** V1, V2, V3 y V4: altura real del hueco, altura de alféizar y profundidad si es accesible.
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
- **Validación prevista:** revisar diff y trazabilidad del JSON, ejecutar los gates oficiales, regenerar una variante derivada solo con autorización y comprobar que los fallbacks sustituidos quedan identificados.
- **Decisiones pendientes:** instrumento concreto y evidencia de cada lectura; incertidumbre de accesos difíciles; profundidades/espesores realmente accesibles; autorización específica para iniciar la sesión y actualizar el JSON.

## T2.13 — Cerrar el slice y preparar PR

- **Estado:** `[ ]`
- **Objetivo:** revisar scope, documentación, riesgos, invariantes y gates; dejar la PR lista sin empezar el siguiente slice.
- **Archivos:** solo los artefactos aprobados de este checkpoint, sin ampliar el alcance.
- **Validación:** `git diff --check`, `git status --short`, diff completo, ausencia de secretos, ausencia de datos reales nuevos bajo `measurements/`, revisión de los binarios/preview derivados y revisión contra `.quality/QUALITY.md`/`CONTRIBUTING.md`.
- **Rollback:** revertir el commit documental si el contrato requiere cambios antes de aprobarse.
- **Autorización:** autorización explícita para commit/push/PR; el merge queda fuera de esta tarea.
