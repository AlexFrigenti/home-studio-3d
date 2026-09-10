# Slice 006 — Visual Furnishing & Materials v1

## Estado

Validación final de T6.06 realizada el 2026-09-10. Estados:

- T6.01 — `[x]` validada.
- T6.02 — `[x]` APPROVED.
- T6.03 — `[x]` APPROVED.
- T6.04 — `[x]` APPROVED.
- T6.05 — `[x]` VALIDATED.
- T6.06 — `[x]` validación documental y auditoría final.

Slice 006 queda preparado para revisión final. No se hizo staging, commit, push,
merge ni PR.

## Objetivo y alcance

Slice 006 materializa una capa visual procedural y reversible sobre el room
validado `living-room-main`. Añade furniture reconocible, cinco materiales
visuales y una presentación de review reproducible, preservando las autoridades
de room, measurements y furniture de Slices 001–005.

No busca fotorealismo, decoración final, catálogo ni una nueva autoridad de
medidas o placement.

## Contratos y autoridades

| Elemento | Valor |
| --- | --- |
| Room plan | `room-v1.1-generator-2` |
| Room logical signature | `182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a` |
| Layout authority | `layouts/living-room-main/variants/baseline-a.json` |
| Layout schema | `furniture-layout-1` |
| FurniturePlan | `furniture-placement-generator-1` |
| FurniturePlan signature | `b107d146c81a300858d33d48265d7e42480c88f6ed8443e6a54f80a008e19a0c` |
| Spatial report | `furniture-spatial-validation-1` |
| Visual contract | `visual-scene-contract-1` |
| Visual provenance | `procedural_synthetic` |
| Units / coordinates | `m` / `canonical_room` |

## Source y escena derivada

- Source arquitectónico: `blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend`.
- Escena derivada autoritativa: `blender/scenes/review/2026-09-10-living-room-main-slice-006-visual-v1.blend`.
- Source SHA-256 verificado antes y al finalizar:
  `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.
- El source no se abrió como escena de trabajo, no se guardó y no se sobrescribió.
- Toda la capa visual vive en la derivada, bajo el root hermano
  `HSLAYOUT_VISUAL_living-room-main_slice-005-acceptance-baseline-a_v1`.

## Arquitectura preservada

La escena derivada conserva:

- 22 objetos `HS3D_WALL_wall-*` en `Architecture`;
- 6 opening proxies en `Openings`;
- `HS3D_FLOOR` con `8.03 × 5.35 m`;
- 0 objetos en `FixedElements`;
- jerarquía `HS3D_ROOM_living-room-main` → `Architecture`, `FixedElements`,
  `Openings` y `Validation`;
- `HS3D_CAMERA`, `HS3D_KEY_LIGHT` y los materiales técnicos
  `HS3D_MAT_DOOR_PROXY`, `HS3D_MAT_FLOOR`, `HS3D_MAT_WALL` y
  `HS3D_MAT_WINDOW_PROXY`.

## Furniture visual

Los tres items de baseline A permanecen vinculados al FurniturePlan:

| Item | Position | Yaw | Dimensions |
| --- | --- | --- | --- |
| `sofa` | `[-3.1, 1.2, 0]` | `0°` | `2.2 × 0.95 × 0.85 m` |
| `armchair` | `[-1.0, 1.2, 0]` | `270°` | `0.8 × 0.8 × 0.9 m` |
| `coffee_table` | `[-3.1, 0.2, 0]` | `90°` | `1.0 × 0.6 × 0.4 m` |

Cada item tiene root determinista `HSLAYOUT_VISUAL_*`, ownership exclusivo de
`FurnitureVisual`, jerarquía root/children, `anchor=bottom_center`, footprint,
metadata de item, source ID, provenance y binding de versión/firma.
La geometría es procedural y reconocible; no se incorporaron assets externos.

## Materiales visuales

Existen exactamente estos cinco material IDs:

- `hs3d_visual_mat_sofa_v1`: base `[0.42,0.30,0.22,1]`, roughness `0.82`, metallic `0.0`.
- `hs3d_visual_mat_sofa_cushion_v1`: base `[0.58,0.43,0.30,1]`, roughness `0.86`, metallic `0.0`.
- `hs3d_visual_mat_armchair_v1`: base `[0.12,0.30,0.34,1]`, roughness `0.80`, metallic `0.0`.
- `hs3d_visual_mat_armchair_cushion_v1`: base `[0.20,0.45,0.46,1]`, roughness `0.84`, metallic `0.0`.
- `hs3d_visual_mat_coffee_table_wood_v1`: base `[0.34,0.14,0.045,1]`, roughness `0.48`, metallic `0.0`.

Todos usan namespace visual, semantic role, `materials-v1`, owner de review,
`procedural_synthetic`, nodos Principled BSDF + Material Output y no contienen
imágenes ni nodos `TEX_IMAGE`. Hay 19 assignments deterministas y ningún
datablock `.001`/`.002`.

## ReviewPresentation y render

`ReviewPresentation` contiene exclusivamente:

- cámara `..._REVIEW_CAMERA_v1`: location `[-5.8,-1.0,1.7]`, target
  `[-2.4,1.1,0.6]`, focal `35 mm`, sensor `36 mm`, clipping `0.1–100 m`, DOF off;
- key `..._REVIEW_KEY_AREA_v1`: `900 W`, size `4.0 m`, color `[1.0,0.91,0.82]`;
- fill `..._REVIEW_FILL_AREA_v1`: `250 W`, size `3.0 m`, color `[0.82,0.90,1.0]`.

Los tres objetos tienen ownership, namespace, metadata, unidades y provenance
correctos. El world usa strength `0.32`. El render usa `BLENDER_EEVEE`,
`960 × 720`, 100 % y transparencia desactivada.

Render versionado:

`renders/previews/living-room-main-slice-006-visual-v1/review-v1.png`

Es un PNG legible de `862587` bytes. Su SHA puntual es
`05481687AC98123F571681530AAB7AF4CF76C9DD88485CD1EE7647BC19306594`; este hash
no es golden contractual y no se exige igualdad binaria futura.

La auditoría final reprodujo en el artefacto previo de `863031` bytes (SHA
`A81BD18990A43AF1ABB5B528A5DCEF3A61D543C9F665EAA4063F8F569A66A0BA`) chunks
`eXIf` y `tEXt`, incluyendo una ruta absoluta y campos de render no
contractuales. Se aplicó sanitización binaria determinista al PNG existente,
sin rerenderizar: se eliminaron `eXIf`, `tEXt`, `iTXt` y `zTXt`, preservando los
chunks permitidos y `IDAT` sin recomprimir. Los chunks finales son
`IHDR`, `sRGB`, `gAMA`, `cHRM`, `oFFs`, `pHYs` e `IEND`, además de `IDAT`.

El hash de píxeles antes/después es idéntico:
`ed9ca1260baa9b96896ad71fdb048914f318f0a49d9e83b012e4d5ea966bfab6`. El hash
del payload concatenado de `IDAT` antes/después también es idéntico:
`d0d44dee1c9aa171022f0252c32dbd2e690215ee6b999efd87e4b98a35558d20`. El SHA
del PNG se conserva como evidencia puntual, no como golden.

El guard reutilizable `validate_review_render_bytes` /
`sanitize_review_render_file` vive en
`blender/scripts/furniture/generate_furniture_visual.py` y comprueba PNG,
dimensiones, CRC, chunks prohibidos y marcadores de rutas locales. La cobertura
está en `tests/furniture/test_furniture_visual_contract.py`: RED reproducido con
el artefacto previo y GREEN tras la sanitización.

## Workflow Blender/MCP

La evidencia visual se obtuvo en Blender GUI real 5.2.1 LTS, con
`bpy.app.background=false`, `VIEW_3D` disponible, escena derivada activa y MCP
local en `127.0.0.1:9876`. Funcionaron `get_scene_info`, `execute_blender_code` y
`get_viewport_screenshot`. La escena queda abierta al finalizar.

No se usó Blender background/headless como sustituto de la inspección gráfica y
no se generó un nuevo render durante T6.06.

## Determinismo lógico e idempotencia

El inventario normalizado incluye collections, object names/types, ownership,
jerarquía, transforms contractuales, dimensiones, metadata, materiales,
assignments, parámetros de cámara y luces, world y render.

Dos lecturas independientes fueron idénticas: 8 collections, 56 objetos, 9
materiales, `canonical_length=85096` y fingerprint interno `315456719271`.
Este fingerprint solo evidencia la comparación del inventario; no es golden del
`.blend`.

La reconstrucción lógica desde source, baseline A, FurniturePlan y contratos
visuales es determinista. La comprobación read-only no encontró collections,
objetos, materiales, assignments, cámaras, luces ni geometría residual
duplicados; no se destruyó ni regeneró la escena aprobada.

## Aceptación humana

Los STOP VISUAL quedan registrados como evidencia humana explícita:

- T6.02 — Furniture geometry / recognition: **APPROVED**.
- T6.03 — Materials v1: **APPROVED**.
- T6.04 — Lighting + review camera + review render: **APPROVED**.
- T6.05 — Visual acceptance & reproducibility: **VALIDATED**.

La aprobación de T6.04 confirma cámara interior útil, sofá, armchair y coffee
table completos y reconocibles, arquitectura contextual, iluminación legible y
ausencia de clipping funcional invalidante.

Se aceptan como no bloqueantes: sofá próximo al borde izquierdo, apariencia
técnica/simple, iluminación clara, geometría procedural simple y ausencia de
fotorealismo o decoración final. No se convierten en bugs ni trabajo adicional.

## Gates finales

| Gate | Resultado |
| --- | --- |
| Visual contract | `8/8 PASS` |
| Variant comparison | `75/75 PASS` |
| Slice 005 acceptance | `5/5 PASS` |
| Furniture full | `233/233 PASS` |
| Room baseline | `230/230 PASS` |
| Historical room | `37/37 PASS` |
| Measurement/layout validators | `VALID` |
| `build_generation_plan` | `PASS` |
| `compare_room_to_plan` | `valid=true`, 0 discrepancies/warnings |
| Furniture spatial validation | `valid=true`, 0 errors/warnings |
| Golden v1 | exacta `1105946a0dfe0088f5ad59da4178939644305b0d09b94022bfe5c87d9dde36f0` |
| Python syntax | `32/32 PASS` |
| JSON syntax | `11/11 PASS` |
| `git diff --check` | `PASS` |

Los validadores de mediciones para `living-room-main`, fixture room-v1 y
fixture room-v1.1 devolvieron `VALID`. Los inputs room y layout permanecieron
sin mutación durante la reconstrucción pura.

## Provenance, privacidad y hygiene

- Provenance visual y material: `procedural_synthetic`.
- No hay fotografías, EXIF, LiDAR, assets comerciales, fabricantes ni texturas
  externas.
- No se introdujeron secretos, tokens, passwords, API keys, emails, usernames,
  UUIDs accidentales ni rutas privadas en archivos versionables.
- No hay caches tracked, temporales, `.blend1` nuevos ni renders fuera de la
  ruta autorizada de Slice 006.
- Los artefactos históricos existentes fuera de Slice 006 no fueron modificados.

## Anomalías y limitaciones aceptadas

- `get_addon_status` devuelve `No module named 'blender_mcp.config'`. No bloqueó
  las operaciones MCP reales, que funcionaron mediante la sesión GUI.
- La API de Blender 5.2.1 expone `BLENDER_EEVEE` y no
  `BLENDER_EEVEE_NEXT`. Es una diferencia de nomenclatura/API, no un fallo
  visual ni una razón para cambiar la escena.
- La presentación sigue siendo deliberadamente técnica/simple: cuboids
  procedurales, materiales simples, iluminación clara, sin decoración, texturas
  externas ni fotorealismo.
- La cámara deja el sofá relativamente próximo al borde izquierdo, pero fue
  aprobada y no existe clipping funcional.
- Persisten las limitaciones heredadas: opening proxies, dirección de openings
  `unknown`, espesores de pared con fallback explícito, layouts manuales y
  ausencia de rollback transaccional del guardado.

## Rollback, regeneración y fuera de alcance

La regeneración futura debe partir de `measurements/`, baseline A, FurniturePlan
y contratos versionados, siempre sobre una copia derivada. El source es
read-only; no se debe sobrescribir ni usar una escena aprobada como laboratorio
destructivo. La recuperación de esta entrega consiste en conservar o eliminar
la copia derivada y el preview como unidad de Slice 006, sin alterar las
autoridades de Slices 001–005.

Quedan fuera de alcance: cambios al room pipeline o schemas existentes,
measurements, funcionalidad de Slice 005, assets comerciales, manufacturers,
texturas externas, decoración fina, ergonomía/circulación, ranking,
comparación visual A/B/C, UI, VR/AR, animación y Slice 007.

## Estado final

T6.06 queda documentada y validada. La escena derivada permanece como artefacto
autoritativo de Slice 006, Blender queda abierto y la rama permanece sin
staging, commit, push, merge ni PR.
