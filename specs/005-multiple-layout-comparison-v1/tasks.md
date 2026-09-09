# Tareas: Multiple Layout Comparison / Variant Review v1

> Estado del checkpoint actual: T5.01 implementada y validada; T5.02–T5.06 no implementadas.
>
> Rama: `spec/005-multiple-layout-comparison-v1`

## Contrato del slice

Slice 005 compara hechos entre dos o más variantes del mismo room mediante un comparator puro. Consume `furniture-layout-1`, `furniture-placement-generator-1`, `furniture-spatial-validation-1` y `room-v1.1-generator-2` sin modificar ninguno.

La salida es `furniture-variant-comparison-1`. El `baseline_layout_id` es explícito y los deltas v1 se calculan baseline→cada variante. `item_id` es identidad semántica. `MATH_TOLERANCE_M=1e-6` m se mantiene para magnitudes lineales; yaw usa delta periódico y tolerancia derivada de radio.

`valid` significa que los inputs son comparables contractualmente. El diseño posterior conservará la validez espacial de cada variante y comparará errores/warnings/limitations sin recalcularlos; T5.01 solo valida el binding del report espacial. No existe ranking subjetivo.

En el checkpoint T5.01, el report contiene únicamente binding/versiones, findings contractuales, summary de bindings y firma lógica. Los campos de items y los deltas espaciales se reservan para T5.02/T5.03.

## T5.01 [x] — Variant comparison contract

- [x] Fijar `furniture-variant-comparison-1` y la representación serializable de `VariantComparisonReport`.
- [x] Fijar la API explícita con baseline, variantes y wrappers espaciales; exigir `baseline_layout_id` explícito.
- [x] Validar un baseline + 1..N variantes, IDs únicos, room binding, versiones, unidades y coordinate system.
- [x] Fijar ordering canónico, normalización de `-0.0`, floats finitos, firma lógica excluida de su propio payload y exclusiones.
- [x] Cubrir errores de binding y anti-cascade antes de implementar deltas.

**Cierre:** el contrato rechaza inputs incompatibles sin consultar Blender ni recalcular spatial validation. No emite todavía deltas de items ni deltas espaciales.

## T5.02 — Pure comparison engine

- [ ] Comparar sets `common`, `added` y `removed` por `item_id`.
- [ ] Comparar posición, yaw periódico, dimensiones, footprint, OBB y z bounds.
- [ ] Reportar `moved_items`, `rotated_items`, `resized_items` y `geometry_changed_items` con `from`, `to` y `delta`.
- [ ] Reportar cambios de `type`, `dimensions_status` y `source_id` como metadata/provenance.
- [ ] No inferir replacements ni identidad por proximidad.

**Cierre:** dos planes compatibles producen deltas deterministas e independientes del ordering de entrada.

## T5.03 — Spatial report delta integration

- [ ] Asociar cada `SpatialValidationReport` al layout mediante el wrapper explícito.
- [ ] Resumir por layout `valid`, `errors`, `warnings`, `limitations` y `checked_items`.
- [ ] Calcular errores, warnings y limitations introducidos/resueltos por código y entidades estructuradas.
- [ ] Mantener limitations separadas de errors.
- [ ] No llamar `validate_furniture_spatial` dentro del comparator.

**Cierre:** el report compara resultados espaciales ya calculados sin cambiar su semántica.

## T5.04 — Regression and mutation matrix

- [ ] Cubrir add/remove, move, rotate, resize, footprint/OBB/z bounds, type, status y source.
- [ ] Cubrir room/version/signature/units/coordinate-system mismatch.
- [ ] Cubrir duplicate IDs, malformed plans, malformed spatial reports y baseline inválido.
- [ ] Cubrir ordering, canonical serialization, logical signature y no mutation.
- [ ] Cubrir error espacial y limitation introducidos/resueltos usando deep copies.

**Cierre:** cada mutación produce el finding o delta estructurado esperado sin cascadas redundantes.

## T5.05 — living-room-main variant acceptance

- [ ] Crear fixtures sintéticos dedicados en `tests/furniture/fixtures/variant_comparison/`.
- [ ] Definir baseline A, variante válida B con movimiento/rotación y variante válida C con resize y cambio de conjunto.
- [ ] Construir planes y reports previos con los productores T4 existentes.
- [ ] Verificar room binding, summaries, deltas, spatial validity, limitations, ordering, signature y no mutation.
- [ ] Mantener las mutaciones espaciales inválidas como casos negativos en memoria, no como acceptance layout canónico.

**Cierre:** acceptance pura reproducible para `living-room-main`, sin Blender, `.blend` ni preview.

## T5.06 — Documentation, privacy and final audit

- [ ] Reconciliar spec, plan y tasks contra la implementación real y los tests.
- [ ] Ejecutar furniture pure suite, room pure suite, Python/JSON syntax y `git diff --check`.
- [ ] Auditar privacy: sin rutas, UUIDs, timestamps, secrets, datos personales ni provenance inventada.
- [ ] Documentar acceptance, determinismo, limitations, rollback y provenance sintética.
- [ ] Mantener Visual Furnishing & Materials fuera de scope y no iniciar Slice 006.

**Cierre:** Slice 005 queda listo para revisión documental/PR sin artefactos Blender y sin trabajo de Slice 006.

## Dependencias y exclusiones

| Tarea | Depende de | Produce |
|---|---|---|
| T5.01 | Slice 004 | contrato y binding |
| T5.02 | T5.01 | deltas de plan |
| T5.03 | T5.01, T5.02 | deltas espaciales |
| T5.04 | T5.02, T5.03 | regresión y mutaciones |
| T5.05 | T5.01–T5.04 | acceptance sintética |
| T5.06 | T5.01–T5.05 | auditoría y documentación |

Fuera de scope: Blender/MCP, side-by-side rendering, cámaras, dashboard, assets reales, materiales, PBR, iluminación, ergonomía, circulación, ranking, recomendaciones, multi-room, fixed elements nuevos, cambios room pipeline y artefactos `.blend`.

## Checklist de cierre del slice

- [ ] `VariantComparisonReport` es puro, serializable y determinista.
- [ ] Todos los variants comparten room binding y versiones soportadas.
- [ ] `item_id` permanece como identidad semántica.
- [ ] Geometry, metadata/provenance y spatial facts se distinguen.
- [ ] No se recalcula spatial validation.
- [ ] No existe ranking subjetivo.
- [ ] Acceptance `living-room-main` es sintética y reproducible.
- [ ] No hay Blender/MCP ni artefactos visuales.
- [ ] Slice 006 permanece sin iniciar.
