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

## Estado de la foundation

- Blender 5.2.1, Blender MCP y Codex CLI están instalados y operativos en el portátil.
- La comunicación live `Codex → Blender MCP → Blender` quedó validada mediante lectura de escena.
- El fixture `blender/scenes/tests/001-foundation-room.blend` quedó validado y probado entre portátil y sobremesa, sin convertir ninguna máquina en autoridad sobre las medidas.
- La producción 3D del proyecto aún no se ha iniciado.

## Contrato común de calidad

`AlexFrigenti/project-quality` es el contrato común de referencia. Home Studio 3D usa un perfil Blender/3D adaptado, y `.quality/QUALITY.md` define sus gates concretos.

## Límite de este bootstrap

Este repositorio contiene la base documental y estructural inicial, junto con la evidencia de foundation validada. La producción 3D, los assets y cualquier ampliación del entorno quedan fuera de este slice.
