# Validación de la habitación sintética de fundación

## Fixture

- Escena: `blender/scenes/tests/001-foundation-room.blend`
- Colección: `HS3D_T2_09_FOUNDATION_ROOM`
- Contrato: volumen interior `5.00 × 4.00 × 2.50 m`
- T2.10: PASS con tolerancia `1e-6 m`; `sofa_proxy.location` corregido y persistente tras reapertura.

## Validación entre equipos

- El fixture `blender/scenes/tests/001-foundation-room.blend` fue probado entre el portátil y el sobremesa.
- La prueba confirmó la reproducibilidad del fixture y de su contrato sintético; no se registran aquí rutas ni detalles adicionales del sobremesa.

## Evidencia visual T2.11

- Evidencia persistente: `renders/previews/001-foundation-room/viewport-overview.png`
- Resolución: `800 × 600`
- Motor: `BLENDER_WORKBENCH`
- Tamaño: `297438` bytes
- GPU/VRAM: no utilizada/no hubo incidencia registrada
- No se ejecutó Cycles ni render final pesado.

La captura muestra de forma reconocible el suelo, las cuatro paredes, `door`, `window` y `sofa_proxy`. El sofá aparece dentro del volumen, sin atravesar suelo o paredes; las aperturas se distinguen en las paredes sur y este. La cámara y la luz del fixture forman parte de la composición/escena sin objetos residuales inesperados.

## Inspección por criterio

1. Volumen de habitación coherente: PASS; el test no incluye techo.
2. Paredes sin solapes o huecos visuales no previstos: PASS.
3. Suelo alineado: PASS.
4. `door` asociada a pared sur: PASS.
5. `window` asociada a pared este: PASS.
6. `sofa_proxy` dentro del volumen: PASS.
7. `sofa_proxy` sin penetración visual en suelo o paredes: PASS.
8. Cámara del test útil para inspección interior: PASS.
9. Legibilidad de la iluminación del preview: PASS; Workbench usa sombreado de estudio y no evalúa artísticamente la energía de la luz de escena.
10. Objetos residuales inesperados: PASS; la escena conserva únicamente los 10 objetos contractuales.
11. Artefactos visuales graves contradictorios con T2.10: PASS; no observados.

## Limitaciones y reversibilidad

Se usó una vista de cámara MCP y un encuadre elevado temporal para hacer visibles simultáneamente las aperturas y el proxy. Se restauró el fixture reabriendo el mismo archivo y el viewport volvió a perspectiva de usuario; no se guardaron los cambios temporales de cámara, render o viewport. La evidencia es de preview técnico, no una evaluación estética ni un render de producción.
