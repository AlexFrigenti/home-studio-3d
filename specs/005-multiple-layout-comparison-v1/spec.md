# Especificación: Multiple Layout Comparison / Variant Review v1

> Estado: diseño documental aprobado para implementación posterior. Slice 005 no está implementado.
>
> Rama: `spec/005-multiple-layout-comparison-v1`

## Objetivo

Permitir responder de forma estructurada y determinista qué cambia entre dos o más distribuciones de furniture para la misma habitación, sin decidir subjetivamente cuál es mejor.

El slice compara hechos contractuales derivados de `FurniturePlan` y de los `SpatialValidationReport` ya producidos. No construye planes, no recalcula spatial validation y no consulta Blender.

## Alcance

Slice 005 añadirá un core puro equivalente a:

```text
compare_layout_variants(
    variants,
    baseline_layout_id
) -> VariantComparisonReport
```

Cada entrada de `variants` transportará un `FurniturePlan` y el `SpatialValidationReport` correspondiente, asociados explícitamente por `layout_id`. El comparator será serializable, determinista, no mutable e independiente de `bpy`, layouts originales y room JSON.

## Fuentes de autoridad

- `furniture-layout-1` sigue siendo el contrato de entrada.
- `furniture-placement-generator-1` sigue siendo la versión del `FurniturePlan`.
- `furniture-spatial-validation-1` es la versión soportada del report espacial.
- `room-v1.1-generator-2` es la versión soportada del room generation plan.
- `measurements/` continúa siendo la autoridad arquitectónica indirecta del room plan.
- `item_id` es la identidad semántica de un item dentro de las variantes.

Slice 005 no crea un segundo contrato de placement ni modifica contratos T4.01–T4.05.

## Contrato `furniture-variant-comparison-1`

La salida mínima es un mapping serializable con esta forma:

```json
{
  "report_version": "furniture-variant-comparison-1",
  "valid": true,
  "room_id": "living-room-main",
  "baseline_layout_id": "layout-a",
  "room_plan_version": "room-v1.1-generator-2",
  "room_logical_signature": "0000000000000000000000000000000000000000000000000000000000000000",
  "compared_layout_ids": ["layout-a", "layout-b"],
  "per_layout": [],
  "pairwise_deltas": [],
  "errors": [],
  "warnings": [],
  "limitations": [],
  "logical_signature": "0000000000000000000000000000000000000000000000000000000000000000"
}
```

`logical_signature` se calcula sobre la representación canónica sin ese propio campo. No es una golden binaria y no obliga a versionar un hash de cada acceptance.

### `per_layout`

Cada resumen contiene únicamente hechos del plan y del report espacial ya recibido:

- `layout_id`;
- `furniture_plan_version`;
- `furniture_plan_logical_signature`;
- `spatial_report_version`;
- `spatial_valid`;
- `item_ids` ordenados;
- `item_count`;
- conteos y códigos estables de `errors`, `warnings` y `limitations`.

Un `SpatialValidationReport.valid=false` se conserva como hecho de esa variante. No convierte por sí solo el report de comparación en inválido si la comparación contractual puede realizarse.

### `pairwise_deltas`

La estrategia v1 es baseline explícito → cada variante. Cada delta contiene:

- `from_layout_id`;
- `to_layout_id`;
- `common_items`;
- `added_items`;
- `removed_items`;
- `moved_items`;
- `rotated_items`;
- `resized_items`;
- `geometry_changed_items` para footprint, OBB o z bounds que cambien sin quedar completamente descritos por posición, yaw o dimensiones;
- `metadata_changes` para `type`, `dimensions_status` y `source_id`;
- `spatial_deltas`.

Todos los arrays se ordenan por identidad estable. Los registros de cambio contienen valores `from`, `to` y `delta` cuando aplica; no contienen handles Blender, timestamps ni rutas.

## Identidad y sets

Para cada pareja baseline→variante:

- `common_items = intersection(item_id)`;
- `added_items = variant_ids - baseline_ids`;
- `removed_items = baseline_ids - variant_ids`.

El mismo `item_id` conserva identidad aunque cambien `type`, dimensiones, estado o `source_id`. Esos cambios se reportan como metadata/provenance o geometría. No se infiere identidad por posición.

Un item eliminado y otro añadido con IDs distintos no se presenta como replacement. Si un mismo `item_id` contiene datos incompatibles o malformados, se emite un error estructurado y se omiten sus deltas derivados.

## Deltas geométricos

Para items comunes se comparan independientemente:

- `position_xy_m` y sus componentes `dx_m`, `dy_m`;
- distancia lineal del movimiento;
- yaw canónico y delta angular periódico;
- `dimensions_m` y delta por componente;
- footprint efectiva;
- `obb_2d`;
- `z_min` y `z_max`.

La tolerancia lineal es exactamente `MATH_TOLERANCE_M = 1e-6` m. Un movimiento, resize o cambio geométrico solo se registra cuando excede esa tolerancia.

El delta angular es el signed shortest delta en grados dentro de `[-180, 180)`. La comparación angular usa una tolerancia computacional derivada, no física:

```text
theta_tolerance_rad = MATH_TOLERANCE_M /
                      max(max_plan_radius_m, MATH_TOLERANCE_M)
```

`max_plan_radius_m` se deriva del radio máximo de la geometría efectiva del item. Se convierte a grados únicamente para comparar yaw. No se introduce una constante angular independiente ni se permite división por cero.

## Metadata y provenance

Se comparan sin inventar campos:

- `type`;
- `dimensions_status`;
- `source_id`;
- `anchor`;
- `placement_method` cuando esté materializado a nivel de plan;
- `units`;
- `coordinate_system`.

`dimensions_status=synthetic` permanece `synthetic`. Un cambio de status o `source_id` es una diferencia de metadata/provenance, no una promoción de autoridad.

## SpatialValidationReport

El comparator recibe reports ya calculados y no llama a `validate_furniture_spatial`.

El wrapper de entrada debe asociar cada report a su `layout_id`, porque `SpatialValidationReport` actual no sustituye esa identidad. Se valida exactamente `furniture-spatial-validation-1`.

Para cada variante se conserva:

- `valid`;
- errores;
- warnings;
- limitations;
- `checked_items`.

Entre baseline y variantes se calculan:

- `errors_introduced`;
- `errors_resolved`;
- `warnings_introduced`;
- `warnings_resolved`;
- `limitations_introduced`;
- `limitations_resolved`;
- cambio de `valid`.

La identidad de un finding espacial se basa en sus campos estructurados estables —código, severidad, item y entidades relacionadas—, no en el texto humano del mensaje. Las limitations nunca se convierten en errores.

## Binding y compatibilidad

Todos los variants deben compartir exactamente:

- `room_id`;
- `room_plan_version`;
- `room_logical_signature`;
- `units`;
- `coordinate_system`;
- `furniture_plan_version`;
- `spatial_report_version`.

Un mismatch es error bloqueante. Las versiones desconocidas no se aceptan silenciosamente. Ante un error de binding no se emiten deltas geométricos ni de metadata.

El comparator exige entre 2 y N variantes, IDs de layout únicos y un `baseline_layout_id` explícito que pertenezca al conjunto. La lista canónica de layouts se ordena por `layout_id`; los deltas v1 solo son baseline→variante, evitando una explosión O(N²). Comparaciones entre variantes no baseline quedan para una versión posterior.

## `valid`, errors y anti-cascade

`valid` indica que el report pudo comparar contractualmente todos los inputs. Es independiente de que una variante tenga `spatial_valid=false`; esa condición aparece en `per_layout` y `spatial_deltas`.

Errores contractuales mínimos:

- `invalid_variant_count`;
- `duplicate_layout_id`;
- `missing_baseline_layout`;
- `room_id_mismatch`;
- `room_plan_version_mismatch`;
- `room_logical_signature_mismatch`;
- `units_mismatch`;
- `coordinate_system_mismatch`;
- `furniture_plan_version_mismatch`;
- `spatial_report_version_mismatch`;
- `spatial_report_binding_mismatch`;
- `duplicate_item_id`;
- `malformed_furniture_plan`;
- `malformed_spatial_report`.

Un binding inválido detiene los checks dependientes. Un item malformado produce un finding estable y no genera cascadas de deltas. Un item añadido o eliminado no produce findings de campos inexistentes.

## Determinismo y no mutación

La misma secuencia semántica de inputs produce el mismo report y la misma serialización canónica aunque se reordenen:

- variants de entrada;
- items de cada plan;
- findings y limitations espaciales;
- mappings internos.

La canonicalización normaliza `-0.0` a `0.0`, exige floats finitos, ordena mappings y utiliza el ordering semántico definido para arrays. El comparator no modifica FurniturePlans, SpatialValidationReports ni sus estructuras anidadas.

## Exclusiones

No forman parte de Slice 005:

- ranking de layouts;
- “best layout”;
- score estético, de confort, ergonomía o circulación;
- recomendaciones de IA;
- consulta de layout original o room JSON;
- spatial validation recalculada;
- Blender, bpy o normalización de escenas;
- side-by-side renders, cámaras, compositing o dashboard;
- assets reales, materiales, colores, PBR o iluminación;
- cambios en room pipeline;
- multi-room;
- fixed elements nuevos;
- artefacto `.blend` o preview comparativo.

## Acceptance propuesta

La acceptance será pura Python y usará `living-room-main` con tres planes sintéticos válidos:

- A: baseline con tres items;
- B: mismos IDs con movimiento y rotación dentro del floor polygon;
- C: diferencia de dimensiones y conjunto —un item eliminado y otro añadido— manteniendo un caso espacialmente válido.

Mutaciones negativas separadas cubrirán binding, versiones, item añadido/eliminado, movimiento, yaw, dimensiones, type/status/source, errores espaciales, limitations, ordering y no mutation. Una mutation de report espacial permitirá demostrar errores introducidos/resueltos sin crear un layout inválido permanente.

No se crearán layouts canónicos de producción ni artefactos Blender para cerrar Slice 005.

## Dependencias y Slice 006

Slice 005 depende de los contratos cerrados de Slice 004 y no modifica T4.01–T4.05.

Visual Furnishing & Materials queda fuera de scope y se reserva para un slice posterior: assets reales, materiales, colores, PBR, iluminación, styling, renders y cámaras.
