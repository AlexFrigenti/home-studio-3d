# Project Context

## Decisiones adoptadas

- Proyecto personal de interiorismo y visualización 3D.
- Primera prueba objetivo: una habitación simple, antes de modelar el salón real.
- Línea de Blender elegida: Blender 5.2 LTS.
- MCP candidato principal: `ahujasid/blender-mcp`.
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

## Contrato común de calidad

`AlexFrigenti/project-quality` es el contrato común de referencia. Home Studio 3D usa un perfil Blender/3D adaptado, y `.quality/QUALITY.md` define sus gates concretos.

## Límite de este bootstrap

Este repositorio contiene únicamente la base documental y estructural inicial. La instalación de Blender, MCP, Python, `uv`, dependencias, plugins y otras herramientas queda fuera de esta fase.
