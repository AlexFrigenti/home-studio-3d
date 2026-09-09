# Tareas: Visual Furnishing & Materials v1

Estados: `[ ]` pendiente · `[~]` en curso · `[x]` validada · `[!]` bloqueada.

> Diseño publicado desde `main` después del merge de Slice 005. Esta rama
> contiene únicamente documentación; ninguna tarea T6.x está implementada.

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

## T6.01 [ ] — Visual scene contract & Blender live workflow

- [ ] Fijar la versión del contrato visual, source/derived paths, units,
  coordinate system y baseline A.
- [ ] Fijar roots y ownership: `HS3D_ROOM_*` intacto, `HSLAYOUT_*` semántico
  intacto y `HSLAYOUT_VISUAL_*` como root visual hermano.
- [ ] Fijar colecciones visuales `FurnitureVisual` y `ReviewPresentation`,
  nombres deterministas y metadata `hs3d_visual_*`.
- [ ] Fijar que `item_id`, `source_id`, `dimensions_status`, transforms,
  footprint y firmas proceden del FurniturePlan; la forma visual es detalle.
- [ ] Fijar material contract mínimo: `material_id`, `semantic_role`,
  `base_color`, `roughness`, `metallic`, `provenance`.
- [ ] Definir rollback mediante Save As/checkpoints y prohibir sobrescribir el
  source.
- [ ] Confirmar el workflow Codex → MCP → Blender GUI → inspección y el primer
  STOP antes de crear muebles visuales.
- [ ] Validación: revisión documental, gates pure de entrada y comprobación de
  que no se modifican T4/T5.

## T6.02 [ ] — First visual furniture pass

- [ ] Abrir el source arquitectónico en Blender GUI y capturar el estado inicial
  de root, colecciones, units, cámara y luz técnicas.
- [ ] Crear mediante MCP una capa `HSLAYOUT_VISUAL_*` derivada y separada.
- [ ] Construir geometría procedural simple y reconocible para sofá, sillón y
  mesa, sin descargar assets.
- [ ] Mantener el transform contractual de cada item y comprobar dimensiones,
  footprint, anchor y ausencia de invasión no documentada.
- [ ] Aplicar metadata de provenance sintética y ownership por item.
- [ ] Guardar solo una copia derivada y obtener captura de viewport.
- [ ] **STOP VISUAL:** informar qué cambió, qué debe observarse, estado de
  Blender, captura y limitaciones; esperar feedback humano.

## T6.03 [ ] — Materials v1

- [ ] Crear materiales simples/procedurales para paredes, suelo, sofá, sillón
  y mesa, con IDs estables y sin texturas externas.
- [ ] Asignar materials por semantic role de forma determinista.
- [ ] Comprobar base color, roughness, metallic, escala aparente y ausencia de
  materiales accidentales o datablocks duplicados sin ownership.
- [ ] Inspeccionar visualmente contraste y legibilidad en el viewport real.
- [ ] Registrar los valores realmente usados y su provenance.
- [ ] **STOP VISUAL:** devolver captura, asignaciones, observaciones y
  limitaciones; esperar feedback humano.

## T6.04 [ ] — Lighting & review camera v1

- [ ] Preservar `HS3D_CAMERA` y `HS3D_KEY_LIGHT` de validación; añadir solo
  presentación visual con namespace propio.
- [ ] Crear iluminación ligera de review, preferentemente EEVEE Next, con
  parámetros deterministas y coste acotado.
- [ ] Crear cámara de review reproducible que incluya arquitectura y muebles
  sin clipping ni objetos accidentales.
- [ ] Ajustar exposición y encuadre mediante inspección del viewport, no por
  ejecución background ciega.
- [ ] Generar un review render ligero en path repo-relative, sin prometer
  igualdad binaria.
- [ ] **STOP VISUAL:** devolver render/captura, parámetros, limitaciones y
  cualquier desviación; esperar feedback humano.

## T6.05 [ ] — Visual acceptance & reproducibility

- [ ] Comparar source antes/después y demostrar que no mutaron arquitectura,
  measurements, layouts, FurniturePlan ni spatial reports.
- [ ] Normalizar/inspeccionar roots, collections, ownership, units, transforms,
  materials, camera y lights de la escena derivada.
- [ ] Ejecutar regresión pure furniture/room y comprobaciones estructurales
  Blender aplicables.
- [ ] Repetir la generación lógica en una copia y comparar inventario,
  transforms, assignments y parámetros; no exigir hash binario.
- [ ] Auditar privacidad, provenance, binarios, tamaño, temporales y rollback.
- [ ] Obtener viewport y render final, registrar feedback humano y decidir qué
  evidencia se versiona.
- [ ] **STOP VISUAL:** no avanzar a T6.06 hasta contar con aceptación humana
  explícita o registrar el gate como bloqueado.

## T6.06 [ ] — Documentation & final audit

- [ ] Crear `docs/setup/006-visual-furnishing-materials-validation.md` con
  evidencia real, paths, versiones, gates, feedback y limitaciones.
- [ ] Reconciliar spec/plan/tasks con el comportamiento y no cerrar tareas sin
  evidencia correspondiente.
- [ ] Revisar diff completo, privacy, assets/licencias, binarios, temporales,
  source preservation y rollback.
- [ ] Ejecutar `git diff --check` y gates proporcionales; marcar controles no
  ejecutados honestamente.
- [ ] Confirmar que no hay Slice 007, UI, catálogo, A/B/C visual ni scope creep.
- [ ] Dejar la rama lista para PR; la apertura de PR requiere autorización
  posterior y no forma parte automática de esta tarea.

## Acceptance final prevista

- [ ] La escena visual es reconocible como `living-room-main`.
- [ ] Arquitectura, openings proxy y colecciones `HS3D_ROOM_*` permanecen
  intactos.
- [ ] Sofá, sillón y mesa son visualmente distinguibles y están colocados según
  baseline A.
- [ ] Materiales de pared, suelo y muebles se distinguen y tienen provenance
  procedural sintética.
- [ ] Cámara y luces de review permiten inspeccionar volumen, materiales y
  relación furniture/arquitectura.
- [ ] No aparecen geometría rota, objetos accidentales, overlays/debug no
  intencionados ni datos privados en el render.
- [ ] Existe evidencia de viewport y review render inspeccionada por el usuario.
- [ ] La lógica es reproducible y la escena source queda preservada; no se
  exige igualdad binaria de `.blend` o PNG.
