# Multiple Layout Comparison / Variant Review v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir un comparator puro que compare dos o más FurniturePlans y sus SpatialValidationReports para la misma habitación, produciendo un VariantComparisonReport determinista y sin ranking subjetivo.

**Architecture:** T5.01 implementa `compare_furniture_variants.py` con planes y wrappers espaciales explícitos, `baseline_layout_id`, validación de binding/versiones y serialización determinista. T5.02 añade sets y deltas de items baseline→variante; T5.03 consume los reports espaciales ya calculados y añade summaries por layout y `spatial_delta`. No leerá layouts, room JSON ni Blender ni recalculará spatial validation.

**Tech Stack:** Python estándar, mappings/dataclasses inmutables según los patrones furniture existentes, `unittest`, JSON canónico y SHA-256 lógico opcional. Sin `bpy`, dependencias externas ni cambios de room pipeline.

**Spec:** `specs/005-multiple-layout-comparison-v1/spec.md`

## Global Constraints

- Input layout contract: `furniture-layout-1`.
- FurniturePlan version: `furniture-placement-generator-1`.
- Spatial report version: `furniture-spatial-validation-1`.
- Room plan version: `room-v1.1-generator-2`.
- Units: `m`.
- Coordinate system: `canonical_room`.
- Linear tolerance: `MATH_TOLERANCE_M = 1e-6` m.
- Baseline explícito; deltas v1 baseline→cada variante, no todas las parejas.
- `item_id` es identidad semántica; no se infiere identidad por posición.
- Spatial validation se consume, nunca se recalcula.
- No Blender/MCP, assets, materiales, previews ni artefactos `.blend`.
- No modificar `build_furniture_plan.py`, `validate_furniture_spatial.py`, room pipeline, schemas o layouts existentes.
- Todos los inputs y outputs deben ser serializables, deterministas y no mutables.

---

### Task 5.01: Fijar el contrato del VariantComparisonReport

**Files:**
- Create: `blender/scripts/furniture/compare_furniture_variants.py`
- Test: `tests/furniture/test_furniture_variant_comparison.py`
- Reference: `specs/005-multiple-layout-comparison-v1/spec.md`

**Interfaces:**
- Consumes: un `baseline_plan`, una secuencia de `variant_plans`, un wrapper espacial del baseline, una secuencia de wrappers espaciales de variantes y `baseline_layout_id` explícito.
- Produces: `VariantComparisonReport` con `report_version="furniture-variant-comparison-1"`, serialización estable y `logical_signature` calculada sin incluirse a sí misma.

- [x] **Step 1: Escribir tests de contrato en rojo**

Cubrir `missing_variant`, `baseline_layout_id_invalid`, IDs duplicados, binding room/version/unidades/coordinate system y rechazo de versiones desconocidas.

- [x] **Step 2: Ejecutar el módulo aislado**

Run: `python -m unittest tests/furniture/test_furniture_variant_comparison.py`

Expected: FAIL porque el módulo y su API todavía no existen.

- [x] **Step 3: Implementar el modelo y validación mínima**

Definir `REPORT_VERSION="furniture-variant-comparison-1"`, el wrapper espacial explícito, el report serializable y validación anti-cascade antes de cualquier delta. T5.01 no ejecuta comparaciones numéricas de items, por lo que `MATH_TOLERANCE_M` se aplica en T5.02.

- [x] **Step 4: Ejecutar el contrato**

Run: `python -m unittest tests/furniture/test_furniture_variant_comparison.py`

Expected: PASS para identidad, versiones, binding, canonicalización básica y no mutation.

**Cierre T5.01:** implementado y validado. El report no emite `common_items`, `added_items`, `removed_items`, deltas de plan ni deltas espaciales.

### Task 5.02: Implementar sets y deltas de plan

**Files:**
- Modify: `blender/scripts/furniture/compare_furniture_variants.py`
- Test: `tests/furniture/test_furniture_variant_comparison.py`

**Interfaces:**
- Consumes: planes ya construidos y validados con items ordenables por `id`.
- Produces: `common_items`, `added_items`, `removed_items`, `moved_items`, `rotated_items`, `resized_items`, `geometry_changed_items` y `metadata_changes` dentro de cada delta baseline→variante.

- [x] **Step 1: Añadir tests de sets y cambios**

Usar planes sintéticos con IDs comunes, añadidos y eliminados, y mutaciones independientes de posición, yaw, dimensiones, footprint/OBB/z bounds, type, dimensions status y source ID.

- [x] **Step 2: Ejecutar los tests nuevos**

Run: `python -m unittest tests/furniture/test_furniture_variant_comparison.py`

Expected: FAIL en cada familia de delta todavía no implementada.

- [x] **Step 3: Implementar comparación semántica**

Comparar por `item_id`, usar `MATH_TOLERANCE_M` para magnitudes lineales, shortest signed yaw delta periódico y la fórmula angular definida en la spec. Rechazar datos estructuralmente imposibles —dimensiones no positivas, z bounds invertidos y geometry degenerada— con `malformed_item_data`. Reportar metadata sin convertir un cambio de type/source en replacement.

- [x] **Step 4: Verificar orden y no mutation**

Run: `python -m unittest tests/furniture/test_furniture_variant_comparison.py`

Expected: PASS con entradas reordenadas y snapshots de inputs sin cambios.

**Cierre T5.02:** implementado y validado. Produce únicamente deltas de plan y metadata/provenance; T5.03 es el único checkpoint que consume semánticamente `valid`, `errors`, `warnings` y `limitations` del report espacial.

### Task 5.03: Integrar deltas de SpatialValidationReport

**Files:**
- Modify: `blender/scripts/furniture/compare_furniture_variants.py`
- Test: `tests/furniture/test_furniture_variant_comparison.py`

**Interfaces:**
- Consumes: `SpatialValidationReport` existente asociado explícitamente a cada layout.
- Produces: resumen por layout y `spatial_delta` baseline→variante con errores, warnings y limitations introducidos/resueltos.

- [x] **Step 1: Escribir tests con reports válidos y mutados**

Construir reports sintéticos a partir de `furniture-spatial-validation-1` y mutar únicamente sus findings/limitations para demostrar introducciones y resoluciones sin llamar al validator.

- [x] **Step 2: Ejecutar los tests de integración espacial**

Run: `python -m unittest tests/furniture/test_furniture_variant_comparison.py`

Expected: FAIL si el comparator recalcula, mezcla por mensaje o promociona limitations a errors.

- [x] **Step 3: Implementar consumo read-only de reports**

Normalizar findings mediante código, severity, item y entidades relacionadas; conservar `valid`, counts, checked items y limitations por layout; no invocar `validate_furniture_spatial`.

- [x] **Step 4: Confirmar anti-cascade espacial**

Run: `python -m unittest tests/furniture/test_furniture_variant_comparison.py`

Expected: PASS con reportes ordenados, findings introducidos/resueltos y limitations separadas.

**Cierre T5.03:** implementado y validado con `spatial_delta` determinista por variante, transición objetiva de `valid`, comparación de `checked_items`, deduplicación estructural de findings y summaries espaciales por layout. El comparator no invoca `validate_furniture_spatial`; `SpatialValidationReport.valid=false` permanece como hecho y no invalida por sí solo el report de comparación.

### Task 5.04: Completar matriz de regresión y mutaciones

**Files:**
- Modify: `tests/furniture/test_furniture_variant_comparison.py`
- Optional test fixture code: `tests/furniture/fixtures/variant_comparison_helpers.py`

**Interfaces:**
- Consumes: API pública `compare_layout_variants` y sus mappings serializables.
- Produces: cobertura de error estructurado, determinismo, serialización y no mutation.

- [ ] **Step 1: Añadir la matriz negativa**

Cubrir room mismatch, plan version mismatch, spatial version mismatch, duplicate item, malformed item, added/removed, move, rotate, resize, type/status/source, spatial error, limitation y baseline inválido.

- [ ] **Step 2: Añadir pruebas de determinismo**

Comparar reports con variantes, items, mappings y findings reordenados; exigir igualdad exacta de `to_dict()` y de `logical_signature`.

- [ ] **Step 3: Añadir pruebas de no mutation**

Tomar deep copies de planes, reports y wrappers, ejecutar el comparator y comprobar que las copias coinciden con los inputs posteriores.

- [ ] **Step 4: Ejecutar la matriz completa**

Run: `python -m unittest tests/furniture/test_furniture_variant_comparison.py`

Expected: PASS sin Blender y sin archivos temporales.

### Task 5.05: Cerrar acceptance sintética de living-room-main

**Files:**
- Create: `tests/furniture/fixtures/variant_comparison/baseline.json`
- Create: `tests/furniture/fixtures/variant_comparison/variant-b.json`
- Create: `tests/furniture/fixtures/variant_comparison/variant-c.json`
- Modify: `tests/furniture/test_furniture_variant_comparison.py`

**Interfaces:**
- Consumes: tres layouts `furniture-layout-1` del mismo `living-room-main` y el room plan actual.
- Produces: acceptance pura del report `furniture-variant-comparison-1`; no `.blend`, preview ni layout canónico productivo.

- [ ] **Step 1: Crear fixtures sintéticos válidos**

Baseline A tendrá tres items; B conservará IDs y cambiará posición/yaw; C demostrará resize y un par added/removed manteniendo placement espacialmente válido. Todos usarán provenance `synthetic`, IDs estables y `canonical_room`.

- [ ] **Step 2: Construir planes y reports en el test**

Usar `build_furniture_plan` y `validate_furniture_spatial` existentes únicamente como productores previos del acceptance; el comparator recibirá sus resultados y no los recalculará internamente.

- [ ] **Step 3: Verificar facts del report**

Exigir room binding común, summaries por layout, deltas esperados, spatial validity, limitations estables, ordering determinista, signature y no mutation.

- [ ] **Step 4: Verificar el caso espacial negativo separado**

Mutar un deepcopy de `SpatialValidationReport` para demostrar `errors_introduced`/`errors_resolved`, sin guardar una variante inválida como layout canónico.

### Task 5.06: Auditoría final y documentación de acceptance

**Files:**
- Modify: `specs/005-multiple-layout-comparison-v1/spec.md`
- Modify: `specs/005-multiple-layout-comparison-v1/plan.md`
- Modify: `specs/005-multiple-layout-comparison-v1/tasks.md`
- Create: `docs/setup/005-multiple-layout-comparison-validation.md`

**Interfaces:**
- Consumes: comparator, tests, fixtures y contratos de Slice 004.
- Produces: evidencia documental de Slice 005; no inicia Slice 006.

- [ ] **Step 1: Ejecutar gates furniture y room requeridos**

Run: `python -m unittest discover -s tests/furniture -p 'test_*.py'` y `python -m unittest discover -s tests/measurements -p 'test_*.py'`.

Expected: las suites existentes y las nuevas pasan sin Blender.

- [ ] **Step 2: Ejecutar syntax, JSON, privacy y diff checks**

Run: `python -c "import ast,json; from pathlib import Path; [ast.parse(p.read_text(encoding='utf-8'), filename=str(p)) for p in Path('.').rglob('*.py') if '.git' not in p.parts and '__pycache__' not in p.parts]; [json.loads(p.read_text(encoding='utf-8')) for p in Path('.').rglob('*.json') if '.git' not in p.parts]"`, validación JSON de fixtures, búsqueda de rutas/secrets y `git diff --check`.

Expected: PASS; sin paths personales, timestamps, UUIDs ni artefactos no autorizados.

- [ ] **Step 3: Auditar coherencia documental**

Verificar que spec, plan y tasks usan exactamente `furniture-variant-comparison-1`, baseline explícito, baseline→variantes, mismas exclusiones y ningún claim de Blender/visual work.

- [ ] **Step 4: Registrar cierre**

Documentar acceptance pura, limitations, provenance sintética, determinismo y boundary de Visual Furnishing & Materials. No crear `.blend`, preview ni iniciar Slice 006.
