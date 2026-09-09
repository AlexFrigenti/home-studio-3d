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
- Derivar en T6.05, si el usuario acepta y el diff lo incluye: `blender/scenes/review/living-room-main-slice-006-visual-v1.blend`.
- Derivar en T6.04/T6.05, si el usuario acepta: `renders/previews/living-room-main-slice-006-visual-v1/review.png`.
- No crear ahora ninguno de esos artefactos; esta rama contiene solo diseño.

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
- Scene/assets: `No se crean en esta tarea de diseño`; la escena derivada se reserva para T6.02.

**Interfaces:**
- Consume: baseline A, FurniturePlan A, SpatialValidationReport A y source room scene.
- Produce: contrato visual versionado, metadata `hs3d_visual_*`, naming/collection policy, transform authority, material ownership y workflow GUI+MCP.

- [ ] Fijar un contrato visual versionado que registre `room_id`, `layout_id`, plan versions, firmas disponibles, units, coordinate system, source role y derived role.
- [ ] Fijar root `HSLAYOUT_VISUAL_<room_id>_<layout_id>_v1`, colecciones `FurnitureVisual` y `ReviewPresentation`, ownership y reglas de no contaminación de `HS3D_ROOM_*`/`HSLAYOUT_*`.
- [ ] Definir metadata por objeto visual: `item_id`, `source_id`, `dimensions_status`, `visual_role`, `visual_generator_version` y `material_id` cuando exista.
- [ ] Implementar la validación pura de identidad, nombres, unidades, transforms contractuales y provenance sin importar `bpy` al probarla.
- [ ] Ejecutar tests puros y una inspección inicial de la sesión gráfica; no crear todavía furniture visual.
- [ ] Registrar el primer checkpoint de workflow y detenerse si el contrato cambia la estructura observable de la escena.

### T6.02: First visual furniture pass

**Archivos:**
- Modify: `blender/scripts/furniture/generate_furniture_visual.py` únicamente si el contrato de T6.01 lo requiere.
- Test: `tests/furniture/test_furniture_visual_contract.py` para límites e identidad.
- Derived scene: `blender/scenes/review/living-room-main-slice-006-visual-v1.blend` solo mediante Save As en Blender GUI/MCP.

**Interfaces:**
- Consume: source architectural scene, baseline A FurniturePlan y contract de T6.01.
- Produce: root visual derivado con objetos reconocibles de sofá, sillón y mesa, conservando transforms y footprint contractuales.

- [ ] Abrir el source en Blender GUI y verificar units, root `HS3D_ROOM_*`, colecciones y cámara/luz técnicas antes de editar.
- [ ] Crear mediante MCP en la sesión gráfica una colección visual separada y formas locales mínimas de sofá, sillón y mesa.
- [ ] Mantener el origen/placement semántico del item y comprobar que el volumen visual no invade la footprint autorizada sin documentar una excepción.
- [ ] Aplicar ownership y metadata `hs3d_visual_*`; mantener `dimensions_status=synthetic` y source IDs existentes.
- [ ] Guardar únicamente una copia derivada y capturar viewport con los tres muebles distinguibles.
- [ ] **STOP VISUAL OBLIGATORIO:** devolver cambios, observaciones, limitaciones y evidencia; esperar feedback humano antes de T6.03.

### T6.03: Materials v1

**Archivos:**
- Modify: `blender/scripts/furniture/generate_furniture_visual.py` para asignación determinista y reusable.
- Test: `tests/furniture/test_furniture_visual_contract.py` para material IDs, roles y parámetros serializables.
- Derived scene: checkpoint de T6.02 abierto en Blender GUI; no modificar source.

**Interfaces:**
- Consume: escena derivada aceptada en T6.02 y semantic roles del contrato visual.
- Produce: materiales procedurales simples con `material_id`, base color, roughness, metallic y provenance sintética.

- [ ] Crear materiales Principled BSDF simples para pared, suelo, sofá, sillón y mesa con IDs estables.
- [ ] Asignar materiales por rol/item de forma determinista, sin depender de orden incidental de datablocks.
- [ ] Comprobar visualmente diferenciación, escala aparente, ausencia de texturas externas y ausencia de metadata personal.
- [ ] Registrar los valores realmente usados en la evidencia de checkpoint; no inventar valores en documentación posterior.
- [ ] **STOP VISUAL OBLIGATORIO:** devolver viewport, material assignments y limitaciones; esperar feedback humano antes de T6.04.

### T6.04: Lighting & review camera v1

**Archivos:**
- Modify: `blender/scripts/furniture/generate_furniture_visual.py` para parámetros reproducibles de review presentation.
- Test: `tests/furniture/test_furniture_visual_contract.py` para nombres, parámetros y ownership de cámara/luces.
- Derived output: `renders/previews/living-room-main-slice-006-visual-v1/review.png` si el usuario aprueba el render.

**Interfaces:**
- Consume: escena visual/materializada de T6.03.
- Produce: cámara y luces de review en `ReviewPresentation`, con encuadre y exposición reproducibles.

- [ ] Mantener intactos `HS3D_CAMERA` y `HS3D_KEY_LIGHT` técnicos; crear presentación visual con namespace propio.
- [ ] Usar un setup ligero de EEVEE Next para iteración; una key area light y una fill suave como máximo en v1 salvo evidencia que exija otra.
- [ ] Crear cámara de review que muestre arquitectura, sofá, sillón y mesa sin clipping ni elementos fuera de cuadro.
- [ ] Ajustar solo mediante observación del viewport y mediciones de cámara; no perseguir fotorealismo.
- [ ] Generar un review render ligero en ruta repo-relative y revisar visualmente su privacidad y legibilidad.
- [ ] **STOP VISUAL OBLIGATORIO:** devolver render/captura, parámetros y limitaciones; esperar feedback humano antes de T6.05.

### T6.05: Visual acceptance & reproducibility

**Archivos:**
- Modify: `tests/furniture/test_furniture_visual_contract.py` para regresiones estructurales finales.
- Create: `tests/furniture/blender_test_furniture_visual.py` para smoke/normalización estructural si la implementación lo necesita.
- Derived: escena y review render aceptados, sin alterar source.

**Interfaces:**
- Consume: escena derivada completa, baseline A, FurniturePlan, spatial report y evidencias de T6.02–T6.04.
- Produce: acceptance visual humana, inventario lógico reproducible, evidencia de no mutación y decisión de versionado de artefactos.

- [ ] Comparar hash o snapshot del source antes/después y demostrar que `measurements`, layout, FurniturePlan y spatial report no mutaron.
- [ ] Normalizar/inspeccionar la escena derivada y verificar roots, collections, object ownership, units, transforms, materials, camera y lights.
- [ ] Repetir la generación/assignment en una copia derivada y comparar el inventario lógico, no hashes binarios.
- [ ] Ejecutar tests puros, smoke Blender aplicable, privacy scan, `git diff --check` y revisión de binarios/tamaños.
- [ ] Obtener inspección visual final del viewport y render; registrar feedback humano y limitaciones aceptadas.
- [ ] **STOP VISUAL OBLIGATORIO:** no pasar a documentación final sin aceptación humana explícita.

### T6.06: Documentation & final audit

**Archivos:**
- Create: `docs/setup/006-visual-furnishing-materials-validation.md`.
- Modify: `specs/006-visual-furnishing-materials-v1/spec.md`, `plan.md`, `tasks.md` para reflejar solo evidencia real.
- Test/assets/scenes: solo auditoría; no nueva funcionalidad visual.

**Interfaces:**
- Consume: evidencia de T6.01–T6.05, gates, capturas/renders y decisiones de provenance.
- Produce: documentación final, diff listo para PR y estado de tareas cerrado únicamente con evidencia.

- [ ] Reconciliar spec, plan, tasks y setup doc con nombres, versiones, paths y acceptance reales.
- [ ] Registrar gates como `PASS`, `NO APLICA`, `PENDIENTE DE INFRAESTRUCTURA` o `NO EJECUTADO` según evidencia; no inventar checks.
- [ ] Revisar privacidad, licenses, binarios, temporales, source preservation y rollback.
- [ ] Confirmar que no se introdujeron Slice 007, comparación visual A/B/C, assets no aprobados o scope creep.
- [ ] Ejecutar `git diff --check`, revisar el diff completo y preparar PR; no abrirla dentro de la implementación de T6.06 sin autorización separada.

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
