# Especificación: Architectural Openings & Fixed Visual Elements v1

> Clasificación: T2
> Rama: `spec/007-architectural-openings-fixed-visual-v1`
> Estado: T7.01 y T7.05 validados; T7.02, T7.03 y T7.04 aprobados visualmente por una persona; T7.06 auditada con PASS. Slice 007 queda listo para revisión precommit.

## Objetivo

Añadir una capa visual procedural, reconocible y reversible para los seis
openings que ya existen en el contrato de `living-room-main`, manteniendo la
arquitectura, las medidas y la escena derivada de Slice 006 como autoridades.
La primera entrega debe mejorar la lectura visual de puertas y ventanas sin
convertir la geometría visual en geometría constructiva ni inventar elementos
físicos ausentes de los datos.

## Decisión de viabilidad

El concepto es viable para los seis openings existentes, con alcance reducido:

- dos puertas identificadas (`door-main`, `door-terrace`);
- cuatro ventanas identificadas (`window-v1` a `window-v4`);
- marcos visuales para los seis openings;
- hoja visual neutra, cerrada y no animada para las dos puertas;
- vidrio plano visual para las cuatro ventanas;
- banda de alféizar visual únicamente en la cota medida de las ventanas;
- cero elementos fijos visuales en `living-room-main`, porque
  `fixed_elements=[]`.

No se implementarán hojas abatibles, arcos de giro, herrajes, perfiles
constructivos, booleanos ni elementos fijos inventados.

## Autoridad contractual auditada

| Contrato | Valor |
| --- | --- |
| Room | `living-room-main` |
| Room schema | `1.1` |
| Room generator | `room-v1.1-generator-2` |
| Room logical signature | `182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a` |
| Units | `m` |
| Coordinate system | `canonical_room` |
| Source architectural | `blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend` |
| Source SHA-256 | `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280` |
| Slice 006 derived input | `blender/scenes/review/2026-09-10-living-room-main-slice-006-visual-v1.blend` |
| Slice 006 derived SHA | `74EA4AF015C95FADD85EC5007E806A550D9F4E88CCC132E35A274ED3493FAC1D` |
| Existing visual contract | `visual-scene-contract-1` |

El layout y el FurniturePlan siguen siendo contratos de Slice 006 aunque no
son la autoridad geométrica de los openings:

| Contrato | Valor |
| --- | --- |
| Layout authority | `layouts/living-room-main/variants/baseline-a.json` |
| FurniturePlan generator | `furniture-placement-generator-1` |
| FurniturePlan signature | `b107d146c81a300858d33d48265d7e42480c88f6ed8443e6a54f80a008e19a0c` |

## Modelo contractual real de openings

El schema `room-v1.1` no tiene una categoría genérica de opening en el room
real: expone `openings.doors` y `openings.windows`. Cada entrada contiene
`id`, `wall_id`, `offset`, `width`, `height` y, en el room real, `depth`;
las ventanas contienen además `sill_height`. `opening_direction` existe como
enum, pero sus seis valores reales son `unknown`.

La posición y la orientación no son campos independientes del JSON. Se
obtienen de forma determinista mediante `wall_id`, el segmento canónico, el
offset y la dirección del muro en `build_generation_plan`. Por tanto, una
orientación visual derivada no se documentará como una lectura física.

| ID | Tipo | Wall | Offset | Width | Height | Sill | Depth | Wall thickness | Direction |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `door-main` | door | `wall-00` | 0.45 measured | 1.60 measured | 2.00 measured | 0.00 derived, floor anchor | 0.08 measured | 0.08 measured | `unknown` |
| `door-terrace` | door | `wall-06` | 0.00 derived | 0.55 measured | 2.30 measured | 0.00 derived, floor anchor | 0.05 measured | 0.08 measured | `unknown` |
| `window-v1` | window | `wall-20` | 0.10 measured | 0.74 measured | 1.39 measured | 0.92 measured | 0.08 measured | 0.08 measured | `unknown` |
| `window-v2` | window | `wall-14` | 0.64 derived | 2.40 measured | 1.39 measured | 0.92 measured | 0.08 measured | 0.08 measured | `unknown` |
| `window-v3` | window | `wall-07` | 0.00 derived | 3.69 measured | 1.25 measured | 0.86 measured | 0.06 measured | 0.08 measured | `unknown` |
| `window-v4` | window | `wall-08` | 0.00 derived | 1.32 measured | 1.25 measured | 0.86 measured | 0.06 measured | 0.08 measured | `unknown` |

El generation plan actual aporta, además, estas posiciones de referencia y
vectores derivados:

| ID | `position_m` del proxy | `direction` del wall | `outward` |
| --- | --- | --- | --- |
| `door-main` | `[-1.25, 0.04, 0.0]` | `[1.0, 0.0, 0.0]` | `[0.0, -1.0, 0.0]` |
| `door-terrace` | `[-7.755, -0.765, 0.0]` | `[1.0, 0.0, 0.0]` | `[0.0, -1.0, 0.0]` |
| `window-v1` | `[-0.47, 2.71, 0.0]` | `[-1.0, 0.0, 0.0]` | `[0.0, 1.0, 0.0]` |
| `window-v2` | `[-4.30, 4.01, 0.0]` | `[-1.0, 0.0, 0.0]` | `[0.0, 1.0, 0.0]` |
| `window-v3` | `[-8.00, 1.055, 0.0]` | `[0.0, -1.0, 0.0]` | `[-1.0, 0.0, 0.0]` |
| `window-v4` | `[-7.37, 2.87, 0.0]` | `[-1.0, 0.0, 0.0]` | `[0.0, 1.0, 0.0]` |

Los `source_id`, `status`, `uncertainty`, `method`, `formula` y
`depends_on` disponibles son provenance de campo. No existe un campo
`confidence`, un booleano `estimated` ni un header medido para estos openings.
En consecuencia:

- el header físico es `UNKNOWN / NOT CONTRACTUALLY AVAILABLE`;
- la cota superior visual puede calcularse como `sill + height`, marcada como
  `derived`, no como medición de header;
- el sentido de apertura es `UNKNOWN / NOT CONTRACTUALLY AVAILABLE`;
- la lista real `fixed_elements` está vacía; el schema sí soporta
  `pillar`, `recess`, `radiator`, `socket`, `switch` y `fixed`, pero el
  fixture sintético no autoriza a crear ninguno en esta habitación.

## Viabilidad por elemento

| Elemento | Estado | Justificación y límite |
| --- | --- | --- |
| Marcos visuales de puertas | **SUPPORTED** | Tipo, wall, offset, ancho, altura, profundidad y wall thickness de ambas puertas. El ancho del perfil será un parámetro visual sintético. |
| Hojas de puerta | **PARTIALLY SUPPORTED** | El tipo y el envelope permiten una hoja plana cerrada y neutra. Espesor, bisagras, herrajes, particiones y pose de apertura no están medidos. |
| Marcos visuales de ventanas | **SUPPORTED** | Tipo, wall, offset, ancho, altura, profundidad, sill y wall thickness de las cuatro ventanas. El perfil será visual, no constructivo. |
| Vidrio simple | **SUPPORTED** | `window` identifica el opening y aporta un envelope completo; se admite un panel plano procedural sin afirmar espesor o acristalamiento real. |
| Alféizares | **PARTIALLY SUPPORTED** | La cota `sill_height` está medida en ventanas, pero no existen vuelo, perfil, ancho constructivo ni material físico. Solo se permite una banda flush visual. |
| Profundidad de huecos | **SUPPORTED** | `depth` está medida en los seis openings; además, el espesor de muro de sus seis jambas es `0.08 m measured`. No se extrapola profundidad fuera del envelope. |
| Sentido/apertura de puertas | **NOT SUPPORTED** | Los seis `opening_direction` son `unknown`; no se generarán swings, arcos ni animación. |
| Elementos fijos adicionales | **NOT SUPPORTED para el target real** | `living-room-main` contiene `fixed_elements=[]` y la escena tiene 0 objetos en `FixedElements`; la entrega no puede inventar obstáculos. |
| Header medido | **PARTIALLY SUPPORTED** | No hay campo ni lectura de header; solo puede derivarse la cota superior desde sill y height para colocar geometría visual. |

## Alcance v1

Incluye únicamente:

- una capa `ArchitecturalVisual` separada, hermana de los roots existentes;
- un frame procedural por cada uno de los seis openings, alineado con los
  valores efectivos del generation plan;
- una hoja de puerta plana, cerrada y neutral para `door-main` y
  `door-terrace`, con su aproximación declarada en metadata;
- un panel de vidrio simple para cada ventana;
- una banda de alféizar flush para cada ventana, colocada en la cota medida;
- cuatro materiales visuales procedurales estables, sin imágenes ni texturas
  externas;
- metadata de identidad, tipo, wall, provenance de campos y estado de
  aproximación;
- regeneración idempotente sobre una copia derivada de Slice 006;
- revisión con Blender GUI + MCP local y STOP VISUAL humano;
- render final únicamente cuando la inspección visual lo solicite, con el
  guard de privacidad PNG ya existente.

Parámetros visuales sintéticos propuestos, que no son medidas de la vivienda:

| Parámetro | Valor v1 | Semántica |
| --- | ---: | --- |
| `frame_profile_width_m` | 0.05 | ancho visual del marco |
| `frame_projection_m` | 0.02 | proyección visual sintética hacia el lado de la habitación para despejar el plano del proxy |
| `panel_recess_m` | 0.01 | retranqueo visual de vidrio/infill respecto al frame |
| `door_leaf_thickness_m` | 0.03 | espesor visual de hoja cerrada |
| `glass_thickness_m` | 0.01 | espesor visual del panel, no acristalamiento medido |
| `sill_band_height_m` | 0.03 | altura visual de banda flush |

`frame_profile_width_m`, `frame_projection_m` y `panel_recess_m` son constantes
sintéticas de legibilidad, no perfiles ni profundidades constructivas medidas.
En ventanas, el lado local `+Y` representa el lado de la habitación: el frente
del frame se coloca en `depth/2 + frame_projection_m`, el frame conserva una
profundidad `min(depth, 2 * frame_projection_m)` y el frente del glass queda
`panel_recess_m` detrás del reverso del frame. El sill sigue el mismo centro
Y del frame y permanece discreto. La puerta conserva el root y el placement
contractual de T7.02; su frame e infill visuales pueden usar la misma política
sintética de profundidad sin alterar ese authority. Estos valores deben quedar marcados como
`procedural_synthetic` y nunca entrar en `measurements/`, schemas o el
generation plan.

## Fuera de alcance

- fotorealismo, decoración y acabado final;
- cortinas, persianas detalladas, lámparas decorativas, plantas, cuadros o
  alfombras;
- fabricantes, marcas, productos comerciales, assets o texturas externas;
- UV/PBR complejo, servicios remotos o descargas;
- booleanos, cortes constructivos, remodelación arquitectónica o cambio de
  medidas;
- hojas abiertas, sentidos de giro, bisagras, manillas, herrajes o animación;
- generación de cualquier objeto para `fixed_elements` vacío;
- muebles, ergonomía, circulación, ranking, A/B/C, UI, VR/AR, física o
  iluminación avanzada;
- cambios al room pipeline, schemas, measurements, FurniturePlan, Slice 005
  o Slice 006;
- Slice 008 o cualquier slice posterior no definido.

## Arquitectura visual materializada

La escena de trabajo se obtuvo con `Save As` desde la derivada de Slice 006
hacia la salida materializada:

`blender/scenes/review/2026-09-10-living-room-main-slice-007-architectural-visual-v1.blend`

La fuente arquitectónica y la derivada de Slice 006 permanecerán read-only.
La jerarquía materializada es:

```text
HS3D_ROOM_living-room-main
  Architecture
  Openings                  # proxies técnicos, intactos
  FixedElements             # vacío para living-room-main
  Validation
HSLAYOUT_living-room-main_* # overlay FurniturePlan, intacto
HSLAYOUT_VISUAL_*          # FurnitureVisual + ReviewPresentation de T6
HSARCH_VISUAL_living-room-main_slice-007_v1
  ArchitecturalVisual
    OpeningVisual
    FixedElementVisual      # vacío y validado explícitamente
```

Los objetos de `OpeningVisual` usarán nombres deterministas:

- `HSARCH_VISUAL_living-room-main_<opening_id>_ROOT_v1`;
- `HSARCH_VISUAL_living-room-main_<opening_id>_FRAME_v1`;
- `HSARCH_VISUAL_living-room-main_<opening_id>_LEAF_v1` solo para puertas;
- `HSARCH_VISUAL_living-room-main_<opening_id>_GLASS_v1` solo para ventanas;
- `HSARCH_VISUAL_living-room-main_<opening_id>_SILL_v1` solo para ventanas.

Los materiales tendrán exactamente estos nombres dentro de la capa visual:

- `hs3d_visual_mat_arch_opening_frame_v1`;
- `hs3d_visual_mat_arch_door_leaf_v1`;
- `hs3d_visual_mat_arch_window_glass_v1`;
- `hs3d_visual_mat_arch_sill_v1`.

Cada objeto conservará, como mínimo, `hs3d_visual_owner=ArchitecturalVisual`,
`hs3d_visual_namespace=HSARCH_VISUAL`, `hs3d_room_id`, `hs3d_opening_id`,
`hs3d_opening_kind`, `hs3d_wall_id`, `hs3d_source_ids`, los estados y valores
efectivos usados, `hs3d_opening_direction=unknown`,
`hs3d_visual_approximation` cuando corresponda,
`hs3d_provenance=procedural_synthetic`, `hs3d_constructive_geometry=false` y
la versión del generador. Los `source_ids` deben ser los que ya existen en el
room/generation plan; no se inventará un source ID físico.

La capa visual no será consumida por el normalizer arquitectónico como entidad
managed. Los proxies `HS3D_DOOR_*` y `HS3D_WINDOW_*` se conservarán con su
ownership, metadata, transforms y materiales técnicos. La nueva geometría no
podrá modificar paredes, suelo, openings técnicos, fixed elements, Furniture,
FurnitureVisual, cámara ni luces existentes.

La `ReviewPresentation` de Slice 006 se reutilizará sin añadir cámaras ni
luces. Si la vista actual no permite evaluar un opening, se registrará como
limitación/decisión de revisión; no se cambiará automáticamente la
composición.

## Determinismo, idempotencia y límites de mutación

- El input será el room JSON validado y su generation plan determinista; no se
  leerán medidas desde la geometría visual.
- Los openings se procesarán por `id` ordenado y los componentes por un orden
  fijo (`FRAME`, `LEAF`/`GLASS`, `SILL`).
- `position_m`, `direction`, `outward`, `width_m`, `height_m`, `sill_height_m`
  y `depth_m` procederán del plan efectivo y conservarán sus estados.
- La hoja de puerta usará siempre la pose `closed_neutral`; cualquier intento
  de usar `opening_direction != unknown` quedará fuera de este v1.
- `fixed_elements` no vacío será un input no soportado para este target y debe
  producir un fallo explícito, no un objeto por defecto.
- Una segunda ejecución debe encontrar el root propio, sustituir únicamente
  su contenido y producir el mismo inventario lógico; nunca debe tocar roots
  de room, FurniturePlan o Slice 006.
- No se prometerá hash binario idéntico del `.blend` ni del PNG.

## Criterios de aceptación

- [x] Los seis IDs reales se resuelven exactamente como 2 doors y 4 windows;
  no se crea una categoría genérica ni se inventa un opening.
- [x] El contrato conserva source, room signature, units, coordinates,
  offsets, dimensions, depths, sills, wall IDs y provenance observada/derivada.
- [x] Se crean exactamente los componentes permitidos para cada tipo y cero
  componentes en `FixedElementVisual` para `living-room-main`.
- [x] La escena derivada tiene root, collections, names, ownership, metadata y
  materiales deterministas sin `.001/.002` ni objetos fuera de la capa.
- [x] La arquitectura `HS3D_ROOM_*`, los proxies técnicos y la capa Furniture
  permanecen byte/contractualmente sin mutación; el source conserva su SHA.
- [x] Dos lecturas o regeneraciones lógicas producen inventarios idénticos;
  no se exige igualdad binaria del `.blend`.
- [x] La evidencia de viewport (y el review render solo si se genera) muestra
  openings reconocibles sin clipping funcional; el STOP VISUAL lo aprueba una
  persona.
- [x] El preview, si se versiona, es PNG válido y pasa el guard de privacidad;
  no contiene metadata privada y su hash solo es evidencia puntual.
- [x] Los gates de Python/JSON, validadores room, comparación room-to-plan,
  preservación de Slice 006 y `git diff --check` pasan.

## Casos de error y límites

- Opening con tipo distinto de `door` o `window`: rechazo explícito como
  `unsupported_opening_kind`.
- Campo contractual requerido ausente o con estado no usable: rechazo; no se
  aplica el fallback visual de `0.10 m` de la generación histórica salvo que
  el plan efectivo lo exponga explícitamente y se conserve su provenance.
- `opening_direction` distinto de `unknown`: no se interpreta como swing; se
  rechaza o se mantiene fuera del alcance de este v1.
- `fixed_elements` no vacío en el target: rechazo explícito y sin objetos
  visuales fijos.
- Source y derivada con la misma ruta: bloqueo de source protection.
- Root o material ya existente con ownership ajeno: bloqueo de idempotencia,
  sin borrado masivo.
- Metadata PNG prohibida o ruta local: se aplica el guard existente y el
  artefacto no se versiona hasta pasar la auditoría.

## Riesgos e invariantes

- **Riesgo:** promover una aproximación visual a geometría arquitectónica.
  **Mitigación:** root hermano, `constructive_geometry=false`, metadata de
  approximation y ningún cambio al normalizer.
- **Riesgo:** inventar swing, header, sill profile o fixed elements.
  **Mitigación:** matriz de viabilidad, rechazo de direction no soportada,
  banda flush únicamente y colección fixed vacía.
- **Riesgo:** mutar el source o la derivada aprobada de Slice 006.
  **Mitigación:** abrir read-only, `Save As` a la ruta Slice 007 y hashes antes
  y después.
- **Riesgo:** duplicados por ejecución repetida.
  **Mitigación:** namespace propio, ownership exclusivo, nombres deterministas
  y comparación de inventario lógico.
- **Riesgo:** filtrar rutas locales mediante el render.
  **Mitigación:** validación/sanitización byte-level de chunks PNG y auditoría
  de secretos antes de versionar.

Invariantes: metros, `canonical_room`, room generator y signature, source SHA,
seis IDs, cero fixed elements en el target, `proxy_only=true` y
`constructive_geometry=false` en la capa técnica, y separación completa de
`HS3D_*`, `HSLAYOUT_*`, `HSLAYOUT_VISUAL_*` y `HSARCH_VISUAL_*`.

## Evidencia visual y workflow

- Requerida: sí.
- Blender: `5.2.1 LTS`, GUI visible, `bpy.app.background=false`, `VIEW_3D` y
  MCP local en `127.0.0.1:9876`.
- La aceptación debe observar seis openings, reconocer puertas/ventanas,
  comprobar que el vidrio y los marcos no ocultan arquitectura y confirmar
  ausencia de clipping funcional.
- El STOP VISUAL humano requerido antes de T7.05/T7.06 quedó completado en
  T7.02–T7.04.
- No se usará background/headless como sustituto de la inspección gráfica.

## Compatibilidad, rollback y dependencias

La compatibilidad se mantiene al no modificar schemas, measurements,
generators room, FurniturePlan, source ni Slice 006. El rollback consiste en
descartar la nueva derivada y preview de Slice 007 o regenerarlos desde el
source + Slice 006 derivada + contratos, sin sobrescribir ninguna autoridad.

Dependencias externas: ninguna. Se reutilizan Blender 5.2.1 GUI, Blender MCP
local y las librerías estándar existentes. No se incorporan assets, servicios,
addons ni paquetes.

## Resultado de T7.02

T7.02 está implementado en dos capas separadas: el planificador puro
`blender/scripts/architecture/architectural_visual_geometry.py` y el adaptador
Blender `blender/scripts/architecture/materialize_architectural_visual.py`.
La derivada materializada es
`blender/scenes/review/2026-09-10-living-room-main-slice-007-architectural-visual-v1.blend`.

La escena contiene, bajo `HSARCH_VISUAL_living-room-main_slice-007_v1`, seis
roots `EMPTY`, 6 frames, 2 neutral door infills, 4 glass panels y 4 sill
bands; `FixedElementVisual` permanece vacío. El inventario de la primera y la
segunda materialización coincide: 4 colecciones visuales, 22 objetos visuales,
6 roots y 16 meshes. La segunda pasada conservó además los 22 nombres estables
sin sufijos de fallback. No se crearon materiales en T7.02, no se cambió la
cámara, las luces, la arquitectura, FurnitureVisual, ReviewPresentation ni
las derivadas protegidas.

La primera revisión visual detectó un perfil de 0.04 m y una separación de
frente de solo 0.005 m, con frame y paneles centrados en el mismo plano local.
La última revisión pidió mejorar específicamente la lectura de profundidad de
las ventanas. La nueva prueba RED falló con el frame de ventana todavía en el
plano frontal antiguo. La corrección final conserva el inventario y
`frame_profile_width_m=0.05`, y usa `frame_projection_m=0.02` para despejar
visualmente el proxy; el glass queda detrás del reverso del frame mediante
`panel_recess_m=0.01`. Los anchos y alturas de los infills de puerta no cambian;
la profundidad sintética de `door-terrace` queda acotada a 0.02 m para
permanecer dentro de su opening de 0.05 m. Los tests puros de T7.02 pasan
34/34 y el resultado lógico es determinista.
La nueva derivada observada tras la regeneración limpia y el guardado en
Blender GUI tiene 178386 bytes; su SHA puntual es
`9CE444108950CBF715BF295EDC0256C79C7B10AA7AFD8BDB31F72A3F3CB39CE4` y no es
un golden binario.
El estado documental permaneció deliberadamente abierto hasta el STOP VISUAL,
que ya quedó completado:

**T7.02 — HUMAN VISUAL ACCEPTANCE — APPROVED**

## Resultado de T7.03

T7.03 añade exclusivamente datos de material y assignments a los 16 meshes
`HSARCH_VISUAL_*`; el planificador geométrico de T7.02 no cambia. El contrato
puro está en `blender/scripts/architecture/architectural_visual_materials.py`
y el adaptador Blender en
`blender/scripts/architecture/materialize_architectural_visual.py`. La escena
derivada Slice 007 conserva 6 roots, 16 meshes, 22 objetos visuales y
`FixedElementVisual` vacío.

Los cuatro materiales exactos son:

- `hs3d_visual_mat_arch_opening_frame_v1`: `opening_frame`, base color
  `[0.74, 0.76, 0.78, 1.0]`, roughness `0.42`, metallic `0.0`;
- `hs3d_visual_mat_arch_door_leaf_v1`: `door_presentation_panel`, base color
  `[0.36, 0.20, 0.10, 1.0]`, roughness `0.58`, metallic `0.0`;
- `hs3d_visual_mat_arch_window_glass_v1`: `window_glass`, base color
  `[0.88, 0.90, 0.92, 1.0]`, roughness `0.06`, metallic `0.0`, alpha `0.16`
  y transmission weight `0.88`;
- `hs3d_visual_mat_arch_sill_v1`: `sill_band`, base color
  `[0.52, 0.54, 0.56, 1.0]`, roughness `0.50`, metallic `0.0`.

Todos son `procedural_synthetic`, visual-only, sin imágenes, texturas ni
assets externos, con dos nodos (`Principled BSDF` y `Material Output`). Los
assignments son por `component_type`: los 6 frames usan el material de frame,
los 2 `DOOR_INFILL` el material de hoja, los 4 `GLASS` el material de vidrio y
los 4 `SILL` el material de sill; cada mesh tiene exactamente un slot. La
materialización GUI/MCP se ejecutó dos veces, reutilizó los cuatro datablocks,
conservó la huella geométrica live `11632:642518` y no modificó arquitectura,
muebles, cámara, luces ni materiales técnicos.

La escena permaneció en Blender GUI 5.2.1 LTS con `bpy.app.background=false`,
`VIEW_3D` disponible y engine observado `BLENDER_EEVEE`. Las capturas de
`WINDOW_MATERIAL_CLOSEUP_T7_03` y `DOOR_MATERIAL_CLOSEUP_T7_03` quedan como
evidencia de inspección; T7.03 fue posteriormente aprobada visualmente y no
se afirma fotorealismo ni un material constructivo real.

La calibracion visual del glass se ajusto en dos pasos: primero a un gris azulado
claro y transmisivo (`[0.76, 0.80, 0.84]`, alpha `0.22`, transmission `0.78`) y
despues a la configuracion final de baja saturacion indicada arriba. No se
modificaron nodes, engine, geometria ni otros materiales. La aceptacion humana
se completó después de resolver la interferencia del proxy; el viewport
pre-policy aún mostraba el panel azul dominante y no permitía confirmar contexto
claramente visible detrás del glass.

La auditoria A/B de T7.03 demostro que la dominante azul procedia de los seis
opening proxies tecnicos, que son opacos y se solapan con los componentes
visuales. Se implemento una politica explicita de `presentation visibility
override`: cuando existe la representacion `HSARCH_VISUAL_*`, el proxy tecnico
permanece intacto en `Openings` y conserva su autoridad, pero se excluye de la
presentacion mediante `Object.hide_viewport=True` y `Object.hide_render=True`.
No se usa `hide_set`, no se borra, desplaza ni cambia ningun dato geometrico,
transform, material o metadata del proxy. La politica es reversible, apunta
unicamente a los seis nombres contractuales y deja intactos Architecture,
FurnitureVisual, ReviewPresentation y las colecciones no relacionadas.

El contrato puro esta en
`blender/scripts/architecture/architectural_visual_visibility.py` y el adaptador
Blender en
`blender/scripts/architecture/materialize_architectural_visual_visibility.py`.
La aplicacion GUI/MCP se ejecuto dos veces sobre la derivada Slice 007, con los
seis proxies presentes y las 22 piezas visuales HSARCH presentes en ambas
pasadas; las huellas independientes de los proxies fueron iguales antes y
despues, no hubo cambios de visibilidad fuera de esos seis objetos y
`FixedElementVisual` continuo vacio. La escena guardada permanece en GUI
Blender 5.2.1, `bpy.app.background=false`, `VIEW_3D` y `BLENDER_EEVEE`.
La aceptacion humana de T7.03 fue completada y aprobada. La politica de
visibilidad de presentacion tambien quedo aprobada: los proxies tecnicos
siguen siendo autoridad y permanecen intactos; solo se excluyen de la
presentacion derivada cuando existe la representacion HSARCH correspondiente.

## Resultado de T7.04

T7.04 se ejecuto como integracion y revision visual de la derivada existente;
no requirio geometria, materiales, politica de visibilidad, camara, luces ni
codigo adicional. La escena activa es
`blender/scenes/review/2026-09-10-living-room-main-slice-007-architectural-visual-v1.blend`.

La comprobacion live mediante Blender GUI/MCP confirmo Blender 5.2.1 LTS,
`bpy.app.background=false`, `VIEW_3D` disponible y `BLENDER_EEVEE`. La capa
`HSARCH_VISUAL_living-room-main_slice-007_v1` contiene exactamente las
colecciones `ArchitecturalVisual`, `OpeningVisual` y `FixedElementVisual`;
mantiene 6 roots, 16 meshes, 22 objetos visuales y 0 fixed objects. Los seis
proxies tecnicos continuan en `Openings`, existen y usan
`hide_viewport=True`/`hide_render=True` para presentacion, sin mutacion de su
geometria, transforms, dimensiones, materiales o metadata. ReviewPresentation
conserva exactamente una camara y dos luces, sin cambios de parametros.

Se obtuvo evidencia de viewport para integracion de habitacion, contexto
arquitectonico, ventanas, puertas, frame, glass, sill, neutral infill y
ausencia de clipping funcional. No se genero un render nuevo porque las
capturas de viewport fueron suficientes para este checkpoint.

T7.04 queda aprobado visualmente por una persona. El registro de aceptación
humana confirma reconocimiento conjunto de puertas y ventanas, legibilidad de
la arquitectura para el alcance del slice, integración con FurnitureVisual,
ausencia de clipping funcional evidente y reutilización de ReviewPresentation.
No se requieren modificaciones adicionales de geometría, materiales,
visibilidad de proxies ni integración visual. T7.04 queda congelado.

## Resultado de T7.05

T7.05 queda completado con PASS como auditoría objetiva de reproducibilidad,
mutación, privacidad y validación. No requería una aceptación visual humana
adicional: la aceptación visual contractual quedó registrada en T7.02, T7.03
y T7.04.

La validación ejecutó explícitamente 555 tests y obtuvo `555/555 PASS`, con
arquitectura `92/92`, measurements `230/230` y furniture `233/233`. También
pasaron los validadores de room, generation plan, `room_to_plan`, spatial,
golden, Python AST `42/42`, JSON `11/11`, privacy/hygiene y whitespace.
La discovery genérica del repositorio devolvió `0 tests`: no se considera
PASS ni suite completa y permanece como deuda conocida. Los runners Blender
históricos que regeneran o mutan escenas no se ejecutaron durante este cierre.

La lectura del inventario normalizado se repitió y produjo el mismo resultado:
6 opening roots, 16 meshes, 22 objetos HSARCH, 6 frames, 2 neutral door
infills, 4 glass, 4 sill bands, 0 fixed visual objects, sin `.001/.002` ni
duplicados. La repetición del contrato puro fue idéntica y no mutó inputs.
La escena se inspeccionó con Blender GUI/MCP live en Blender 5.2.1 LTS,
`bpy.app.background=False`, `VIEW_3D` disponible y
`bpy.data.is_dirty=False`; `execute_blender_code`/MCP live funcionó. La deuda
histórica de `get_addon_status` (`No module named 'blender_mcp.config'`) queda
documentada como no bloqueante y no se modificó producción para resolverla.

Source, Slice 006 derived, room signature y FurniturePlan signature conservan
sus contratos. Los seis proxies siguen en `Openings`, con su huella contractual
intacta y solo `hide_viewport=True`/`hide_render=True` para presentación en la
derivada; `hide_set` no se usó como sustituto. No existe PNG contractual nuevo
de Slice 007, por lo que no se generó uno únicamente para satisfacer esta
auditoría.

**T7.05 — REPRODUCIBILITY / MUTATION / PRIVACY / VALIDATION — PASS**

## Resultado de T7.06

T7.06 audita la implementación real, los tres documentos de Slice 007, los
tests explícitos, la escena derivada y los contratos heredados. La auditoría
confirma que la única vertical implementada es la visualización procedural de
openings/fixed visual v1: no hay decoración, assets comerciales, texturas
externas, fotorealismo, nuevas variantes de furniture, cambios en
Architecture/FurniturePlan, medidas inferidas de fotografías ni Slice 008.

La escena final contiene exactamente 6 opening roots, 16 meshes HSARCH, 6
frames, 4 glass panels, 2 neutral door infills, 4 sill bands, 0 fixed visual
objects y 22 objetos HSARCH gestionados. La geometría es determinista, no hay
`.001/.002`, duplicados ni orphan meshes, y se conserva el fingerprint
geométrico esperado. Los cuatro materiales visuales exactos son frame, door
leaf/infill, glass y sill; todos son `procedural_synthetic`, sin image textures,
rutas externas, marcas, fabricantes ni assets comerciales. El glass conserva la
calibración aprobada: Base Color `(0.88, 0.90, 0.92, 1.0)`, Roughness `0.06`,
Metallic `0.0`, Alpha `0.16`, Transmission `0.88`, IOR `1.5/default`. Blender
5.2.1 observa `surface_render_method=DITHERED` y el alias API
`blend_method=HASHED` para esta configuración.

La documentación distingue inequívocamente `TECHNICAL AUTHORITY` de
`VISUAL PRESENTATION`: los seis proxies siguen existiendo en `Openings`, con
geometría, transforms, dimensiones, materiales y metadata contractuales; en la
derivada solo tienen `hide_viewport=True` y `hide_render=True`, con
`hide_get/hide_set` sin uso. Architecture, FurniturePlan, FurnitureVisual,
ReviewPresentation, cámara, luces, source y Slice 006 derived permanecen
intactos. La privacidad/hygiene no detectó rutas Windows privadas, usernames,
metadata sensible, ningún `.blend1` nuevo generado por Slice 007, temporales,
capturas accidentales ni artefactos no previstos; el único `.blend1` observado
es el fixture histórico/preexistente `blender/scenes/tests/001-foundation-room.blend1`,
ignorado y fuera del scope de Slice 007.

La documentación final queda coherente con la implementación y registra las
aceptaciones humanas existentes sin inventar una aceptación nueva para T7.05
ni T7.06:

- T7.02 — HUMAN VISUAL ACCEPTANCE — APPROVED.
- T7.03 — HUMAN VISUAL ACCEPTANCE — APPROVED.
- T7.04 — HUMAN VISUAL ACCEPTANCE — APPROVED.

**T7.06 — FINAL DOCUMENTATION & AUDIT — PASS**

**SLICE 007 FINAL AUDIT PASSED — READY FOR PRECOMMIT REVIEW**

## Estado de T7.01

T7.01 queda implementado y validado como contrato puro, sin importar `bpy`,
crear meshes, materiales o escenas. El contrato reconoce los seis openings,
conserva sus medidas y vectores efectivos, mantiene `opening_direction=unknown`,
deja `FixedElementVisual` vacío y rechaza capacidades no soportadas. T7.02 está
aprobado visualmente por una persona. T7.03 está aprobado visualmente por una
persona. T7.04 está aprobado visualmente por una persona y queda congelado;
T7.05 queda completado con PASS y T7.06 queda completado con PASS. No se
realizó commit, staging, push, PR, merge, rebase, squash ni force push.
