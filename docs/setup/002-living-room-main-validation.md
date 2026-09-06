# Validación de la primera reconstrucción real: `living-room-main`

## Alcance y fuente

Este documento registra el checkpoint de la primera reconstrucción real del
salón principal dentro del slice `002-room-measurement-and-reconstruction`.
No inicia nuevas mediciones ni añade modelado adicional.

- Input canónico: `measurements/rooms/living-room-main.json`
- Schema: `1.1`
- HEAD fuente: `69b39a69cadd36a07f8b674bf993a64c86c2e228`
- Unidades: metros (`m`)
- Boundary: 22 segmentos, winding antihorario
- Openings: 6

## Reconciliaciones y generation plan

- `wall-05`: observado `0.45 m` (`measured`); geometría `0.47 m` (`derived`, reconciliada).
- `wall-16`: observado `1.00 m` (`measured`); geometría `0.99 m` (`derived`, reconciliada).
- `V2` (`window-v2`): `wall-14`, offset observado `0.64 m`, width `2.40 m`.
- Altura observada de la habitación: `unknown`, valor `null`.
- Altura geométrica: `3.00 m`, `derived`, fallback explícito de generación.

Los `3.00 m` no son una medida real, una estimación ni una reconciliación de
la altura. Solo materializan provisionalmente la escena para revisión.

Los seis openings conservan sus offsets y widths canónicos. Su geometría
vertical es únicamente un proxy visual de `0.10 m`; el estado vertical
observado permanece `unknown`, `proxy_only=true` y
`constructive_geometry=false`. No se ejecutan booleanos constructivos.

Openings generados:

| Identificador | Pared | Offset | Width |
| --- | --- | ---: | ---: |
| P1 (`door-main`) | `wall-00` | 0.45 m | 1.60 m |
| P2 (`door-terrace`) | `wall-06` | 0.00 m | 0.55 m |
| V1 (`window-v1`) | `wall-20` | 0.10 m | 0.74 m |
| V2 (`window-v2`) | `wall-14` | 0.64 m | 2.40 m |
| V3 (`window-v3`) | `wall-07` | 0.00 m | 3.69 m |
| V4 (`window-v4`) | `wall-08` | 0.00 m | 1.32 m |

Fallbacks explícitos:

- Profundidad desconocida de openings: proxy derivado de `0.06 m`.
- Espesor de pared desconocido: proxy derivado de `0.10 m`.

## Evidencia y validaciones

- Tests de `tests/measurements`: `61/61 PASS`.
- `GENERATION_VALID`: PASS.
- `SCENE_VALID`: PASS.
- Firma de escena: `6122a4811a8cbce931b05e6e4f52c9a45dd3170e6eb9fb73d7d1fc41ddc05ef3`.
- Determinismo: PASS; las generaciones repetidas produjeron la misma firma.
- Escena derivada: `blender/scenes/review/2026-09-07-living-room-main-v1.1-generated.blend`.
- Preview ortográfico aprobado:
  `renders/previews/2026-09-07-living-room-main-v1.1/qa-top-orthographic-v2.png`.
- QA visual final: `14/14 PASS`.
- Revisión humana del usuario: aprobada.

La captura perspectiva inicial (`viewport-overview.png`) conserva valor
histórico limitado por su encuadre recortado. La captura intermedia
`qa-top-orthographic.png` no forma parte de la evidencia versionada por su
encuadre incorrecto. La evidencia aprobada es `qa-top-orthographic-v2.png`.

## Limitaciones y exclusiones

- La altura real de la habitación continúa desconocida.
- `3.00 m` es un fallback `derived`, no una medida real.
- Las alturas verticales de los openings son proxies visuales.
- No hay booleanos ni geometría constructiva de openings.
- La profundidad `unknown` usa el fallback proxy de `0.06 m`.
- El espesor `unknown` de pared usa el fallback proxy de `0.10 m`.
- No se ha añadido mobiliario ni decoración.
- No se ha inferido geometría a partir de fotografías.
- No se han incorporado assets externos.

Este checkpoint deja la primera escena real como:

`ESCENA REAL APTA PARA REVISIÓN`
