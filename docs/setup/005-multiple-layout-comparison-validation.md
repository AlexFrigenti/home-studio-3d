# Slice 005 — Multiple Layout Comparison / Variant Review v1

## Propósito y estado

Slice 005 compara hechos contractuales entre un baseline y una o más variantes
de mobiliario para la misma habitación. El resultado es un
`VariantComparisonReport` puro, serializable y determinista; no decide cuál
layout es mejor.

T5.01–T5.06 están implementadas y auditadas en la rama
`spec/005-multiple-layout-comparison-v1`. T5.06 cierra la documentación,
privacidad, provenance, compatibilidad y gates del slice. No se modifican los
contratos de Slice 004 ni el room pipeline.

## Matriz de versiones y binding

| Contrato | Versión |
| --- | --- |
| Furniture layout | `furniture-layout-1` |
| FurniturePlan | `furniture-placement-generator-1` |
| SpatialValidationReport | `furniture-spatial-validation-1` |
| VariantComparisonReport | `furniture-variant-comparison-1` |
| Room generation plan | `room-v1.1-generator-2` |
| Units | `m` |
| Coordinate system | `canonical_room` |

Todos los planes comparados comparten `room_id`, versión y firma lógica del
room plan, unidades, sistema de coordenadas y versiones de FurniturePlan y
spatial report. Las versiones desconocidas o los mismatches de binding son
errores contractuales; no se aceptan versiones legacy silenciosamente.

El baseline es explícito mediante `baseline_layout_id`. Slice 005 compara
baseline → cada variante; no ejecuta comparaciones variant → variant ni todas
las parejas.

## Contrato de comparación

`compare_layout_variants(...)` consume FurniturePlans y wrappers de
SpatialValidationReports ya generados. No lee layouts originales ni room JSON,
no usa Blender y no llama a `validate_furniture_spatial`.

`item_id` es la identidad semántica. Los sets `common_items`, `added_items` y
`removed_items` se ordenan de forma canónica. Los items comunes producen:

- deltas de posición XY, yaw, dimensiones, footprint, OBB y z bounds;
- clasificación `unchanged`, `geometry_changed`, `metadata_changed` o
  `geometry_and_metadata_changed`;
- cambios de `type`, `dimensions_status`, `source_id`, `anchor` y
  `placement_method` cuando están materializados.

La tolerancia lineal es `MATH_TOLERANCE_M = 1e-6` m. El yaw usa delta angular
periódico signed shortest en `[-180, 180)`, con tolerancia derivada del radio
de la geometría efectiva. No se infiere identidad por posición ni se inventan
replacements.

## Deltas espaciales

T5.03 consume, sin recalcular, `valid`, errors, warnings, limitations y
`checked_items` de cada report espacial. Para cada variante produce hechos
`introduced`, `resolved` y `persistent` para errors, warnings y limitations,
además de la transición objetiva:

- `unchanged_valid`;
- `unchanged_invalid`;
- `became_valid`;
- `became_invalid`.

Las limitations permanecen separadas de errors y warnings. Un report espacial
`valid=false` no invalida automáticamente el `VariantComparisonReport` si el
binding y el contenido son comparables. Findings equivalentes se deduplican y
se identifican por campos contractuales estructurados; el mensaje humano no
participa en la identidad.

## Acceptance `living-room-main`

La acceptance pure Python está en
`tests/furniture/test_furniture_variant_acceptance.py` y usa los fixtures:

- `layouts/living-room-main/variants/baseline-a.json`;
- `layouts/living-room-main/variants/variant-b.json`;
- `layouts/living-room-main/variants/variant-c.json`.

Los tres fixtures usan `furniture-layout-1`, `room_id=living-room-main`,
unidades `m`, `canonical_room`, placement `manual`,
`dimensions_status=synthetic` y source IDs sintéticos estables. No contienen
assets reales, manufacturers, rutas ni datos personales.

La pipeline real genera el room plan `room-v1.1-generator-2` con firma:

```text
182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a
```

Las firmas reproducibles de FurniturePlan son:

```text
A  b107d146c81a300858d33d48265d7e42480c88f6ed8443e6a54f80a008e19a0c
B  32b40195178f96178e2ba64ecc637e09c4c941ccc6fabe50c216049a0a52d70e
C  a723fb4c9e89495aa441dd184b8cb2a3579badfcfee47de8714465e9493b8c96
```

El `VariantComparisonReport` de acceptance tiene la firma:

```text
42754f8500d836c9e8e901129ee7c49d65d3c2505b7d78e8369480484011e6c8
```

Estas firmas son evidencia de acceptance y reproducibilidad; no crean nuevos
goldens contractuales. La determinación lógica sí es contractual. La
determinación binaria no aplica a este slice porque no crea binarios.

### Hechos observados

| Caso | Resultado |
| --- | --- |
| A | 3 items; spatial `valid=true`. |
| B | Mismos IDs; `armchair` moved y rotated; spatial `valid=true`; `unchanged_valid`. |
| C | `sofa` resized; `armchair` removed; `floor_proxy` added; spatial `valid=false`; único error `furniture_out_of_floor`; `became_invalid`. |
| Comparación | `VariantComparisonReport.valid=true`: la comparación es válida aunque C contenga una violación espacial. |

Las limitations heredadas y persistentes en A/B/C son:

- `wall_thickness_fallback`;
- `opening_proxy_only`;
- `opening_direction_unknown`.

La acceptance ejecuta dos construcciones equivalentes, reorder de B/C,
deep-copy/no mutation y probes en memoria para cambios de `source_id` y
findings espaciales.

## Determinismo, provenance y privacidad

Los mismos inputs producen el mismo report, JSON canónico y firma lógica. El
reordenamiento de variantes y mappings semánticamente equivalentes no cambia
la salida. El comparator y la acceptance no mutan planes, layouts, reports,
wrappers, containers ni estructuras anidadas.

La provenance de acceptance es explícitamente sintética: dimensions sintéticas,
source IDs sintéticos y placement manual. No se promocionan medidas sintéticas
a medidas reales y no se inventan fabricantes, assets, timestamps, UUIDs ni
rutas.

La auditoría de los paths de Slice 005 no encontró rutas personales
(`C:\\Users\\` o `/Users/`), emails, tokens, API keys, passwords, private keys,
`hs3d_input_path` ni datos personales. No hay binarios nuevos que auditar.

## Gates ejecutados

| Gate | Evidencia |
| --- | --- |
| Variant comparison | `75/75 PASS` |
| Acceptance | `5/5 PASS` |
| Furniture pure suite | `225/225 PASS` |
| Room suite | `230/230 PASS` |
| Historical room suite | `37/37 PASS` (`test_room_v1_validation`) |
| Validators | v1, v1.1 y `living-room-main`: `VALID` |
| Generation plan | `room-v1.1-generator-2` |
| room → plan | `valid=true`, errors/warnings/info `0` |
| Golden v1 | `1105946a0dfe0088f5ad59da4178939644305b0d09b94022bfe5c87d9dde36f0` exacta |
| Python syntax | PASS |
| JSON syntax | PASS |
| `git diff --check` | PASS |

Los comandos principales son:

```text
python -m unittest tests/furniture/test_furniture_variant_comparison.py
python -m unittest tests/furniture/test_furniture_variant_acceptance.py
python -m unittest discover -s tests/furniture -p 'test_*.py'
python -m unittest discover -s tests/measurements -p 'test_*.py'
python -m unittest tests.measurements.test_room_v1_validation
python blender/scripts/measurements/validate_measurements.py measurements/fixtures/room-v1-synthetic.json
python blender/scripts/measurements/validate_measurements.py measurements/fixtures/room-v1.1-reconciliation-synthetic.json
python blender/scripts/measurements/validate_measurements.py measurements/rooms/living-room-main.json
git diff --check
```

Blender y MCP son `NO APLICA`: T5.06 solo cierra un slice pure Python y
documental, sin escenas, previews, renders, cámaras, materiales ni assets.

## Limitaciones y exclusiones

Slice 005 no implementa ranking, “best layout”, score subjetivo,
recomendaciones, ergonomía, circulación, rendering, Blender, assets reales,
materiales, colores, PBR, iluminación, cámaras, dashboard, multi-room ni
fixed elements nuevos. Los layouts de acceptance son sintéticos y manuales.

Las limitations espaciales heredadas (`wall_thickness_fallback`,
`opening_proxy_only`, `opening_direction_unknown`) permanecen visibles y no se
promocionan a errores contractuales del comparador.

## Rollback y lectura

El comparator y la acceptance tienen semántica read-only respecto a sus
inputs. El rollback de este slice consiste en revertir el commit documental o
retirar sus documentos y fixtures versionados; no requiere tocar room pipeline,
contratos T4, escenas Blender ni medidas arquitectónicas. No se realizan
operaciones destructivas ni guardados de Blender.

## Próximo límite

Slice 006 — **Visual Furnishing & Materials v1** queda como horizonte futuro,
no iniciado ni aprobado en este checkpoint. Quedan fuera de Slice 005 los
assets reales, materiales, colores, PBR, iluminación, cámaras, visual styling,
renders finales y cualquier trabajo visual equivalente.
