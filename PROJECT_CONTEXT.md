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
- La foundation, el contrato de medición/reconstrucción y la comparación/validación de escena real están implementados e integrados en `main`.

## Estado actual

- `living-room-main` es la habitación real validada de referencia.
- El flujo vigente es `measurements/` → generation plan determinista → generación arquitectónica en Blender → `NormalizedScene` → comparación `room → plan` y `plan → scene`.
- El contrato actual usa `room-v1.1-generator-2`, con `room-scene-adapter-1` y `room-scene-comparison-1`; la compatibilidad v1 se conserva.
- `measurements/` sigue siendo la autoridad arquitectónica; la escena es un derivado validado.

## Limitaciones actuales

- Los openings siguen siendo proxies técnicos (`proxy_only=true`, `constructive_geometry=false`); no hay booleanos ni geometría constructiva.
- No hay una capa de mobiliario/decoración libre ni validación multi-room como producto.
- La provenance materializada en Blender es parcial por diseño.
- Dieciséis espesores permanecen `unknown` con fallback explícito y `opening_direction` continúa `unknown`.

## Próximo horizonte

El trabajo posterior deberá definirse mediante un nuevo slice aprobado. Este contexto no inicia ni da por aprobado Slice 004.

## Contrato común de calidad

`AlexFrigenti/project-quality` es el contrato común de referencia. Home Studio 3D usa un perfil Blender/3D adaptado, y `.quality/QUALITY.md` define sus gates concretos.

## Límite histórico de este bootstrap

Este apartado conserva el alcance original del bootstrap: su producción 3D, sus assets y cualquier ampliación del entorno quedaban fuera de aquel slice inicial.
