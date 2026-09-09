# Especificación: Visual Furnishing & Materials v1

> Clasificación: T2
> Rama: `spec/006-visual-furnishing-materials-v1`
> Estado: diseño documental; T6.01–T6.06 pendientes.

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

- [ ] T6.01 fija el contrato de escena, ownership, provenance, rollback y
  workflow GUI+MCP sin modificar T4/T5.
- [ ] T6.02 produce en una sesión gráfica una habitación donde sofá, sillón y
  mesa sean visualmente reconocibles, manteniendo el placement de baseline A y
  alcanzando un STOP VISUAL con evidencia de viewport.
- [ ] T6.03 asigna materiales procedurales simples y diferenciables a paredes,
  suelo y muebles, con `material_id`, roughness, metallic y provenance
  deterministas; alcanza un STOP VISUAL.
- [ ] T6.04 proporciona iluminación y cámara de revisión reproducibles,
  muestra arquitectura y muebles sin clipping ni oscuridad obstructiva, genera
  un review render ligero y alcanza un STOP VISUAL.
- [ ] T6.05 demuestra que source, measurements, layout, FurniturePlan y
  contracts no mutaron; normaliza/inspecciona la escena derivada; registra
  evidencia estructural, de privacidad y visual; alcanza aceptación humana.
- [ ] T6.06 actualiza documentación y gates sin añadir nueva funcionalidad,
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

## Decisiones cerradas para el diseño

- Baseline visual: `baseline-a`, no A/B/C.
- Assets v1: geometría procedural/simple, sin descargas.
- Materiales v1: nodos simples/procedurales, sin texturas externas.
- Render de revisión: ligero y reproducible; no calidad final.
- Workflow visual: Blender GUI + MCP obligatorios para tareas visuales.
- Checkpoints: humanos y bloqueantes; Codex no continúa automáticamente.
