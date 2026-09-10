# Visual Furnishing & Materials v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear una escena visual derivada y humanamente evaluable de `living-room-main` con furniture procedural reconocible, materiales simples, iluminación y cámara de revisión, sin alterar las autoridades de room ni furniture.

**Architecture:** La escena arquitectónica `HS3D_ROOM_*` y el overlay semántico `HSLAYOUT_*` permanecen como capas contractuales. Slice 006 añade un root visual hermano `HSLAYOUT_VISUAL_*` en una escena derivada; los objetos visuales heredan identidad y transforms del `FurniturePlan`, pero su detalle geométrico y material se mantiene separado. Las tareas visuales se ejecutan en Blender 5.2.1 gráfico mediante MCP local, con tests y background solo como soporte estructural.

**Tech Stack:** Blender 5.2.1 LTS, Blender MCP en `127.0.0.1:9876`, Python/bpy inspeccionado, FurniturePlan `furniture-placement-generator-1`, SpatialValidationReport `furniture-spatial-validation-1`, room plan `room-v1.1-generator-2`, JSON repo-relative y materiales Principled BSDF simples.

**Spec:** `specs/006-visual-furnishing-materials-v1/spec.md`

## Global Constraints

- Clasificación: T2 por cambios visuales, uso privilegiado de Blender/MCP, artefactos binarios derivados y provenance.
- `measurements/` sigue siendo la autoridad arquitectónica; Blender no redefine medidas.
- Units: `m`; coordinate system: `canonical_room`.
- Source scene: `blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend`; nunca sobrescribirla.
- T6.01 derived checkpoint: `blender/scenes/review/2026-09-10-living-room-main-slice-006-visual-v1.blend`, creado solo mediante `Save As` en la GUI.
- Layout authority: `layouts/living-room-main/variants/baseline-a.json`; no modificarlo.
- `HS3D_ROOM_*` y el overlay semántico `HSLAYOUT_*` existentes permanecen compatibles.
- La capa visual será derivada, separable, regenerable y con nombres/metadata deterministas.
- T6.02–T6.05 requieren Blender GUI abierta, MCP local y STOP VISUAL humano; un test verde no cierra una fase artística.
- No assets externos, fabricantes, texturas externas, secretos, rutas absolutas ni datos personales en v1.
- No se promete determinismo binario de `.blend` o PNG; sí determinismo lógico de inventario, transforms contractuales, materiales, cámara y luces.
- No iniciar Slice 007 ni ampliar a comparación visual A/B/C, catálogo, ergonomía o fotorealismo.

## Mapa de archivos y artefactos futuros

Durante la implementación futura, cada archivo tendrá una responsabilidad clara:

- Crear: `blender/scripts/furniture/generate_furniture_visual.py` para la especificación determinista de la capa visual y operaciones pequeñas invocables desde la sesión gráfica.
- Crear: `tests/furniture/test_furniture_visual_contract.py` para invariantes puras de identidad, ownership, material assignment y transform authority.
- Crear: `tests/furniture/blender_test_furniture_visual.py` solo para smoke/normalización estructural ejecutable en Blender; no sustituye la inspección GUI.
- Crear en T6.06: `docs/setup/006-visual-furnishing-materials-validation.md` con evidencia final y limitaciones.
- El checkpoint estructural T6.01 ya existe en `blender/scenes/review/2026-09-10-living-room-main-slice-006-visual-v1.blend`; T6.02 añade únicamente furniture visual procedural a esa copia mediante Blender GUI/MCP.
- Derivar en T6.04/T6.05, si el usuario acepta: `renders/previews/living-room-main-slice-006-visual-v1/review-v1.png`.
- T6.02 no crea todavía materiales artísticos, luces/cámara de review ni renders; esos artefactos siguen reservados para T6.03–T6.04.

## Flujo de trabajo visual obligatorio

Cada fase visual seguirá este ciclo, sin pasar automáticamente el STOP:

1. Ejecutar gates puros de entrada y confirmar el FurniturePlan esperado.
2. Abrir/seleccionar la sesión gráfica de Blender 5.2.1 y verificar que MCP
   está en `127.0.0.1:9876`.
3. Inspeccionar la escena y la acción prevista antes de usar `bpy`.
4. Aplicar una operación acotada mediante MCP y observar el viewport real.
5. Comprobar numéricamente transforms, ownership y unidades.
6. Guardar como derivado si se alcanza un checkpoint estable; nunca guardar
   sobre source.
7. Capturar la evidencia exigida.
8. Detenerse y devolver cambios, observaciones, limitaciones y estado Blender.
9. Esperar feedback humano antes de la siguiente fase.

## Tareas

### T6.01: Visual scene contract & Blender live workflow

**Archivos:**
- Modify: `specs/006-visual-furnishing-materials-v1/spec.md`, `plan.md`, `tasks.md` si el contrato aprobado requiere precisión adicional.
- Create: `blender/scripts/furniture/generate_furniture_visual.py` en la implementación de T6.01.
- Test: `tests/furniture/test_furniture_visual_contract.py`.
- Scene/assets: se crea únicamente el checkpoint derivado indicado arriba; no contiene furniture visual ni presentación artística.

**Interfaces:**
- Consume: baseline A, FurniturePlan A, SpatialValidationReport A y source room scene.
- Produce: contrato visual versionado, metadata `hs3d_visual_*`, naming/collection policy, transform authority, material ownership y workflow GUI+MCP.

- [x] Fijar un contrato visual versionado que registre `room_id`, `layout_id`, plan versions, firmas disponibles, units, coordinate system, source role y derived role.
- [x] Fijar root `HSLAYOUT_VISUAL_<room_id>_<layout_id>_v1`, colecciones `FurnitureVisual` y `ReviewPresentation`, ownership y reglas de no contaminación de `HS3D_ROOM_*`/`HSLAYOUT_*`.
- [x] Definir metadata por objeto visual: `item_id`, `source_id`, `dimensions_status`, `visual_role`, `visual_generator_version` y `material_id` cuando exista.
- [x] Implementar la validación pura de identidad, nombres, unidades, transforms contractuales y provenance sin importar `bpy` al probarla.
- [x] Ejecutar tests puros y una inspección inicial de la sesión gráfica; no crear todavía furniture visual.
- [x] Registrar el primer checkpoint de workflow y detenerse si el contrato cambia la estructura observable de la escena.

#### Evidencia T6.01

- `Save As` se ejecutó en Blender GUI/MCP sobre el source con resultado `FINISHED`; Blender quedó sobre la derivada y `bpy.app.background=false`.
- El root visual usa el `layout_id` real `slice-005-acceptance-baseline-a`. Las collections visuales están vacías y separadas del root `HS3D_ROOM_living-room-main`.
- Room plan: `room-v1.1-generator-2`; room logical signature:
  `182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a`.
- Source SHA-256 antes/después:
  `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.
  Derived SHA-256 puntual:
  `14AD33F882A815DFD7882FE273060ECB2F29B3AF7D03BE3BF679C7B0C10FE17F`.
- Viewport real inspeccionado antes y después; 31 objetos arquitectónicos/técnicos,
  22 walls, 6 openings, floor y transforms sin incidencias, 4 materiales
  técnicos, cero objetos visuales y cero outputs de render.
- `get_addon_status` quedó como anomalía de infraestructura por
  `No module named 'blender_mcp.config'`; las operaciones live usadas para
  la evidencia sí respondieron desde la sesión gráfica real.

### T6.02: First visual furniture pass

**Archivos:**
- Modify: `blender/scripts/furniture/generate_furniture_visual.py` únicamente si el contrato de T6.01 lo requiere.
- Test: `tests/furniture/test_furniture_visual_contract.py` para límites e identidad.
- Derived scene: checkpoint `blender/scenes/review/2026-09-10-living-room-main-slice-006-visual-v1.blend`, solo mediante Save As en Blender GUI/MCP.

**Interfaces:**
- Consume: source architectural scene, baseline A FurniturePlan y contract de T6.01.
- Produce: root visual derivado con objetos reconocibles de sofá, sillón y mesa, conservando transforms y footprint contractuales.

- [x] Abrir el source en Blender GUI y verificar units, root `HS3D_ROOM_*`, colecciones y cámara/luz técnicas antes de editar.
- [x] Crear mediante MCP en la sesión gráfica una colección visual separada y formas locales mínimas de sofá, sillón y mesa.
- [x] Mantener el origen/placement semántico del item y comprobar que el volumen visual no invade la footprint autorizada sin documentar una excepción.
- [x] Aplicar ownership y metadata `hs3d_visual_*`; mantener `dimensions_status=synthetic` y source IDs existentes.
- [x] Guardar únicamente una copia derivada y capturar viewport con los tres muebles distinguibles.
- [x] **STOP VISUAL OBLIGATORIO:** devolver cambios, observaciones, limitaciones y evidencia; esperar feedback humano antes de T6.03.

#### Evidencia real T6.02 — IMPLEMENTED / APPROVED VISUALLY

- FurniturePlan autoridad: `baseline-a.json`, versión `furniture-placement-generator-1`, firma `b107d146c81a300858d33d48265d7e42480c88f6ed8443e6a54f80a008e19a0c`.
- Inventario: 22 objetos visuales exactos bajo `FurnitureVisual` — sofa 8 objetos incluyendo root, armchair 7 y coffee table 7; `ReviewPresentation` 0.
- Roots deterministas: `HSLAYOUT_VISUAL_living-room-main_slice-005-acceptance-baseline-a_{sofa,armchair,coffee_table}`. Todos los hijos usan el mismo namespace y metadata de item.
- Bounds locales verificadas: sofa `[-1.05,-0.45,0]..[1.05,0.45,0.85]`; armchair `[-0.39,-0.35,0]..[0.39,0.37,0.9]`; coffee table `[-0.47,-0.27,0]..[0.47,0.27,0.4]`; todas dentro del envelope contractual.
- Idempotencia: dos ciclos de regeneración canónica equivalentes, sin duplicados, sufijos `.001/.002` ni objetos fuera de `FurnitureVisual`.
- Materiales visuales asignados: ninguno. Cámaras/luces visuales: ninguna. Materiales técnicos: cuatro `HS3D_MAT_*` intactos.
- Source intacto antes/después con SHA `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`. Derived SHA puntual tras guardar: `A65F9888D71CCBE2F5908FFB4D21A697F8868C82A6084F32A35BCCFE025B5F66`.
- El usuario aprobó visualmente T6.02: muebles reconocibles, proporciones aceptables, placement coherente y arquitectura intacta.

### T6.03: Materials v1

**Archivos:**
- Modify: `blender/scripts/furniture/generate_furniture_visual.py` para asignación determinista y reusable.
- Test: `tests/furniture/test_furniture_visual_contract.py` para material IDs, roles y parámetros serializables.
- Derived scene: checkpoint de T6.02 abierto en Blender GUI; no modificar source.

**Interfaces:**
- Consume: escena derivada aceptada en T6.02 y semantic roles del contrato visual.
- Produce: materiales procedurales simples con `material_id`, base color, roughness, metallic y provenance sintética.

- [x] Crear cinco materiales Principled BSDF simples para sofá, cojines, sillón y mesa con IDs estables; se preservan los materiales técnicos de pared/suelo.
- [x] Asignar materiales por rol/item de forma determinista, sin depender de orden incidental de datablocks.
- [x] Comprobar visualmente diferenciación, escala aparente, ausencia de texturas externas y ausencia de metadata personal.
- [x] Registrar los valores realmente usados en la evidencia de checkpoint; no inventar valores en documentación posterior.
- [x] **STOP VISUAL OBLIGATORIO:** devolver viewport, material assignments y limitaciones; esperar feedback humano antes de T6.04.

#### Evidencia real T6.03 — IMPLEMENTED / APPROVED VISUALLY

- Se crearon cinco materiales bajo `HSLAYOUT_VISUAL_*`: `hs3d_visual_mat_sofa_v1`, `hs3d_visual_mat_sofa_cushion_v1`, `hs3d_visual_mat_armchair_v1`, `hs3d_visual_mat_armchair_cushion_v1` y `hs3d_visual_mat_coffee_table_wood_v1`.
- Parámetros deterministas: sofa `[0.42,0.30,0.22,1]`/roughness `0.82`; sofa cushion `[0.58,0.43,0.30,1]`/`0.86`; armchair `[0.12,0.30,0.34,1]`/`0.80`; armchair cushion `[0.20,0.45,0.46,1]`/`0.84`; coffee table wood `[0.34,0.14,0.045,1]`/`0.48`; todos metallic `0.0`.
- Assignments verificados: 19 meshes, un material por mesh, cojines diferenciados y mesa completa en madera. Metadata `semantic_role`, `materials-v1`, `procedural_synthetic`, base color, roughness y metallic materializada.
- Idempotencia: dos aplicaciones consecutivas equivalentes; cinco materiales exactos, sin `.001/.002`, nodos externos ni imágenes.
- Technical materials `HS3D_MAT_*`, transforms contractuales y arquitectura permanecen intactos. `ReviewPresentation` sigue vacío.
- Viewport final: `Material Preview`, perspectiva elevada diagonal aprobada, arquitectura contextual y cero selección individual.
- Source SHA antes/después: `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`. Derived SHA puntual: `2C0DFA489056E1DE426DE470F1EF6DDFA797E508A21A0F540FF5745A70477766`.
- El usuario aprobó visualmente T6.03 en Blender GUI; no se requieren ajustes de
  geometría, color o shaders antes de evaluar iluminación.

### T6.04: Lighting & review camera v1 — APPROVED VISUALLY

**Archivos:**
- Modify: `spec.md`, `plan.md` y `tasks.md` únicamente para registrar evidencia real.
- Derived scene: `blender/scenes/review/2026-09-10-living-room-main-slice-006-visual-v1.blend`, guardada desde Blender GUI/MCP.
- Output: `renders/previews/living-room-main-slice-006-visual-v1/review-v1.png`.

**Interfaces:**
- Consume: escena visual/materializada de T6.03.
- Produce: cámara y luces de review en `ReviewPresentation`, con encuadre y exposición reproducibles.

- [x] Mantener intactos `HS3D_CAMERA` y `HS3D_KEY_LIGHT` técnicos; crear presentación visual con namespace propio.
- [x] Usar un setup ligero de EEVEE; una key area light y una fill suave con parámetros deterministas.
- [x] Crear cámara de review que muestre arquitectura, sofá, sillón y mesa sin clipping ni elementos fuera de cuadro.
- [x] Ajustar solo mediante observación del viewport y mediciones de cámara; no perseguir fotorealismo.
- [x] Generar un review render ligero en ruta repo-relative y revisar visualmente su privacidad y legibilidad.
- [x] **STOP VISUAL OBLIGATORIO:** devolver render/captura, parámetros y limitaciones; esperar feedback humano antes de T6.05.

#### Evidencia real T6.04 — IMPLEMENTED / APPROVED VISUALLY

- `ReviewPresentation` pasó de 0 a 3 objetos exactos: cámara de review, key
  area y fill area. Todos pertenecen exclusivamente a la colección y llevan
  `hs3d_visual_role`, `hs3d_visual_owner`, namespace, versión de presentación y
  provenance `procedural_synthetic`.
- Cámara final: `[-5.8,-1.0,1.7]`, target `[-2.4,1.1,0.6]`, Euler
  `[1.30219,0,-1.017502]`, 35 mm, sensor 36 mm, DOF off. La captura MCP final
  quedó en `CAMERA` + `RENDERED`, sin selección ni overlays de debug.
- Key/fill: `900 W`/`4.0 m` y `250 W`/`3.0 m`, respectivamente; world neutral
  controlado con strength `0.32`. La API local de Blender solo expuso
  `BLENDER_EEVEE`, por lo que se usó ese identificador en lugar de
  `BLENDER_EEVEE_NEXT`; queda registrado como anomalía de compatibilidad.
- Render único `renders/previews/living-room-main-slice-006-visual-v1/review-v1.png`,
  `960×720`, SHA puntual pre-sanitización
  `A81BD18990A43AF1ABB5B528A5DCEF3A61D543C9F665EAA4063F8F569A66A0BA`.
- Source intacto antes/después con SHA
  `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`;
  derivada guardada con SHA puntual
  `74EA4AF015C95FADD85EC5007E806A550D9F4E88CCC132E35A274ED3493FAC1D`.
- Invariantes PASS: 22 walls, 6 openings, floor `8.03 × 5.35 m`, furniture
  roots y yaw contractuales, 5 materiales visuales T6.03, 4 `HS3D_MAT_*`,
  `HS3D_CAMERA` y `HS3D_KEY_LIGHT`; cero nombres `.001/.002`.
- Visual human approval T6.04: `PASS`; el usuario confirmó cámara interior útil,
  muebles completos y reconocibles, arquitectura contextual, iluminación legible
  y ausencia de clipping funcional invalidante.
- Observaciones no bloqueantes aceptadas: sofá próximo al borde izquierdo,
  apariencia técnica/simple, geometría procedural simple, iluminación clara y
  ausencia de fotorealismo/decoración final. No se corrigieron en T6.05.

### T6.05: Visual acceptance & reproducibility — VALIDATED

**Archivos:**
- Modify: `tests/furniture/test_furniture_visual_contract.py` para regresiones estructurales finales.
- Create: `tests/furniture/blender_test_furniture_visual.py` para smoke/normalización estructural si la implementación lo necesita.
- Derived: escena y review render aceptados, sin alterar source.

**Interfaces:**
- Consume: escena derivada completa, baseline A, FurniturePlan, spatial report y evidencias de T6.02–T6.04.
- Produce: acceptance visual humana, inventario lógico reproducible, evidencia de no mutación y decisión de versionado de artefactos.

- [x] Comparar hash o snapshot del source antes/después y demostrar que `measurements`, layout, FurniturePlan y spatial report no mutaron.
- [x] Normalizar/inspeccionar la escena derivada y verificar roots, collections, object ownership, units, transforms, materials, camera y lights.
- [x] Repetir la generación/assignment en una copia derivada y comparar el inventario lógico, no hashes binarios.
- [x] Ejecutar tests puros, smoke Blender aplicable, privacy scan, `git diff --check` y revisión de binarios/tamaños.
- [x] Obtener inspección visual final del viewport y render; registrar feedback humano y limitaciones aceptadas.
- [x] **STOP VISUAL OBLIGATORIO:** no pasar a documentación final sin aceptación humana explícita.

#### Evidencia real T6.05 — VALIDATED

- Preflight GUI/MCP: Blender `5.2.1 LTS`, `bpy.app.background=false`,
  `VIEW_3D`, addon presente en preferencias, listener exclusivo
  `127.0.0.1:9876`, escena derivada activa y captura de viewport MCP obtenida.
- Source protegido: SHA-256 exacto
  `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.
  No se abrió ni guardó el source.
- FurniturePlan authority: versión `furniture-placement-generator-1`, firma
  `b107d146c81a300858d33d48265d7e42480c88f6ed8443e6a54f80a008e19a0c`; los
  tres items pasaron IDs, transforms, dimensiones, yaw, footprint, hierarchy,
  metadata, provenance, unidades, coordinate system y binding.
- Architecture non-mutation: 22 walls, 6 opening proxies, floor `8.03×5.35 m`,
  0 fixed elements, hierarchy preservada, `HS3D_CAMERA`, `HS3D_KEY_LIGHT` y
  `HS3D_MAT_DOOR_PROXY`, `HS3D_MAT_FLOOR`, `HS3D_MAT_WALL`,
  `HS3D_MAT_WINDOW_PROXY` preservados.
- Material contract: cinco IDs aprobados, parámetros exactos, nodos Principled
  esperados, 19 assignments, sin imágenes/texturas externas ni `.001/.002`.
  ReviewPresentation: exactamente review camera, key y fill; ownership y
  metadata correctos; cero objetos de presentación fuera y cero debug.
- Inventario lógico normalizado: dos lecturas independientes idénticas;
  `canonical_length=85096`, fingerprint interno `315456719271`, sin usar hash
  binario como golden. Idempotencia lógica PASS por nombres/cantidades exactos,
  sin colecciones, objetos, materiales, assignments, luces, cámaras o residuos
  duplicados.
- Render inspeccionado en T6.05: PNG legible en
  `renders/previews/living-room-main-slice-006-visual-v1/review-v1.png`,
  `960×720`, `863031` bytes, SHA puntual
  `A81BD18990A43AF1ABB5B528A5DCEF3A61D543C9F665EAA4063F8F569A66A0BA` antes
  de la sanitización posterior; no se promovió el hash a golden.
- Regression gates: visual contract `6/6`; variant `75/75`; Slice 005 `5/5`;
  furniture `231/231`; room baseline `230/230`; histórico `37/37`; validadores,
  generation plan, `room_to_plan` y spatial validation PASS; golden v1 exacta
  `1105946a0dfe0088f5ad59da4178939644305b0d09b94022bfe5c87d9dde36f0`;
  Python `32`, JSON `11`, `git diff --check` PASS.
- EEVEE API: Blender 5.2.1 expone `BLENDER_EEVEE` y no expone
  `BLENDER_EEVEE_NEXT`; se registra como nomenclatura/API. La anomalía
  `get_addon_status → No module named 'blender_mcp.config'` permanece documentada
  y no bloquea las operaciones MCP reales.
- Privacy/provenance/hygiene de escena y diff textual: PASS; provenance visual
  `procedural_synthetic`, sin secretos, UUIDs accidentales, fabricantes,
  assets/texturas externos, caches tracked, temporales, `.blend1` nuevos ni
  renders accidentales. La metadata no contractual del PNG pre-sanitización se
  detectó y corrigió en la auditoría final de T6.06. T6.06 no se inicia todavía.

### T6.06: Documentation & final audit — VALIDATED

**Archivos:**
- Create: `docs/setup/006-visual-furnishing-materials-validation.md`.
- Modify: `specs/006-visual-furnishing-materials-v1/spec.md`, `plan.md`, `tasks.md` para reflejar solo evidencia real.
- Test/assets/scenes: solo auditoría; no nueva funcionalidad visual.

**Interfaces:**
- Consume: evidencia de T6.01–T6.05, gates, capturas/renders y decisiones de provenance.
- Produce: documentación final, diff listo para PR y estado de tareas cerrado únicamente con evidencia.

- [x] Reconciliar spec, plan, tasks y setup doc con nombres, versiones, paths y acceptance reales.
- [x] Registrar gates como `PASS`, `NO APLICA`, `PENDIENTE DE INFRAESTRUCTURA` o `NO EJECUTADO` según evidencia; no inventar checks.
- [x] Revisar privacidad, licenses, binarios, temporales, source preservation y rollback.
- [x] Confirmar que no se introdujeron Slice 007, comparación visual A/B/C, assets no aprobados o scope creep.
- [x] Ejecutar `git diff --check`, revisar el diff completo y preparar PR; no abrirla dentro de la implementación de T6.06 sin autorización separada.

#### Evidencia real T6.06 — VALIDATED

- Documento creado: `docs/setup/006-visual-furnishing-materials-validation.md`.
- `spec.md`, `plan.md` y `tasks.md` reconciliados con los artefactos y estados
  reales de T6.01–T6.06; no se añadió funcionalidad visual.
- Diff completo y paths auditados: solo documentación de Slice 006 modificada,
  con la escena, script, test y preview acumulados esperados; sin staging.
- Privacy, provenance, assets/licencias, binarios, temporales, source protection,
  rollback y scope auditados. README.md y PROJECT_CONTEXT.md solo se ajustan
  para corregir el estado heredado de Slice 005 y declarar que no existe Slice 007.
- `git diff --check` y todos los gates proporcionales pasan. La rama queda lista
  para revisión final; commit, push y PR permanecen fuera de esta tarea.
- La auditoría final reprodujo metadata PNG no contractual (`eXIf` y `tEXt`, con
  una ruta absoluta). El guard de privacidad añadido a
  `generate_furniture_visual.py` y cubierto por
  `test_furniture_visual_contract.py` dio RED con el artefacto previo y GREEN
  después de sanitizarlo byte-level.
- La sanitización eliminó `eXIf`, `tEXt`, `iTXt` y `zTXt`, preservó `IDAT` y no
  requirió rerender. El PNG final conserva `960×720`, mide `862587` bytes y su
  SHA puntual es
  `05481687AC98123F571681530AAB7AF4CF76C9DD88485CD1EE7647BC19306594`; el hash
  es evidencia puntual, no golden.
- Hash de píxeles antes/después:
  `ed9ca1260baa9b96896ad71fdb048914f318f0a49d9e83b012e4d5ea966bfab6`.
  Hash de `IDAT` antes/después:
  `d0d44dee1c9aa171022f0252c32dbd2e690215ee6b999efd87e4b98a35558d20`.
  La corrección no modificó Blender, la escena derivada, el source ni ningún
  parámetro visual.
- Gates finales tras la corrección: visual contract `8/8`, variant `75/75`, Slice
  005 `5/5`, furniture discovery `233/233`, room `230/230`, histórico `37/37`,
  validadores/generation plan/`room_to_plan`/spatial `PASS`, golden v1 exacta,
  Python `32`, JSON `11` y `git diff --check` PASS.

## Gates previstos

Los gates se ejecutarán proporcionalmente en cada tarea. La selección mínima
final es:

- pure furniture/room regression: `PASS` si se ejecuta y conserva baseline;
- visual scene structure: `PASS` solo con inspección/normalización real;
- Blender GUI/MCP checkpoint: `PASS` solo con evidencia de sesión y observación;
- source hash/preservation: `PASS` si el source permanece byte/semánticamente intacto;
- dimensions/transforms/units: `PASS` con comprobación numérica;
- material/camera/light inspection: `PASS` con viewport/render revisado;
- privacy/provenance/assets: `PASS` con auditoría real;
- binary/render determinism: `NO APLICA` como igualdad exacta salvo que se demuestre;
- `git diff --check`: `PASS`.

## Gates ejecutados para T6.01

- Variant comparison: `75/75 PASS`.
- Slice 005 acceptance: `5/5 PASS`.
- Furniture full: `231/231 PASS` tras añadir el contrato visual puro.
- Room baseline: `230/230 PASS`; histórico v1: `37/37 PASS`.
- Python syntax: `32` archivos compilados sin escribir bytecode.
- JSON syntax: `11` archivos válidos.
- Blender GUI/MCP: `PASS` para lectura, viewport, estructura, transforms y Save As; el endpoint `get_addon_status` queda `PENDIENTE DE INFRAESTRUCTURA` por el error de módulo indicado arriba.
- Source preservation: `PASS`; el source conserva su SHA-256 antes/después.
- Derived scene: `PASS` como archivo existente y abrible en la GUI; su SHA se registra solo como evidencia puntual.
- Privacy/hygiene: `PASS`, sin rutas privadas, credenciales ni outputs accidentales.
- `git diff --check`: `PASS` (código 0; solo avisos de normalización LF/CRLF).

## Gates ejecutados para T6.02

- Blender GUI/MCP live workflow: `PASS`; sesión visible, `bpy.app.background=false`, ruta derivada activa y viewport capturado.
- Visual structure: `PASS`; 22 objetos, hierarchy por item, ownership `FurnitureVisual`, bounds y metadata verificadas.
- Controlled regeneration/idempotence: `PASS`; dos inventarios canónicos equivalentes, sin sufijos ni residuos.
- Architecture protection: `PASS`; 22 walls, 6 openings, floor, `HS3D_CAMERA`, `HS3D_KEY_LIGHT` y cuatro materiales técnicos sin cambios observables.
- Source protection: `PASS`; source conserva el SHA-256 contractual antes/después.
- Derived scene: `PASS` como archivo existente y guardado desde Blender GUI; SHA solo como evidencia puntual, no golden.
- Visual human approval: `PASS`; el usuario aprobó visualmente T6.02 en Blender GUI.
- Variant comparison: `75/75 PASS`; Slice 005 acceptance: `5/5 PASS`.
- Furniture full: `231/231 PASS`; room baseline: `230/230 PASS`; histórico room v1: `37/37 PASS`.
- Python syntax: `32` archivos válidos; JSON syntax: `11` archivos válidos.
- Privacy/hygiene: `PASS` en el alcance de T6.02; no se generaron rutas privadas,
  secretos, renders ni backups nuevos. Permanecen artefactos históricos fuera del
  alcance de esta tarea: `blender/scenes/tests/001-foundation-room.blend1` y seis
  previews existentes de Slices 001/002/004/005 bajo `renders/previews/`.
- `git diff --check`: `PASS` (código 0; solo avisos de normalización LF/CRLF).

## Gates ejecutados para T6.03

- Blender GUI/MCP live workflow: `PASS`; derivada activa, `bpy.app.background=false`,
  `Material Preview`, perspectiva elevada y captura MCP obtenida.
- Material contract: `PASS`; cinco materiales con IDs, semantic roles, base color,
  roughness, metallic, scene version y `procedural_synthetic`.
- Material assignments: `PASS`; 19 meshes con una asignación determinista cada uno.
- Material idempotence: `PASS`; dos aplicaciones consecutivas equivalentes, cinco
  materiales exactos, sin `.001/.002`, nodos externos ni imágenes.
- Transform/architecture protection: `PASS`; roots contractuales, 22 walls, 6
  openings, floor, cámara/luz técnicas y cuatro `HS3D_MAT_*` intactos.
- Source protection: `PASS`; source SHA antes/después `352FDC...178280`.
- Derived scene: `PASS`; guardada únicamente mediante Blender GUI/MCP; SHA puntual
  `2C0DFA489056E1DE426DE470F1EF6DDFA797E508A21A0F540FF5745A70477766`.
- Visual human approval T6.03: `PASS`; el usuario aprobó color, contraste,
  diferenciación y lectura en Material Preview.
- Regression suites: variant `75/75 PASS`, Slice 005 `5/5 PASS`, furniture `231/231 PASS`,
  room `230/230 PASS`, histórico room `37/37 PASS`.
- Python syntax: `32` archivos válidos; JSON syntax: `11` archivos válidos.
- Privacy/hygiene: `PASS` en el alcance; cero renders T6.03 y cero `.blend1` en la
  carpeta review; las coincidencias de rutas en tres tests/docs son marcadores de
  privacidad intencionales, no rutas privadas de la escena.
- `git diff --check`: `PASS` (código 0; solo avisos de normalización LF/CRLF).

## Gates ejecutados para T6.04

- Blender GUI/MCP live workflow: `PASS`; sesión gráfica real, `bpy.app.background=false`,
  derivada activa, `VIEW_3D` en `CAMERA` + `RENDERED`, captura MCP final y cero selección.
- ReviewPresentation ownership: `PASS`; exactamente tres objetos bajo la colección,
  con namespace `HSLAYOUT_VISUAL_*`, sin objetos nuevos fuera de scope.
- Lighting/camera contract: `PASS`; key/fill deterministas, cámara con target,
  lens, sensor y clipping explícitos, y world controlado.
- Render: `PASS`; PNG único en ruta repo-relative, `960×720`, inspeccionado como
  imagen y no tratado como golden binario. Render SHA puntual pre-sanitización:
  `A81BD18990A43AF1ABB5B528A5DCEF3A61D543C9F665EAA4063F8F569A66A0BA`.
- EEVEE Next: `NO DISPONIBLE EN LA API LOCAL`; Blender 5.2.1 expuso el enum
  `BLENDER_EEVEE`, que fue usado y documentado. No se ejecutó background/headless.
- Transform/architecture/material protection: `PASS`; 22 walls, 6 openings,
  floor, FurnitureVisual, 5 materiales T6.03, 4 `HS3D_MAT_*`, `HS3D_CAMERA`,
  `HS3D_KEY_LIGHT` y roots contractuales sin cambios observables.
- Idempotencia lógica: `PASS`; la re-aplicación de setup conservó tres nombres
  exactos, sin `.001/.002` ni residuos.
- Source protection: `PASS`; source antes/después
  `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`.
- Derived scene: `PASS`; guardada únicamente mediante Blender GUI/MCP, SHA puntual
  `74EA4AF015C95FADD85EC5007E806A550D9F4E88CCC132E35A274ED3493FAC1D`.
- Regression suites: variant comparison `75/75 PASS`, Slice 005 acceptance `5/5 PASS`,
  furniture `231/231 PASS`, room `230/230 PASS`, histórico room `37/37 PASS`,
  visual contract `6/6 PASS`.
- Syntax: Python `32` y JSON `11` válidos; `git diff --check` `PASS` (código 0,
  solo avisos de normalización LF/CRLF).
- Privacy/hygiene: `PASS`; no hay secretos ni rutas privadas en outputs nuevos,
  solo un fixture histórico intencional con rutas de prueba; no quedan `.blend1`
  ni renders accidentales bajo `blender/scenes/review`.
- Visual human approval T6.04: `PASS`; el usuario aprobó la cámara interior,
  muebles completos y reconocibles, arquitectura contextual, iluminación legible
  y ausencia de clipping funcional invalidante. Las observaciones de sofá próximo
  al borde izquierdo, apariencia técnica/simple, iluminación clara y ausencia de
  fotorealismo/decoración final son no bloqueantes y no se corrigieron.

Un gate visual no puede marcarse `PASS` por una suite pure o por una ejecución
background sin inspección gráfica.

## Reversión y compatibilidad

Cada tarea visual debe trabajar en una copia derivada. Si una iteración falla,
se descarta o se vuelve al checkpoint anterior y se regenera desde el source.
La reversión Git cubre scripts, tests y documentación; la reversión de escena
usa Save As/checkpoints. No se eliminan ni sobrescriben escenas canónicas. Los
contratos T4/T5 siguen siendo inputs y no se migran dentro de Slice 006.

## Dependencias externas

- Blender 5.2.1 LTS ya validado en el entorno.
- Blender MCP ya validado y limitado a `127.0.0.1:9876`.
- No se requiere descargar paquetes, addons, assets o servicios externos.
