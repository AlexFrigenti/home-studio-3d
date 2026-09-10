# Especificación: Visual Furnishing & Materials v1

> Clasificación: T2
> Rama: `spec/006-visual-furnishing-materials-v1`
> Estado: T6.01–T6.05 validadas; T6.06 validada; Slice 006 preparado para revisión final.

## Objetivo

Convertir una distribución válida de `living-room-main` en una primera escena
visualmente evaluable dentro de Blender, preservando la arquitectura, las
medidas y los contratos de Slices 001–005. La escena debe sentirse como una
habitación amueblada, aunque todavía no sea fotorealista.

El slice introduce una representación visual reconocible de los muebles,
materiales simples, iluminación de revisión y una cámara reproducible. Las
tareas visuales se desarrollarán en Blender 5.2.1 LTS abierto en modo gráfico,
con Blender MCP local y Codex observando la sesión.

## Baseline heredada

- Room: `living-room-main`.
- Room plan soportado: `room-v1.1-generator-2`.
- Room logical signature: `182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a`.
- Layout authority: `layouts/living-room-main/variants/baseline-a.json`.
- Layout contract: `furniture-layout-1`.
- FurniturePlan: `furniture-placement-generator-1`.
- FurniturePlan baseline A signature: `b107d146c81a300858d33d48265d7e42480c88f6ed8443e6a54f80a008e19a0c`.
- Spatial report: `furniture-spatial-validation-1`, válido para A.
- Units: `m`.
- Coordinate system: `canonical_room`.
- Architecture source: `blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend`.
- Architecture source SHA-256 registrada: `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.

La aceptación de Slice 005 sigue siendo la evidencia contractual de las
entradas. Los hashes anteriores son evidencia existente, no nuevos goldens de
Slice 006.

## Problema

Slice 004 materializa muebles como cuboides sintéticos y el preview existente
es técnico. Slice 005 compara layouts y hechos espaciales, pero no permite
evaluar visualmente forma, material, volumen, iluminación ni encuadre. El
riesgo principal de este slice es que una iteración artística desplace,
redimensione o sobrescriba silenciosamente la representación contractual.

## Principio visual-first

Los tests protegen la infraestructura y los contratos. La inspección visual
valida el producto visual. Ninguna tarea cuyo criterio sea principalmente
visual se cierra solo porque un script, test o ejecución en background termine
sin errores.

Cada fase visual requiere una sesión gráfica real de Blender 5.2.1 LTS,
inspección directa del viewport y, cuando el criterio lo indique, un render de
revisión. Codex debe detenerse en cada STOP VISUAL y esperar feedback humano;
no puede decidir por sí solo que el resultado artístico es correcto.

## Alcance

### Incluye

- Contrato de escena visual derivada y ownership explícito.
- Flujo autoritativo `Codex → Blender MCP local → Blender GUI → inspección → ajuste → aceptación`.
- Primera representación procedural/simple y reconocible de sofá, sillón y mesa.
- Materiales procedurales simples, reproducibles y diferenciables.
- Iluminación de revisión y una cámara de revisión reproducible.
- Acceptance visual de `living-room-main` usando baseline A.
- Preservación de `FurniturePlan`, placement, footprint, dimensiones contractuales y provenance sintética.
- Evidencia de viewport/render, estructura de escena, privacidad y rollback.

### Fuera de alcance

- Fotorealismo final o fotografía arquitectónica.
- Catálogo completo, fabricantes, marcas o modelos comerciales.
- Descarga masiva, scraping o incorporación de assets externos sin licencia.
- Texturas externas, PBR avanzado o materiales dependientes de servicios remotos.
- Decoración fina, plantas, cuadros o accesorios no necesarios para la aceptación.
- Ergonomía avanzada, circulación, ranking u optimización automática de layouts.
- Comparación visual A/B/C; Slice 006 usa baseline A únicamente.
- UI, aplicación interactiva, VR/AR, animation o render farm.
- Cambios en `measurements/`, schemas, room pipeline o contratos T4/T5.
- Slice 007.

## Autoridad y contratos

La autoridad semántica permanece en esta dirección:

```text
measurements/
  → room-v1.1-generator-2
  → arquitectura HS3D_ROOM_*
baseline-a.json
  → FurniturePlan
  → spatial validation
  → representación visual derivada
```

La visualización puede añadir detalle local, pero no puede convertirse en una
segunda fuente de verdad para posición, yaw, dimensiones, footprint o
validación espacial. Todo objeto visual debe conservar metadata que permita
volver a `room_id`, `layout_id`, `item_id`, `source_id`, `dimensions_status`,
`furniture_plan_version`, `room_plan_version` y las firmas disponibles.

`dimensions_status=synthetic` permanece `synthetic`; una forma visual más
reconocible no transforma un proxy en un mueble medido.

## Contrato de escena visual derivada

El contrato propuesto es aditivo y no modifica los normalizers T4:

- El root arquitectónico existente `HS3D_ROOM_<room_id>` permanece intacto.
- Sus colecciones `Architecture`, `Openings`, `FixedElements` y `Validation`
  siguen siendo propiedad del room pipeline.
- El root semántico existente `HSLAYOUT_<room_id>_<layout_id>` y su colección
  `Furniture` siguen representando el overlay contractual de Slice 004.
- La capa visual nueva vive como root hermano:
  `HSLAYOUT_VISUAL_<room_id>_<layout_id>_v1`.
- La capa visual tendrá, como mínimo, las colecciones `FurnitureVisual` y
  `ReviewPresentation`; las colecciones existentes no se reutilizan para
  ocultar ownership.
- Los objetos visuales usarán nombres deterministas como
  `HSLAYOUT_VISUAL_<room_id>_<layout_id>_<item_id>` y metadata `hs3d_visual_*`.
- Cada objeto visual tendrá un `item_id` semántico y un `source_id` sintético,
  aunque su geometría interna tenga varios componentes.
- Los proxies contractuales se conservan como capa de referencia y no se
  sobrescriben. Si se ocultan del render derivado, la decisión queda
  documentada y no afecta al source.

No se permite añadir un root visual dentro de `HS3D_ROOM_*` ni dentro del root
semántico `HSLAYOUT_*` si eso rompe los normalizers existentes. La capa visual
debe poder eliminarse o regenerarse sin tocar arquitectura ni FurniturePlan.

## Estrategia de assets

Slice 006 v1 usará geometría procedural/simple creada en el propio proyecto.
No se descargan assets en esta ejecución ni se introducen modelos de
fabricantes reales por defecto. Los muebles se reconocen por silueta y
componentes mínimos:

- sofá: base, asiento, respaldo y brazos;
- sillón: base, asiento, respaldo y brazos más compactos;
- mesa: tablero y soportes/patas.

Las formas son representaciones visuales sintéticas. Si una fase posterior
introduce un asset externo, deberá abrir un cambio de alcance con procedencia,
licencia, dimensiones, `source_id` y decisión de versionado explícitas.

## Contrato mínimo de materiales

Cada material visual tendrá:

- `material_id` estable;
- `semantic_role` (`wall`, `floor`, `sofa`, `armchair`, `coffee_table` u otro
  item realmente presente);
- `base_color` RGBA determinista;
- `roughness` determinista;
- `metallic` determinista;
- `provenance=procedural_synthetic`;
- referencia a la versión de Slice 006 y al rol visual, no a una ruta local.

La primera paleta será deliberadamente simple: paredes neutras cálidas, suelo
contrastado, tapicería diferenciable para sofá/sillón y mesa con acabado
mate o ligeramente reflectante. `metallic` solo será distinto de cero si el
material representa realmente una superficie metálica; no se añadirá un
sistema universal de shaders.

La asignación material→rol será determinista y no dependerá del orden de
creación de datablocks. No se usan texturas externas en v1.

## Flujo Blender GUI + MCP

La sesión gráfica abierta de Blender es la autoridad durante la iteración:

1. Codex prepara y revisa el input contractual y la acción acotada.
2. Blender 5.2.1 LTS permanece abierto en modo gráfico.
3. Blender MCP se conecta únicamente a `127.0.0.1:9876`.
4. Codex envía a MCP operaciones inspeccionadas y acotadas.
5. El usuario observa el viewport y Codex inspecciona la escena mediante GUI,
   viewport y datos numéricos cuando corresponda.
6. Se guarda únicamente una escena derivada, nunca el source arquitectónico.
7. Se captura evidencia y se alcanza el STOP VISUAL.
8. Codex devuelve el estado y espera feedback humano antes de la siguiente
   fase visual.

Blender background sigue permitido para tests, validación estructural,
reproducción controlada y comprobaciones automatizadas. No es el workflow
principal de las tareas artísticas y no sustituye la inspección visual.

No se ejecutará código externo no inspeccionado, no se expondrá MCP a la red,
no se instalarán addons/dependencias y no se lanzarán procesos desde Blender.

## Source, derived y rollback

El source arquitectónico de referencia se abre read-only y se conserva en su
ruta existente. La visualización se guarda mediante `Save As` a una ruta
derivada prevista, por ejemplo:

```text
blender/scenes/review/living-room-main-slice-006-visual-v1.blend
renders/previews/living-room-main-slice-006-visual-v1/review.png
```

Esas rutas son salidas futuras, no archivos creados en esta tarea. La escena
derivada puede descartarse y regenerarse desde el source, el layout A y el
FurniturePlan. Antes de operaciones destructivas se guarda un checkpoint
derivado; nunca se usa `--force`, se sobrescribe el source ni se destruyen
colecciones en masa sin inspección. El rollback normal es volver al último
checkpoint derivado o regenerar desde source + contratos.

## Determinismo

### Logical determinism

Debe ser reproducible:

- root y colecciones;
- nombres y ownership de objetos;
- transforms contractuales;
- `item_id`, `source_id` y metadata;
- `material_id` y asignaciones por rol;
- parámetros de cámara y luces;
- inventario normalizado y firmas lógicas disponibles.

La creación visual no puede depender de timestamps, UUIDs, rutas locales o
orden incidental de selección en Blender.

### Binary/render determinism

No se promete igualdad binaria de `.blend` ni igualdad byte a byte de PNG. Un
hash binario podrá registrarse como evidencia puntual de una entrega, pero no
será un golden contractual salvo que una tarea futura lo justifique y lo
demuestre en la misma infraestructura.

## Criterios de aceptación

- [x] T6.01 fija el contrato de escena, ownership, provenance, rollback y
  workflow GUI+MCP sin modificar T4/T5.
- [x] T6.02 produce en una sesión gráfica una habitación donde sofá, sillón y
  mesa sean visualmente reconocibles, manteniendo el placement de baseline A y
  alcanzando un STOP VISUAL con evidencia de viewport.
- [x] T6.03 asigna materiales procedurales simples y diferenciables a paredes,
  suelo y muebles, con `material_id`, roughness, metallic y provenance
  deterministas; alcanza un STOP VISUAL.
- [x] T6.04 proporciona iluminación y cámara de revisión reproducibles,
  muestra arquitectura y muebles sin clipping ni oscuridad obstructiva, genera
  un review render ligero y alcanza un STOP VISUAL.
- [x] T6.05 demuestra que source, measurements, layout, FurniturePlan y
  contracts no mutaron; normaliza/inspecciona la escena derivada; registra
  evidencia estructural, de privacidad y visual; alcanza aceptación humana.
- [x] T6.06 actualiza documentación y gates sin añadir nueva funcionalidad,
  deja el diff dentro de alcance y prepara la rama para PR.

### Criterios visuales no sustituibles por tests

La aceptación visual debe confirmar explícitamente: habitación reconocible,
arquitectura intacta, muebles reconocibles y correctamente situados,
materiales distinguibles, iluminación suficiente, cámara útil, ausencia de
geometría rota u objetos accidentales y ausencia de overlays/debug no
intencionados en el render.

## Riesgos e invariantes

- Riesgo: modificar el source `.blend` al iterar. Mitigación: read-only,
  `Save As`, rutas derivadas y comprobación de hash antes/después.
- Riesgo: desplazar muebles para mejorar la composición. Mitigación: el
  FurniturePlan gobierna transforms y se comparan numéricamente antes de cada
  checkpoint.
- Riesgo: confundir proxies sintéticos con assets reales. Mitigación:
  provenance `procedural_synthetic`, `dimensions_status=synthetic` y nombres
  visuales explícitos.
- Riesgo: materiales o luces frágiles por contexto de Blender. Mitigación:
  sesión gráfica controlada, operaciones pequeñas, checkpoint después de cada
  fase y revisión visual humana.
- Riesgo: scope creep hacia catálogo o fotorealismo. Mitigación: no assets
  externos, paleta mínima, EEVEE de revisión y exclusiones cerradas.
- Riesgo: privacidad por rutas o metadata Blender. Mitigación: paths
  repo-relative, sanitización de previews y auditoría de custom properties.

Invariantes: `measurements/` es autoridad; unidades `m`; coordinate system
`canonical_room`; root `HS3D_ROOM_*` intacto; overlay semántico separado del
visual; source no sobrescrito; no se inventa provenance; no se interpreta el
render como validación geométrica.

## Evidencia visual

- Requerida: sí.
- T6.02: captura del viewport gráfico con arquitectura y los tres muebles.
- T6.03: captura del viewport mostrando la separación de materiales.
- T6.04: review render ligero y captura de cámara/viewport.
- T6.05: evidencia final visual más inventario/normalización/hash lógico.
- Cada evidencia debe indicar qué se observa y qué limitación permanece.

## Checkpoint real T6.01 — 2026-09-10

- Blender 5.2.1 LTS quedó abierto en la sesión gráfica autoritativa mediante
  MCP local. La lectura confirmó `bpy.app.background=false`, una ventana
  `Layout` con `VIEW_3D`, y la ruta activa derivada después de `Save As`.
- Source observado antes de escribir:
  `blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend`.
  SHA-256 antes y después:
  `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.
- Derived checkpoint creado mediante Blender GUI/MCP:
  `blender/scenes/review/2026-09-10-living-room-main-slice-006-visual-v1.blend`.
  SHA-256 puntual, no golden contractual:
  `14AD33F882A815DFD7882FE273060ECB2F29B3AF7D03BE3BF679C7B0C10FE17F`.
- La derivada contiene el root hermano
  `HSLAYOUT_VISUAL_living-room-main_slice-005-acceptance-baseline-a_v1`,
  `FurnitureVisual` y `ReviewPresentation`, todos sin objetos. El root
  registra `hs3d_visual_*`, `room-v1.1-generator-2`, la firma de room
  `182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a`, la
  firma FurniturePlan A `b107d146c81a300858d33d48265d7e42480c88f6ed8443e6a54f80a008e19a0c`,
  unidades `m` y `canonical_room`.
- La inspección derivada confirmó 22 paredes, 6 openings proxy, floor
  `8.03 x 5.35 m`, transforms arquitectónicos sin incidencias,
  `HS3D_CAMERA`, `HS3D_KEY_LIGHT` y los cuatro materiales técnicos
  `HS3D_MAT_*` intactos; el inventario mantiene 31 objetos.
- No se crearon muebles visuales, materiales artísticos, luces de review,
  cámara de review, decoración ni renders. T6.02+ permanecen fuera de este
  checkpoint.
- El endpoint diagnóstico `get_addon_status` devolvió
  `No module named 'blender_mcp.config'`; las operaciones de escena,
  viewport, lectura y `Save As` sí se ejecutaron contra la GUI real mediante
  MCP local. Se conserva como anomalía de infraestructura, no como éxito
  simulado del endpoint.

## Checkpoint real T6.02 — 2026-09-10 — IMPLEMENTED / APPROVED VISUALLY

- Blender 5.2.1 LTS permaneció abierto en la sesión gráfica autoritativa mediante MCP local,
  con `bpy.app.background=false`, sobre la derivada
  `blender/scenes/review/2026-09-10-living-room-main-slice-006-visual-v1.blend`.
- La autoridad usada fue `baseline-a.json` con FurniturePlan
  `furniture-placement-generator-1`, firma
  `b107d146c81a300858d33d48265d7e42480c88f6ed8443e6a54f80a008e19a0c`,
  sin modificar layout ni FurniturePlan.
- Se crearon exactamente 22 objetos visuales procedurales, todos en
  `FurnitureVisual`: 3 roots EMPTY y 19 piezas MESH. El sofá tiene 7 piezas,
  el sillón 6 y la mesa de centro 6. `ReviewPresentation` permanece vacío.
- Los roots conservan los transforms contractuales: sofá `[-3.1, 1.2, 0]`,
  yaw `0°`, envelope `[2.2, 0.95, 0.85]`; sillón `[-1.0, 1.2, 0]`,
  yaw `270°`, envelope `[0.8, 0.8, 0.9]`; mesa `[-3.1, 0.2, 0]`,
  yaw `90°`, envelope `[1.0, 0.6, 0.4]`. Las bounds locales verificadas
  quedaron dentro de cada envelope contractual.
- Cada root y pieza materializa metadata `hs3d_visual_*` con room/layout/item,
  tipo, FurniturePlan version y firma, `dimensions_status=synthetic`,
  provenance `procedural_synthetic`, unidades `m` y `canonical_room`.
- La regeneración controlada en dos ciclos canónicos produjo inventarios
  lógicamente equivalentes: 22 objetos, ownership íntegro en `FurnitureVisual`,
  sin nombres `.001/.002` ni geometría residual.
- La inspección final confirmó 22 walls, 6 openings, floor `8.03 x 5.35 m`,
  `HS3D_CAMERA`, `HS3D_KEY_LIGHT` y los cuatro materiales técnicos intactos.
  No se asignaron materiales visuales, ni se crearon cámara/lights de review,
  decoración o renders. No existía overlay semántico `HSLAYOUT_*` antes ni después.
- El checkpoint se inspeccionó inicialmente en modo Solid y vista superior; después
  se cambió la navegación a perspectiva 3D elevada y diagonal. El usuario aprobó
  visualmente sofá, sillón, mesa, proporciones, placement, arquitectura y ausencia
  de geometría rota; T6.02 queda validada `[x]`.
- Source SHA-256 antes/después: `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.
  SHA-256 puntual de la derivada guardada: `A65F9888D71CCBE2F5908FFB4D21A697F8868C82A6084F32A35BCCFE025B5F66`.

## Checkpoint real T6.03 — 2026-09-10 — IMPLEMENTED / APPROVED VISUALLY

- Blender 5.2.1 LTS permaneció abierto mediante MCP local sobre la derivada,
  con `bpy.app.background=false`, viewport `PERSP` en `Material Preview`,
  arquitectura contextual y cero objetos seleccionados.
- Se crearon cinco materiales propios bajo namespace `HSLAYOUT_VISUAL_*`, todos
  con nodos únicamente `Principled BSDF` y `Material Output`, sin texturas ni
  imágenes externas: sofa, sofa cushion, armchair, armchair cushion y coffee
  table wood.
- IDs y parámetros usados: sofa `hs3d_visual_mat_sofa_v1`, color `[0.42,0.30,0.22,1]`,
  roughness `0.82`, metallic `0.0`; sofa cushion `hs3d_visual_mat_sofa_cushion_v1`,
  `[0.58,0.43,0.30,1]`, `0.86`, `0.0`; armchair `hs3d_visual_mat_armchair_v1`,
  `[0.12,0.30,0.34,1]`, `0.80`, `0.0`; armchair cushion
  `hs3d_visual_mat_armchair_cushion_v1`, `[0.20,0.45,0.46,1]`, `0.84`, `0.0`;
  coffee table wood `hs3d_visual_mat_coffee_table_wood_v1`, `[0.34,0.14,0.045,1]`,
  `0.48`, `0.0`.
- Se verificaron 19 assignments: estructura de sofá y sillón con sus variantes
  de cojín, y todas las piezas de coffee table con madera. Cada material y cada
  assignment registra `material_id`, `semantic_role`, `materials-v1`, scene
  version, `provenance=procedural_synthetic`, base color, roughness y metallic.
- La segunda aplicación determinista produjo el mismo inventario, sin materiales
  `.001/.002`. Los cuatro materiales técnicos `HS3D_MAT_*` de arquitectura no
  fueron modificados; no se creó lighting/cámara de review ni contenido en
  `ReviewPresentation`.
- Los transforms contractuales siguen intactos: sofa `[-3.1,1.2]`/`0°`, armchair
  `[-1.0,1.2]`/`270°`, coffee table `[-3.1,0.2]`/`90°`; arquitectura: 22 walls,
  6 openings y floor `8.03 x 5.35 m`.
- Source SHA-256 antes/después: `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.
  SHA-256 puntual de la derivada tras guardar: `2C0DFA489056E1DE426DE470F1EF6DDFA797E508A21A0F540FF5745A70477766`.
- El usuario aprobó visualmente T6.03: sofa y armchair diferenciables, cushions
  contrastados, coffee table reconocible como madera, arquitectura separada y
  lectura correcta en Material Preview. No se requieren ajustes antes de T6.04.

## Checkpoint real T6.04 — 2026-09-10 — IMPLEMENTED / APPROVED VISUALLY

- Blender 5.2.1 LTS permaneció abierto en la sesión gráfica autoritativa mediante
  MCP local, con `bpy.app.background=false`, derivada activa y `VIEW_3D` en
  `CAMERA` + `RENDERED`, sin objetos seleccionados.
- Antes de T6.04 `ReviewPresentation` tenía 0 objetos. Después contiene
  exactamente tres objetos, todos con namespace `HSLAYOUT_VISUAL_*` y ownership
  exclusivo en `ReviewPresentation`: `..._REVIEW_CAMERA_v1`,
  `..._REVIEW_KEY_AREA_v1` y `..._REVIEW_FILL_AREA_v1`.
- Iluminación determinista: key `AREA/DISK`, location `[-3.6,-0.2,4.6]`,
  rotation Euler `[0.363836,0,-0.404892]`, `900 W`, size `4.0 m`, color
  `[1.0,0.91,0.82]`; fill `AREA/DISK`, location `[-0.5,2.5,2.8]`, rotation
  `[0.833134,0,2.239086]`, `250 W`, size `3.0 m`, color `[0.82,0.90,1.0]`.
- Cámara de review: location `[-5.8,-1.0,1.7]`, target `[-2.4,1.1,0.6]`,
  rotation Euler `[1.30219,0,-1.017502]`, focal `35 mm`, sensor `36 mm`,
  clip `0.1–100 m`, DOF desactivado. La captura MCP y el render muestran
  sofá, sillón y mesa completos, con suelo, paredes y openings en contexto.
- World derivado `..._WORLD_v1`: Background `[0.035,0.045,0.055,1]`,
  strength `0.32`. Render ligero: engine `BLENDER_EEVEE` (identificador
  disponible en esta instalación; `BLENDER_EEVEE_NEXT` no está expuesto por la
  API local), PNG RGBA, `960×720`, 100 %, transparente desactivado.
- Review render único: `renders/previews/living-room-main-slice-006-visual-v1/review-v1.png`.
  SHA-256 puntual pre-sanitización
  `A81BD18990A43AF1ABB5B528A5DCEF3A61D543C9F665EAA4063F8F569A66A0BA`; no es
  golden contractual.
- Source SHA-256 antes/después:
  `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.
  SHA-256 puntual de la derivada tras guardar:
  `74EA4AF015C95FADD85EC5007E806A550D9F4E88CCC132E35A274ED3493FAC1D`.
- La arquitectura permanece en 22 walls, 6 openings y floor `8.03 × 5.35 m`;
  `HS3D_CAMERA`, `HS3D_KEY_LIGHT` y los cuatro `HS3D_MAT_*` técnicos siguen
  intactos. Los roots de furniture conservan location/yaw contractuales y
  `FurnitureVisual` mantiene 22 objetos.
- La re-aplicación controlada del setup usó nombres exactos y dejó tres objetos
  de review, sin `.001/.002`, sin decoración y sin geometría residual; la
  idempotencia lógica queda PASS. No se generó ningún backup `.blend1` final.
- El usuario aprobó visualmente T6.04: cámara interior útil; sofá, sillón y
  coffee table completos y reconocibles; arquitectura suficiente para entender
  el espacio; iluminación suficiente para distinguir muebles, materiales, suelo,
  paredes y openings; sin clipping funcional invalidante.
- Observaciones aceptadas como no bloqueantes y no convertidas en bugs:
  sofá próximo al borde izquierdo; apariencia todavía técnica/simple; geometría
  procedural deliberadamente simple; iluminación clara; sin fotorealismo ni
  decoración final.

## Checkpoint real T6.05 — 2026-09-10 — VALIDATED

- La sesión gráfica real de Blender 5.2.1 LTS quedó abierta con la escena
  derivada activa, `bpy.app.background=false`, `VIEW_3D` disponible y MCP
  operativo en `127.0.0.1:9876`. `get_scene_info`, `execute_blender_code` y
  captura MCP funcionaron; `get_addon_status` conserva la anomalía histórica
  `No module named 'blender_mcp.config'`, sin bloquear las operaciones reales.
- El source arquitectónico conserva exactamente SHA-256
  `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.
  No se abrió como escena de trabajo ni se guardó.
- FurniturePlan `furniture-placement-generator-1` conserva firma
  `b107d146c81a300858d33d48265d7e42480c88f6ed8443e6a54f80a008e19a0c`.
  Sofa `[-3.1,1.2,0]`, yaw `0°`, `2.2×0.95×0.85 m`; armchair
  `[-1.0,1.2,0]`, yaw `270°`, `0.8×0.8×0.9 m`; coffee table
  `[-3.1,0.2,0]`, yaw `90°`, `1.0×0.6×0.4 m`. IDs, ownership, hierarchy,
  metadata, provenance, unidades, sistema de coordenadas, footprint y binding
  pasaron; el envelope se validó con `anchor=bottom_center`.
- La arquitectura conserva 22 walls, 6 opening proxies, floor
  `8.03×5.35 m`, 0 fixed elements, la jerarquía de collections, `HS3D_CAMERA`,
  `HS3D_KEY_LIGHT` y los cuatro materiales técnicos `HS3D_MAT_*`.
- Los cinco materiales visuales aprobados de T6.03 conservan IDs, roles,
  `procedural_synthetic`, base colors, roughness, metallic, nodos Principled
  esperados y assignments deterministas; no hay imágenes, texturas externas ni
  duplicados `.001/.002`.
- `ReviewPresentation` contiene exclusivamente review camera, key area y fill
  area, con ownership y metadata correctos. El inventario lógico normalizado se
  leyó dos veces de forma independiente: ambas lecturas fueron idénticas,
  `canonical_length=85096`, fingerprint interno `315456719271` (evidencia de
  comparación, no golden binario). La comprobación de idempotencia lógica no
  encontró collections, objetos, materiales, assignments, luces, cámaras ni
  geometría residual duplicados.
- El review render inspeccionado en T6.05 era PNG legible, repo-relative,
  `960×720`, `863031` bytes, SHA puntual
  `A81BD18990A43AF1ABB5B528A5DCEF3A61D543C9F665EAA4063F8F569A66A0BA` antes de
  la sanitización posterior; no se promovió ese hash a golden.
- Gates: visual contract `6/6`; variant comparison `75/75`; Slice 005
  acceptance `5/5`; furniture `231/231`; room baseline `230/230`; histórico
  room `37/37`; validadores, generation plan y `room_to_plan` válidos; spatial
  validation sin errores ni warnings; golden v1 exacta
  `1105946a0dfe0088f5ad59da4178939644305b0d09b94022bfe5c87d9dde36f0`;
  Python `32`, JSON `11` y `git diff --check` PASS.
- La API real de Blender 5.2.1 expone únicamente `BLENDER_EEVEE`; no expone
  `BLENDER_EEVEE_NEXT`. Se documenta como nomenclatura/API, sin cambiar la
  escena ni tratarlo como limitación visual.
- La auditoría de privacidad, provenance y hygiene de la escena y del diff textual
  no encontró usernames, emails, secretos, UUIDs accidentales, fabricantes,
  assets o texturas externas, caches tracked, temporales, `.blend1` nuevos ni
  renders accidentales. La auditoría final de T6.06 detectó separadamente
  metadata no contractual en el PNG pre-sanitización y la corrigió.

## Checkpoint real T6.06 — 2026-09-10 — VALIDATED

- Se creó `docs/setup/006-visual-furnishing-materials-validation.md` siguiendo
  el patrón documental del repositorio, con contratos, artefactos, evidencia,
  gates, limitaciones, anomalías, rollback, provenance y fuera de alcance.
- `spec.md`, `plan.md` y `tasks.md` quedan coherentes con los estados reales:
  T6.01–T6.05 validadas y T6.06 validada. T6.06 no añade funcionalidad visual
  ni modifica la escena derivada.
- README.md y PROJECT_CONTEXT.md se actualizaron únicamente para corregir la
  referencia heredada que indicaba que Slice 005 no estaba iniciado; ambos
  reflejan Slice 005 integrado en `main` y ausencia de Slice 007.
- La auditoría final reprodujo metadata PNG no contractual (`eXIf` y `tEXt`,
  incluida una ruta absoluta) en el artefacto previo. Se sanitizó byte-level el
  PNG ya aprobado, eliminando `eXIf`, `tEXt`, `iTXt` y `zTXt` sin recompresión de
  `IDAT`: el resultado mide `862587` bytes y su SHA puntual es
  `05481687AC98123F571681530AAB7AF4CF76C9DD88485CD1EE7647BC19306594`.
- La equivalencia es exacta: hash de píxeles antes/después
  `ed9ca1260baa9b96896ad71fdb048914f318f0a49d9e83b012e4d5ea966bfab6` y hash
  de `IDAT` antes/después
  `d0d44dee1c9aa171022f0252c32dbd2e690215ee6b999efd87e4b98a35558d20`.
  El guard reutilizable de privacidad reside en
  `generate_furniture_visual.py` y su cobertura está en
  `tests/furniture/test_furniture_visual_contract.py`.
- Tras la corrección, el PNG no contiene chunks de metadata prohibidos, rutas
  privadas ni campos textuales no contractuales. No se modificaron Blender, el
  source, la derivada ni ningún parámetro visual.
- Gates finales tras la corrección: visual contract `8/8`, variant `75/75`, Slice
  005 `5/5`, furniture discovery `233/233`, room `230/230`, histórico `37/37`,
  validadores/generation plan/`room_to_plan`/spatial `PASS`, golden v1 exacta,
  Python `32`, JSON `11` y `git diff --check` PASS.
- El diff completo permanece limitado a Slice 006. La rama queda preparada para
  revisión final, sin staging, commit, push, merge ni PR.

## Decisiones cerradas para el diseño

- Baseline visual: `baseline-a`, no A/B/C.
- Assets v1: geometría procedural/simple, sin descargas.
- Materiales v1: nodos simples/procedurales, sin texturas externas.
- Render de revisión: ligero y reproducible; no calidad final.
- Workflow visual: Blender GUI + MCP obligatorios para tareas visuales.
- Checkpoints: humanos y bloqueantes; Codex no continúa automáticamente.
