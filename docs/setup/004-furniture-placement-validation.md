# Furniture Placement v1 — T4.06 acceptance

Esta acceptance cierra Slice 004 sobre `living-room-main` usando únicamente
proxies sintéticos. `measurements/` continúa siendo la autoridad arquitectónica;
el layout vive en `layouts/` y el `.blend` fuente se abre como read-only.

## Contratos y entradas

| Elemento | Valor |
| --- | --- |
| Room | `living-room-main` |
| Room plan | `room-v1.1-generator-2` |
| Room logical signature | `182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a` |
| Layout schema | `furniture-layout-1` |
| Furniture plan | `furniture-placement-generator-1` |
| Scene adapter | `furniture-scene-adapter-1` |
| Comparison report | `furniture-scene-comparison-1` |
| Layout | `layouts/living-room-main/slice-004-acceptance-v1.json` |
| Dimensions | `synthetic` |
| Provenance | `slice-004-acceptance-sofa`, `slice-004-acceptance-coffee-table`, `slice-004-acceptance-armchair` |

Items: `sofa`, `coffee_table`, `armchair`. Sus dimensiones son proxies de
acceptance y no representan muebles medidos, de fabricante ni pertenecientes a
la vivienda.

## Fuente y artefactos

Fuente arquitectónica preservada:

`blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend`

- SHA-256 antes: `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`
- SHA-256 después: `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`

Artefactos derivados versionados:

| Artefacto | Tamaño | SHA-256 |
| --- | ---: | --- |
| `blender/scenes/review/2026-09-09-living-room-main-slice-004-acceptance-v1-furniture-v1.blend` | 120104 bytes | `7A0F5683D11C5203A9A01D8243C3173FE53022217AC7C00F36FB2DE9A18D422F` |
| `renders/previews/2026-09-09-living-room-main-slice-004-acceptance-v1-furniture-v1/qa-top-orthographic.png` | 349236 bytes | `0184EBD44140BB91178FB38E11B800C09B671B4366D95C0D50C4DE26AEA6F773` |

El `.blend` derivado contiene el root
`HSLAYOUT_living-room-main_slice-004-acceptance-v1`, la colección física
`HSLAYOUT_living-room-main_slice-004-acceptance-v1_Furniture` y tres proxies:

- `HSLAYOUT_FURNITURE_living-room-main_slice-004-acceptance-v1_armchair`
- `HSLAYOUT_FURNITURE_living-room-main_slice-004-acceptance-v1_coffee_table`
- `HSLAYOUT_FURNITURE_living-room-main_slice-004-acceptance-v1_sofa`

El `item_id` semántico permanece separado del nombre físico cualificado.

## Procedimiento reproducible

Blender usado: `5.2.1 LTS`, background CLI, sin MCP. Runner:
`tests/furniture/blender_test_furniture_t406_acceptance.py`.

```powershell
$blender = '<BLENDER_5.2.1>\blender.exe'
& $blender --background --offline-mode --python tests/furniture/blender_test_furniture_t406_acceptance.py -- `
  blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend `
  layouts/living-room-main/slice-004-acceptance-v1.json `
  blender/scenes/review/2026-09-09-living-room-main-slice-004-acceptance-v1-furniture-v1.blend `
  renders/previews/2026-09-09-living-room-main-slice-004-acceptance-v1-furniture-v1/qa-top-orthographic.png
```

El runner ejecuta, en orden, layout validation, generation plan, FurniturePlan,
spatial validation, room comparison before/after, overlay, normalización,
comparison report, anti-false-pass sobre copias profundas, preview técnico y
guardado únicamente de la salida derivada. Reabre el source para una segunda
ejecución lógica y reabre el `.blend` derivado para verificar el archivo real.

Resultados:

- layout: `valid=true`, tres items;
- FurniturePlan signature: `66db6b5248b7cc54b3d610609be76766b77a6a08d0bbce81807894e4b0d597fa`;
- spatial validation: `valid=true`, `errors=0`, `warnings=0`;
- limitations: `wall_thickness_fallback`, `opening_proxy_only`,
  `opening_direction_unknown` agregadas sin invalidar;
- normalized furniture: adapter válido, tres entidades;
- comparison: `valid=true`, `errors=0`, `warnings=0`;
- comparison report hash: `F4AFE2ABBD1DE2FCF9A90F5AB5DEE05398F740263A698A4513F3E899A4F01157`;
- normalized scene hash: `2F7379DC4E8E47CF90E05066033B495419E0DEAF42FD7A1EDC124BED2C269646`;
- room comparison before/after: `valid=true`;
- architecture projection before/after: igual;
- architecture projection hash: `BBC65003DB717D8E1BC463DCAF3F016605029AE9DAD36243B8FA2369A7FCB3C7`;
- logical determinism: PASS en dos ejecuciones contra el mismo source;
- binary determinism: no es contrato de v1 y no se usa como criterio;
- anti-false-pass: PASS para nombre físico, traslación, vértice, escala, yaw,
  source_id, dimensiones y firma de plan;
- no-mutación del layout, room plan y FurniturePlan: PASS.

El preview top-orthographic es técnico: los proxies son cuboides lisos,
sin assets, texturas ni materiales artísticos. La inspección confirma que los
tres proxies son visibles y que el encuadre no los presenta como modelos
reales.
El PNG se sanitiza eliminando los chunks textuales no contractuales, incluida
la ruta local escrita por Blender en `tEXt/File`; la equivalencia pixel a pixel
se conserva y la auditoría binaria de privacidad pasa.

## Gates y baseline

- Furniture pure: `145/145 PASS`.
- Blender T4.04: `4/4 PASS`.
- Blender T4.05: `6/6 PASS`.
- T4.06 acceptance: PASS.
- Room comparison: `137/137 PASS`.
- Room normalize: `22/22 PASS`.
- Room generation: `34/34 PASS`.
- Measurements suite: `230/230 PASS`.
- Historical suite: `37/37 PASS`.
- Validators v1, v1.1 y real: `VALID`.
- `build_generation_plan(living-room-main)`: PASS.
- `compare_room_to_plan(living-room-main)`: `valid=true`, `errors=0`.
- Golden v1 del fixture histórico: `1105946a0dfe0088f5ad59da4178939644305b0d09b94022bfe5c87d9dde36f0`.
- Python y JSON syntax: PASS.
- `git diff --check`: PASS.

## Privacidad, provenance y limitaciones

La acceptance no añade fotos, EXIF, LiDAR, fotogrametría, secretos, tokens,
credenciales, rutas personales ni assets externos. `source_id` es provenance
sintética estable; Blender solo materializa la provenance disponible en el
FurniturePlan y no se inventan fabricantes, medidas reales ni ownership del
usuario.

Se mantienen explícitamente estas limitaciones: proxies sintéticos, sin assets
reales, sin materiales artísticos, sin ergonomía/circulación, sin door swing,
openings proxy-only, `opening_direction=unknown`, espesores wall fallback,
`fixed_elements=[]` sin obstáculos inferidos, provenance Blender parcial y
rollback de guardado no transaccional.

## Reversión

Para revertir T4.06 se eliminan únicamente el layout de acceptance, el `.blend`
derivado, el preview, este documento y la evidencia documental de cierre. Se
preserva la fuente arquitectónica generator-2 y todo el room pipeline. El
`.blend1` histórico `blender/scenes/tests/001-foundation-room.blend1` es
preexistente, ignored y no forma parte de esta acceptance.
