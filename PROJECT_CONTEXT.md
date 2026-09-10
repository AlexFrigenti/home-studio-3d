# Project Context

## Decisiones adoptadas

- Proyecto personal de interiorismo y visualización 3D.
- Primera prueba objetivo: una habitación simple, antes de modelar el salón real.
- Línea de Blender elegida: Blender 5.2 LTS; versión validada: Blender 5.2.1 LTS.
- MCP adoptado y validado: `ahujasid/blender-mcp`, fijado al commit `5866814479b4e2ca674d8d44969a9a2a78fdc8bb`.
- Codex será el agente principal.
- Se prefiere GPT-6 Astra para el trabajo futuro cuando esté disponible en Codex.
- Se podrá utilizar `bpy`, siempre bajo las reglas de seguridad de `AGENTS.md`.
- La conexión MCP será exclusivamente local.
- El feedback visual forma parte obligatoria de la validación.
- PC principal de render: RTX 3080 con 10 GB de VRAM y 32 GB de RAM.
- El portátil será la segunda estación de trabajo.
- Las medidas estructuradas serán la fuente de verdad; la geometría de Blender será su representación.
- GitHub será la fuente de verdad del proyecto compartido entre equipos.
- Los assets pesados y la estrategia de Git LFS se decidirán posteriormente.

## Estado completado

- Blender 5.2.1, Blender MCP y Codex CLI están instalados y operativos en el portátil.
- La comunicación live `Codex → Blender MCP → Blender` quedó validada mediante lectura de escena.
- El fixture `blender/scenes/tests/001-foundation-room.blend` quedó validado y probado entre portátil y sobremesa, sin convertir ninguna máquina en autoridad sobre las medidas.
- Slice 001 — Blender/Codex/MCP Foundation está integrado en `main`.
- Slice 002 — Room Measurement and Reconstruction está integrado en `main`.
- Slice 003 — Real Room Scene Comparison and Validation está integrado en `main`.
- Slice 004 — Furniture Placement v1 está integrado en `main`.
- Slice 005 — Multiple Layout Comparison v1 está integrado en `main`.

## Estado actual

- `living-room-main` es la habitación real validada de referencia.
- Slice 006 — Visual Furnishing & Materials v1 está validado en la rama
  `spec/006-visual-furnishing-materials-v1` y pendiente de revisión final e
  integración.
- El flujo room vigente es `measurements/` → generation plan determinista → generación arquitectónica en Blender → `NormalizedScene` → comparación `room → plan` y `plan → scene`.
- El contrato room actual usa `room-v1.1-generator-2`, con `room-scene-adapter-1` y `room-scene-comparison-1`; la compatibilidad v1 se conserva.
- `measurements/` sigue siendo la autoridad arquitectónica; la escena es un derivado validado.
- El dominio furniture usa `furniture-layout-1`, `furniture-placement-generator-1` y `furniture-spatial-validation-1`.
- El flujo furniture vigente es layout JSON → `FurniturePlan` → spatial validation → overlay Blender reversible → `furniture-scene-adapter-1` → `furniture-scene-comparison-1` → capa visual procedural y review presentation de Slice 006.
- `HSLAYOUT_*` permanece separado de `HS3D_ROOM_*`; el furniture overlay no modifica la arquitectura.
- Slice 004 tiene acceptance sintética canónica, `.blend` derivado, preview técnico, privacy guard y firmas lógicas deterministas.
- Slice 005 tiene comparación de variantes, acceptance canónica y gates puros integrados en `main`.
- Slice 006 tiene escena derivada visual, preview de review, materiales procedurales v1 y validación lógica/documental completa en su rama.

## Limitaciones actuales

- Los openings siguen siendo proxies técnicos (`proxy_only=true`, `constructive_geometry=false`); no hay booleanos ni geometría constructiva.
- El mobiliario sigue limitado a proxies/cuboids sintéticos; no hay assets reales, catálogo ni materiales artísticos finales.
- Los layouts siguen siendo JSON manuales; no hay comparación A/B/C de variantes, ergonomía, circulación ni recomendaciones.
- No existe validación multi-room como producto.
- El contrato de fixed elements existe, pero `living-room-main` no tiene una acceptance representativa de obstáculos fijos.
- La provenance materializada en Blender es parcial por diseño.
- Dieciséis espesores permanecen `unknown` con fallback explícito y los seis openings mantienen `opening_direction=unknown`.
- El guardado de escenas no dispone de rollback transaccional.

## Próximo horizonte

No hay un Slice 007 iniciado. El trabajo posterior deberá definirse mediante un
nuevo slice aprobado.

## Contrato común de calidad

`AlexFrigenti/project-quality` es el contrato común de referencia. Home Studio 3D usa un perfil Blender/3D adaptado, y `.quality/QUALITY.md` define sus gates concretos.

## Límite histórico de este bootstrap

Este apartado conserva el alcance original del bootstrap: su producción 3D, sus assets y cualquier ampliación del entorno quedaban fuera de aquel slice inicial.
