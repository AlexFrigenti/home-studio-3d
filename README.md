# Home Studio 3D

Home Studio 3D es un proyecto personal para reconstruir espacios reales de una vivienda a escala 1:1 y probar distribución, mobiliario, materiales e iluminación.

Blender será la herramienta 3D principal. Codex + MCP de Blender ya proporcionan la capa agentic local para trabajar sobre las escenas con control y validación visual.

El proyecto se compartirá entre el portátil y el PC de sobremesa mediante Git/GitHub.

## Estado actual

Los slices 001–005 están integrados en `main`. Slice 006 está validado en la
rama `spec/006-visual-furnishing-materials-v1` y pendiente de revisión final e
integración. El flujo validado para `living-room-main` es:

`measurements/` → generation plan determinista → arquitectura Blender → normalización y comparación de room → layout furniture validado → `FurniturePlan` → spatial validation → overlay Blender reversible → normalización y comparación furniture → acceptance técnica → capa visual procedural y review presentation de Slice 006.

El dominio furniture usa el contrato `furniture-layout-1`, mantiene `measurements/` como autoridad arquitectónica y conserva la separación entre `HS3D_ROOM_*` y `HSLAYOUT_*`. Slice 004 incluye una acceptance sintética canónica, un `.blend` derivado y un preview técnico.

## Limitaciones actuales

- El mobiliario sigue representado por proxies/cuboids sintéticos; no hay assets reales ni catálogo.
- Los layouts se crean manualmente como JSON y todavía no existe comparación A/B/C de variantes.
- Slice 006 añade materiales visuales v1 procedurales e iluminación/cámara de review; no hay materiales artísticos finales, ergonomía, circulación ni recomendaciones de interiorismo.
- Los openings siguen siendo proxies (`proxy_only=true`, `constructive_geometry=false`) y `opening_direction` continúa `unknown`.
- En `living-room-main` permanecen dieciséis espesores de pared `unknown` con fallback explícito.
- La provenance materializada en Blender es parcial, el producto no está validado para multi-room y no existe una acceptance representativa de fixed elements.
- El guardado de escenas no ofrece rollback transaccional.

## Próximo horizonte

No hay un Slice 007 iniciado. El trabajo posterior a Slice 006 requiere un nuevo
slice definido y aprobado.
