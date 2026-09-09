# Especificación: Multiple Layout Comparison / Variant Review v1

> Estado: T5.01–T5.04 implementados y validados; T5.05–T5.06 no implementados.
>
> Rama: `spec/005-multiple-layout-comparison-v1`

## Objetivo

Permitir responder de forma estructurada y determinista qué cambia entre dos o más distribuciones de furniture para la misma habitación, sin decidir subjetivamente cuál es mejor.

El slice compara hechos contractuales derivados de `FurniturePlan` y de los `SpatialValidationReport` ya producidos. No construye planes, no recalcula spatial validation y no consulta Blender.

## Alcance

T5.01–T5.03 implementan un core puro equivalente a:

```text
compare_layout_variants(
    baseline_plan,
    variant_plans,
    baseline_spatial_report,
    variant_spatial_reports,
    *,
    baseline_layout_id
) -> VariantComparisonReport
```

El wrapper de cada report espacial es `{layout_id, room_id, room_plan_version, room_logical_signature, units, coordinate_system, report}` porque el `SpatialValidationReport` de T4 no materializa por sí solo todos esos campos de binding. El comparator es serializable, determinista, no mutable e independiente de `bpy`, layouts originales y room JSON. T5.01 valida contrato y binding; T5.02 compara items y metadata/provenance del plan; T5.03 compara facts espaciales ya calculados sin recalcularlos.

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
  "units": "m",
  "coordinate_system": "canonical_room",
  "furniture_plan_version": "furniture-placement-generator-1",
  "spatial_report_version": "furniture-spatial-validation-1",
  "errors": [],
  "warnings": [],
  "info": [],
  "summary": {
    "variant_count": 2,
    "layout_bindings": [
      {
        "layout_id": "layout-a",
        "furniture_plan_logical_signature": "plan-a",
        "spatial_report_version": "furniture-spatial-validation-1"
      },
      {
        "layout_id": "layout-b",
        "furniture_plan_logical_signature": "plan-b",
        "spatial_report_version": "furniture-spatial-validation-1"
      }
    ],
    "variant_summaries": [
      {
        "layout_id": "layout-b",
        "common_count": 0,
        "added_count": 0,
        "removed_count": 0,
        "changed_count": 0,
        "unchanged_count": 0,
        "moved_count": 0,
        "rotated_count": 0,
        "resized_count": 0,
        "metadata_changed_count": 0
      }
    ],
    "error_count": 0,
    "warning_count": 0,
    "info_count": 0
  },
  "pairwise_deltas": [
    {
      "from_layout_id": "layout-a",
      "to_layout_id": "layout-b",
      "common_items": [],
      "added_items": [],
      "removed_items": [],
      "changed_items": [],
      "unchanged_items": [],
      "geometry_changed_items": [],
      "metadata_changed_items": [],
      "moved_items": [],
      "rotated_items": [],
      "resized_items": [],
      "classification": {},
      "geometry_changes": [],
      "metadata_changes": [],
      "summary": {
        "common_count": 0,
        "added_count": 0,
        "removed_count": 0,
        "changed_count": 0,
        "unchanged_count": 0,
        "moved_count": 0,
        "rotated_count": 0,
        "resized_count": 0,
        "metadata_changed_count": 0
      }
    }
  ],
  "logical_signature": "0000000000000000000000000000000000000000000000000000000000000000"
}
```

`logical_signature` se calcula sobre la representación canónica sin ese propio campo. No es una golden binaria y no obliga a versionar un hash de cada acceptance. T5.01 emite el binding; T5.02 añade `pairwise_deltas` y `variant_summaries`; T5.03 añade `spatial_delta` a cada bloque baseline→variante y summaries espaciales por layout, derivados únicamente de reports ya calculados.

### `per_layout` (reservado tras T5.01)

El resumen por layout se reserva para T5.03. En T5.01, `summary` contiene únicamente `variant_count`, `layout_bindings` ordenados y conteos de errors/warnings/info del propio contrato.

En T5.03 cada resumen contiene únicamente hechos del plan y del report espacial ya recibido:

- `layout_id`;
- `furniture_plan_version`;
- `furniture_plan_logical_signature`;
- `spatial_report_version`;
- `spatial_valid`;
- `item_ids` ordenados;
- `item_count`;
- conteos y códigos estables de `errors`, `warnings` y `limitations`.

Un `SpatialValidationReport.valid=false` se conserva como hecho de esa variante. No convierte por sí solo el report de comparación en inválido si la comparación contractual puede realizarse.

### `pairwise_deltas` (T5.02)

La estrategia implementada es baseline explícito → cada variante, sin comparaciones variant→variant. Cada delta contiene:

- `from_layout_id`;
- `to_layout_id`;
- `common_items`;
- `added_items`;
- `removed_items`;
- `changed_items`;
- `unchanged_items`;
- `moved_items`;
- `rotated_items`;
- `resized_items`;
- `geometry_changed_items`;
- `metadata_changed_items`;
- `classification` por item común;
- `geometry_changes` para posición, yaw, dimensiones, footprint, OBB y z bounds;
- `metadata_changes` para `type`, `dimensions_status`, `source_id`, `anchor` y `placement_method` materializado.

`added_items` y `removed_items` contienen únicamente IDs semánticos. Los cambios de geometry y metadata contienen valores baseline, variant y delta cuando aplica. `spatial_delta` no forma parte de T5.02 y se añade en T5.03 por cada variante baseline→variante.

Todos los arrays se ordenan por identidad estable. Los registros de cambio contienen valores `baseline`, `variant` y `delta` cuando aplica; no contienen handles Blender, timestamps ni rutas.

## Identidad y sets

Para cada pareja baseline→variante:

- `common_items = intersection(item_id)`;
- `added_items = variant_ids - baseline_ids`;
- `removed_items = baseline_ids - variant_ids`.

El mismo `item_id` conserva identidad aunque cambien `type`, dimensiones, estado o `source_id`. Esos cambios se reportan como metadata/provenance o geometría. No se infiere identidad por posición.

Un item eliminado y otro añadido con IDs distintos no se presenta como replacement. Si un mismo `item_id` contiene datos incompatibles o malformados, se emite un error estructurado y se omiten sus deltas derivados.

La validación estructural T5.02 rechaza `dimensions_m` no finitas, cero o negativas; exige `z_min_m <= z_max_m`; y rechaza footprints y OBB degeneradas. La footprint debe aportar cuatro puntos 2D finitos con área no degenerada. `obb_2d` debe contener ejes 2D finitos, ortonormales y no degenerados, half-extents estrictamente positivos y corners no degeneradas. No se añade una regla nueva de consistencia entre footprint y OBB.

## Deltas geométricos

Para items comunes se comparan independientemente:

- `position_xy_m` y sus componentes `dx_m`, `dy_m`;
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
- `placement_method` cuando esté materializado a nivel de plan o en `provenance` del item;
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

- `introduced_errors`, `resolved_errors`, `persistent_errors`;
- `introduced_warnings`, `resolved_warnings`, `persistent_warnings`;
- `introduced_limitations`, `resolved_limitations`, `persistent_limitations`;
- transición objetiva `unchanged_valid`, `unchanged_invalid`, `became_valid` o `became_invalid`;
- `checked_items_delta` con baseline, variante, IDs añadidos/eliminados y delta de count.

Estos hechos viven en `spatial_delta` dentro de cada bloque baseline→variante. Los findings se identifican por código, severidad, item, entidades relacionadas y details contractuales; `message` no participa en la identidad. Las entradas equivalentes se deduplican y se ordenan canónicamente. El summary añade `spatial_summaries` por layout y conteos de introducidos/resueltos/persistentes. Un report espacial `valid=false` no invalida el `VariantComparisonReport` si el binding y el contenido son comparables; sí se conserva como `spatial_valid`.

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

El comparator exige un baseline y al menos una variante, IDs de layout únicos y un `baseline_layout_id` explícito que pertenezca al conjunto. La lista canónica de layouts se ordena por `layout_id`; los deltas futuros solo serán baseline→variante, evitando una explosión O(N²). Comparaciones entre variantes no baseline quedan para una versión posterior.

## `valid`, errors y anti-cascade

`valid` indica que el report pudo validar contractualmente todos los inputs. En T5.01 warnings/info no invalidan y permanecen vacíos; la validez espacial de una variante se consumirá en T5.03 sin recalcularla.

Errores contractuales mínimos:

- `missing_variant`;
- `duplicate_layout_id`;
- `baseline_layout_id_invalid`;
- `room_id_mismatch`;
- `room_plan_version_mismatch`;
- `room_plan_signature_mismatch`;
- `units_mismatch`;
- `coordinate_system_mismatch`;
- `unsupported_furniture_plan_version`;
- `unsupported_spatial_report_version`;
- `spatial_report_missing`;
- `spatial_report_layout_mismatch`;
- `malformed_variant_input`;
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

## Estado de implementación T5.01–T5.04

T5.01–T5.04 están implementados en `blender/scripts/furniture/compare_furniture_variants.py` y cubiertos por `tests/furniture/test_furniture_variant_comparison.py`. El módulo valida versiones, baseline explícito, cardinalidad, binding room/plan/spatial, ordering canónico, serialización JSON, firma lógica, inputs malformados y no mutación. T5.02 añade sets semánticos y deltas baseline→variante de items, geometry efectiva y metadata/provenance. T5.03 añade summaries por layout y `spatial_delta` de errores, warnings, limitations, checked items y transiciones de validez, sin invocar el validador espacial. T5.04 amplía la regresión con 75 tests de contrato, mutaciones, límites de tolerancia, payloads malformados, deduplicación, determinismo, firma y no mutación. No implementa acceptance canónica ni Blender.

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
