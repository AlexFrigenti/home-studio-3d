# Tareas: Visual Furnishing & Materials v1

Estados: `[ ]` pendiente · `[~]` en curso · `[x]` validada · `[!]` bloqueada.

> Diseño publicado desde `main` después del merge de Slice 005. T6.01 está
> validada con un checkpoint Blender derivado y un contrato puro; T6.02–T6.04
> están validadas visualmente; T6.05 y T6.06 están validadas.

## Reglas comunes

- Clasificación T2.
- Baseline visual: `living-room-main` + `baseline-a`.
- `measurements/`, `FurniturePlan` y `SpatialValidationReport` son autoridades
  de entrada; la escena visual nunca promueve ni corrige sus valores.
- Las tareas T6.02–T6.05 requieren Blender 5.2.1 LTS en modo gráfico, MCP
  local en `127.0.0.1:9876`, inspección visual y STOP humano.
- Background solo respalda tests, estructura y reproducción; no sustituye la
  inspección del viewport/render.
- Source arquitectónico y contratos T4/T5 se preservan; toda escritura va a
  una escena derivada.
- No assets externos, fabricantes, texturas externas, secretos, rutas
  absolutas, Slice 007 ni comparación visual A/B/C.
- Cada tarea termina con evidencia o con un gate marcado `NO EJECUTADO`/
  `PENDIENTE DE INFRAESTRUCTURA`, nunca con un PASS inventado.

## T6.01 [x] — Visual scene contract & Blender live workflow

- [x] Fijar la versión del contrato visual, source/derived paths, units,
  coordinate system y baseline A.
- [x] Fijar roots y ownership: `HS3D_ROOM_*` intacto, `HSLAYOUT_*` semántico
  intacto y `HSLAYOUT_VISUAL_*` como root visual hermano.
- [x] Fijar colecciones visuales `FurnitureVisual` y `ReviewPresentation`,
  nombres deterministas y metadata `hs3d_visual_*`.
- [x] Fijar que `item_id`, `source_id`, `dimensions_status`, transforms,
  footprint y firmas proceden del FurniturePlan; la forma visual es detalle.
- [x] Fijar material contract mínimo: `material_id`, `semantic_role`,
  `base_color`, `roughness`, `metallic`, `provenance`.
- [x] Definir rollback mediante Save As/checkpoints y prohibir sobrescribir el
  source.
- [x] Confirmar el workflow Codex → MCP → Blender GUI → inspección y el primer
  STOP antes de crear muebles visuales.
- [x] Validación: revisión documental, gates pure de entrada y comprobación de
  que no se modifican T4/T5.

### Evidencia T6.01

- Derivada activa: `blender/scenes/review/2026-09-10-living-room-main-slice-006-visual-v1.blend`.
- Root creado: `HSLAYOUT_VISUAL_living-room-main_slice-005-acceptance-baseline-a_v1`.
- Collections vacías: `FurnitureVisual`, `ReviewPresentation`; no se creó ningún objeto visual.
- Source SHA-256 antes/después:
  `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.
- Derived SHA-256 puntual, no golden:
  `14AD33F882A815DFD7882FE273060ECB2F29B3AF7D03BE3BF679C7B0C10FE17F`.
- Blender GUI/MCP observó `bpy.app.background=false`, `VIEW_3D`, 22 paredes,
  6 openings proxy, floor `8.03 x 5.35 m`, cámara/luz técnicas intactas,
  4 materiales técnicos y 31 objetos totales.
- Anomalía: `get_addon_status` no pudo cargar `blender_mcp.config`; las
  operaciones MCP de escena, viewport y `Save As` sí fueron verificadas.

## T6.02 [x] — First visual furniture pass

- [x] Abrir el source arquitectónico en Blender GUI y capturar el estado inicial
  de root, colecciones, units, cámara y luz técnicas.
- [x] Crear mediante MCP una capa `HSLAYOUT_VISUAL_*` derivada y separada.
- [x] Construir geometría procedural simple y reconocible para sofá, sillón y
  mesa, sin descargar assets.
- [x] Mantener el transform contractual de cada item y comprobar dimensiones,
  footprint, anchor y ausencia de invasión no documentada.
- [x] Aplicar metadata de provenance sintética y ownership por item.
- [x] Guardar solo una copia derivada y obtener captura de viewport.
- [x] **STOP VISUAL:** informar qué cambió, qué debe observarse, estado de
  Blender, captura y limitaciones; esperar feedback humano.

### Evidencia T6.02 — IMPLEMENTED / APPROVED VISUALLY

- Derivada activa y guardada: `blender/scenes/review/2026-09-10-living-room-main-slice-006-visual-v1.blend`.
- Inventario exacto: 22 objetos visuales en `FurnitureVisual` — sofa 8,
  armchair 7, coffee table 7; `ReviewPresentation` permanece vacío.
- Placement autoridad: sofa `[-3.1,1.2]`, `0°`, `[2.2,0.95,0.85]`; armchair
  `[-1.0,1.2]`, `270°`, `[0.8,0.8,0.9]`; coffee table `[-3.1,0.2]`, `90°`,
  `[1.0,0.6,0.4]`.
- Idempotencia comprobada con dos regeneraciones canónicas equivalentes; no
  hay duplicados, sufijos automáticos ni objetos fuera de `FurnitureVisual`.
- El usuario aprobó visualmente los tres muebles, proporciones, placement,
  arquitectura intacta y ausencia de geometría rota. El viewport aprobado final
  quedó en perspectiva 3D elevada y diagonal.
- Source SHA antes/después: `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.
  Derived SHA puntual: `A65F9888D71CCBE2F5908FFB4D21A697F8868C82A6084F32A35BCCFE025B5F66`.
- Gated tests: variant `75/75`, Slice 005 `5/5`, furniture `231/231`, room
  `230/230`, histórico room `37/37`, Python `32`, JSON `11`, privacy/hygiene
  y `git diff --check` PASS. El hygiene global mostró únicamente artefactos
  históricos fuera de T6.02 (`blender/scenes/tests/001-foundation-room.blend1`
  y seis previews anteriores); no se generaron nuevos outputs en esta tarea.
  La aprobación visual de T6.02 queda registrada.

## T6.03 [x] — Materials v1 — IMPLEMENTED / APPROVED VISUALLY

- [x] Crear materiales simples/procedurales para sofá, cojines, sillón y mesa,
  con IDs estables y sin texturas externas; se preservan materiales técnicos de
  arquitectura.
- [x] Asignar materials por semantic role de forma determinista.
- [x] Comprobar base color, roughness, metallic, escala aparente y ausencia de
  materiales accidentales o datablocks duplicados sin ownership.
- [x] Inspeccionar visualmente contraste y legibilidad en el viewport real.
- [x] Registrar los valores realmente usados y su provenance.
- [x] **STOP VISUAL:** devolver captura, asignaciones, observaciones y
  limitaciones; esperar feedback humano.

### Evidencia T6.03 — IMPLEMENTED / APPROVED VISUALLY

- Materiales creados: `hs3d_visual_mat_sofa_v1`,
  `hs3d_visual_mat_sofa_cushion_v1`, `hs3d_visual_mat_armchair_v1`,
  `hs3d_visual_mat_armchair_cushion_v1` y
  `hs3d_visual_mat_coffee_table_wood_v1`.
- Parámetros: sofa `[0.42,0.30,0.22,1]` roughness `0.82`; sofa cushion
  `[0.58,0.43,0.30,1]` `0.86`; armchair `[0.12,0.30,0.34,1]` `0.80`;
  armchair cushion `[0.20,0.45,0.46,1]` `0.84`; coffee table wood
  `[0.34,0.14,0.045,1]` `0.48`; metallic `0.0` en todos.
- Assignments: 19 meshes, una ranura de material por mesh, provenance
  `procedural_synthetic`, semantic roles y metadata `materials-v1` correctos.
- Idempotencia: dos aplicaciones equivalentes, cinco materiales exactos y sin
  datablocks `.001/.002`; nodos únicamente Principled BSDF + Output.
- Source SHA antes/después: `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.
  Derived SHA puntual tras guardar: `2C0DFA489056E1DE426DE470F1EF6DDFA797E508A21A0F540FF5745A70477766`.
- Viewport final: Material Preview, perspectiva elevada diagonal, muebles
  completos, arquitectura contextual y cero selección individual.
- El usuario aprobó visualmente los materiales en Blender GUI; no se requieren
  ajustes antes de T6.04.

## T6.04 [x] — Lighting & review camera v1 — IMPLEMENTED / APPROVED VISUALLY

- [x] Preservar `HS3D_CAMERA` y `HS3D_KEY_LIGHT` de validación; añadir solo
  presentación visual con namespace propio.
- [x] Crear iluminación ligera de review, con
  parámetros deterministas y coste acotado.
- [x] Crear cámara de review reproducible que incluya arquitectura y muebles
  sin clipping ni objetos accidentales.
- [x] Ajustar exposición y encuadre mediante inspección del viewport, no por
  ejecución background ciega.
- [x] Generar un review render ligero en path repo-relative, sin prometer
  igualdad binaria.
- [x] **STOP VISUAL:** devolver render/captura, parámetros, limitaciones y
  cualquier desviación; esperar feedback humano.

### Evidencia T6.04 — IMPLEMENTED / APPROVED VISUALLY

- `ReviewPresentation` estaba vacía y ahora contiene exactamente tres objetos:
  `..._REVIEW_CAMERA_v1`, `..._REVIEW_KEY_AREA_v1` y `..._REVIEW_FILL_AREA_v1`.
  No hay nombres `.001/.002`; la ownership es exclusiva de la colección.
- Cámara: location `[-5.8,-1.0,1.7]`, target `[-2.4,1.1,0.6]`, rotation
  `[1.30219,0,-1.017502]`, focal 35 mm, sensor 36 mm, DOF desactivado.
  Key: `900 W`, size `4.0 m`, location `[-3.6,-0.2,4.6]`; fill: `250 W`,
  size `3.0 m`, location `[-0.5,2.5,2.8]`. World strength `0.32`.
- Blender GUI quedó en `CAMERA` + `RENDERED`, sin selección ni overlays de debug;
  la captura MCP y el render muestran los tres muebles y contexto arquitectónico.
- Render: `renders/previews/living-room-main-slice-006-visual-v1/review-v1.png`,
  `960×720`, SHA puntual pre-sanitización
  `A81BD18990A43AF1ABB5B528A5DCEF3A61D543C9F665EAA4063F8F569A66A0BA`.
  El engine guardado es `BLENDER_EEVEE`, única etiqueta EEVEE disponible en la
  API local; `BLENDER_EEVEE_NEXT` fue rechazado por compatibilidad de Blender.
- Source SHA antes/después:
  `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.
  Derived SHA tras guardar:
  `74EA4AF015C95FADD85EC5007E806A550D9F4E88CCC132E35A274ED3493FAC1D`.
- Arquitectura, furniture transforms, 5 materiales T6.03, `HS3D_CAMERA` y
  `HS3D_KEY_LIGHT` permanecen intactos. La re-aplicación exacta fue idempotente;
  no se generaron decoración, cámara técnica alternativa, `.blend1` final ni
  outputs accidentales.
- STOP VISUAL T6.04: `PASS`; el usuario aprobó cámara interior útil, muebles
  completos y reconocibles, arquitectura contextual, iluminación legible y
  ausencia de clipping funcional invalidante.
- Observaciones no bloqueantes aceptadas: sofá próximo al borde izquierdo,
  apariencia técnica/simple, geometría procedural simple, iluminación clara y
  ausencia de fotorealismo/decoración final. No se corrigieron en T6.05.

## T6.05 [x] — Visual acceptance & reproducibility

- [x] Comparar source antes/después y demostrar que no mutaron arquitectura,
  measurements, layouts, FurniturePlan ni spatial reports.
- [x] Normalizar/inspeccionar roots, collections, ownership, units, transforms,
  materials, camera y lights de la escena derivada.
- [x] Ejecutar regresión pure furniture/room y comprobaciones estructurales
  Blender aplicables.
- [x] Repetir la generación lógica en una copia y comparar inventario,
  transforms, assignments y parámetros; no exigir hash binario.
- [x] Auditar privacidad, provenance, binarios, tamaño, temporales y rollback.
- [x] Obtener viewport y render final, registrar feedback humano y decidir qué
  evidencia se versiona.
- [x] **STOP VISUAL:** no avanzar a T6.06 hasta contar con aceptación humana
  explícita o registrar el gate como bloqueado.

### Evidencia T6.05 — VALIDATED

- GUI/MCP real: Blender `5.2.1 LTS`, `bpy.app.background=false`, `VIEW_3D`,
  addon presente, listener `127.0.0.1:9876`, derivada activa y captura MCP.
- Source intacto con SHA-256
  `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`;
  no se abrió ni guardó como escena de trabajo.
- FurniturePlan `furniture-placement-generator-1`, firma
  `b107d146c81a300858d33d48265d7e42480c88f6ed8443e6a54f80a008e19a0c`:
  transforms, dimensiones, yaw, footprints, IDs, metadata, provenance,
  hierarchy, units y binding correctos para los tres items.
- Arquitectura: 22 walls, 6 opening proxies, floor `8.03×5.35 m`, 0 fixed
  elements, collections y elementos técnicos preservados. Cinco materiales
  visuales exactos, 19 assignments, nodos esperados, sin texturas externas ni
  duplicados. `ReviewPresentation` contiene solo cámara, key y fill.
- Inventario lógico normalizado idéntico en dos lecturas independientes;
  `canonical_length=85096`, fingerprint interno `315456719271`, no golden
  binario. Idempotencia lógica PASS sin duplicados ni residuos.
- Render inspeccionado en T6.05: PNG legible `960×720`, `863031` bytes, SHA
  puntual `A81BD18990A43AF1ABB5B528A5DCEF3A61D543C9F665EAA4063F8F569A66A0BA`
  antes de la sanitización posterior; no se promovió el hash a golden.
- Gates PASS: visual contract `6/6`, variant `75/75`, Slice 005 `5/5`,
  furniture `231/231`, room `230/230`, histórico `37/37`, validadores,
  generation plan, `room_to_plan`, spatial validation, golden v1,
  Python `32`, JSON `11` y `git diff --check`.
- EEVEE: API real expone `BLENDER_EEVEE` y no `BLENDER_EEVEE_NEXT`. La anomalía
  histórica `get_addon_status → No module named 'blender_mcp.config'` permanece
  registrada, sin bloquear las operaciones MCP reales. Privacy/provenance/
  hygiene de escena y diff textual PASS; la metadata no contractual del PNG
  pre-sanitización se detectó y corrigió en la auditoría final de T6.06. T6.06
  permanece `[ ]` en este checkpoint histórico.

## T6.06 [x] — Documentation & final audit

- [x] Crear `docs/setup/006-visual-furnishing-materials-validation.md` con
  evidencia real, paths, versiones, gates, feedback y limitaciones.
- [x] Reconciliar spec/plan/tasks con el comportamiento y no cerrar tareas sin
  evidencia correspondiente.
- [x] Revisar diff completo, privacy, assets/licencias, binarios, temporales,
  source preservation y rollback.
- [x] Ejecutar `git diff --check` y gates proporcionales; marcar controles no
  ejecutados honestamente.
- [x] Confirmar que no hay Slice 007, UI, catálogo, A/B/C visual ni scope creep.
- [x] Dejar la rama lista para PR; la apertura de PR requiere autorización
  posterior y no forma parte automática de esta tarea.

## Acceptance final prevista

- [x] La escena visual es reconocible como `living-room-main`.
- [x] Arquitectura, openings proxy y colecciones `HS3D_ROOM_*` permanecen
  intactos.
- [x] Sofá, sillón y mesa son visualmente distinguibles y están colocados según
  baseline A.
- [x] Materiales de pared, suelo y muebles se distinguen y tienen provenance
  procedural sintética.
- [x] Cámara y luces de review permiten inspeccionar volumen, materiales y
  relación furniture/arquitectura.
- [x] No aparecen geometría rota, objetos accidentales, overlays/debug no
  intencionados ni datos privados en el render.
- [x] Existe evidencia de viewport y review render inspeccionada por el usuario.
- [x] La lógica es reproducible y la escena source queda preservada; no se
  exige igualdad binaria de `.blend` o PNG.

### Evidencia T6.06 — VALIDATED

- Documento final creado en `docs/setup/006-visual-furnishing-materials-validation.md`.
- Auditoría completa de Slice 006, coherencia documental, scope, privacy,
  provenance, hygiene, rollback y gates realizada con evidencia actual.
- README.md y PROJECT_CONTEXT.md solo se actualizaron para corregir la deuda
  factual de Slice 005; no se introdujo Slice 007.
- La auditoría final reprodujo `eXIf` y `tEXt` no contractuales en el PNG previo,
  incluida una ruta absoluta. Se añadió un guard reutilizable al contrato de
  render y su test falló con el artefacto previo antes de pasar con el artefacto
  sanitizado.
- La sanitización byte-level eliminó `eXIf`, `tEXt`, `iTXt` y `zTXt`, preservó
  exactamente `IDAT` y los píxeles, y no generó un render nuevo. El PNG final es
  `960×720`, `862587` bytes, SHA puntual
  `05481687AC98123F571681530AAB7AF4CF76C9DD88485CD1EE7647BC19306594`; no es
  golden. Hash de píxeles antes/después:
  `ed9ca1260baa9b96896ad71fdb048914f318f0a49d9e83b012e4d5ea966bfab6`.
- No se modificaron source/derived `.blend`, geometría, placements, materiales,
  cámara, luces ni la GUI de Blender.
- Gates finales tras la corrección: visual contract `8/8`, variant `75/75`, Slice
  005 `5/5`, furniture discovery `233/233`, room `230/230`, histórico `37/37`,
  validadores/generation plan/`room_to_plan`/spatial `PASS`, golden v1 exacta,
  Python `32`, JSON `11` y `git diff --check` PASS.
- La rama queda preparada para revisión final, sin staging, commit, push ni PR.
