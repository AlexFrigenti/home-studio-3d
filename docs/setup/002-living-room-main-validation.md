# Validación de la primera reconstrucción real: `living-room-main`

## Alcance y fuente

Este documento registra el checkpoint de la primera reconstrucción real del
salón principal dentro del slice `002-room-measurement-and-reconstruction`.
La escena y el preview descritos aquí son evidencia histórica; la actualización
de altura de la sesión vertical del 2026-09-07 no los regenera ni añade
modelado adicional.

- Input canónico: `measurements/rooms/living-room-main.json`
- Schema: `1.1`
- HEAD fuente del checkpoint Blender histórico: `69b39a69cadd36a07f8b674bf993a64c86c2e228`
- Unidades: metros (`m`)
- Boundary: 22 segmentos, winding antihorario
- Openings: 6

## Actualización de altura real (sesión vertical 2026-09-07)

- Altura suelo terminado → techo terminado: `3.00 m`, incertidumbre `±0.01 m`.
- Estado y método: `measured` / `manual_tape`.
- `source_id`: `living-room-main-2026-09-07-vertical-session-01-height-floor-to-ceiling`.
- El generation plan actual de `living-room-main` usa `3.00 m` como medida
  observada y geométrica `measured`; el fallback general de altura no se activa.
- El valor coincide numéricamente con el antiguo fallback, pero su procedencia
  actual es una lectura física independiente.

## Reconciliaciones y generation plan

- `wall-05`: observado `0.45 m` (`measured`); geometría `0.47 m` (`derived`, reconciliada).
- `wall-16`: observado `1.00 m` (`measured`); geometría `0.99 m` (`derived`, reconciliada).
- `V2` (`window-v2`): `wall-14`, offset observado `0.64 m`, width `2.40 m`.
- En el checkpoint Blender histórico, la altura observada era `unknown`, valor
  `null`, y la altura geométrica era `3.00 m`, `derived`, con fallback explícito.
- Estado actual del JSON: altura observada `3.00 m` (`measured`) y altura
  geométrica efectiva `3.00 m` (`measured`), sin fallback.

La medida física actual sustituye el estado `unknown` y deja sin efecto el
fallback únicamente para `living-room-main`. El fallback permanece disponible
en el generador para otros documentos v1.1 con altura `unknown`.

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
- Altura general de `living-room-main`: no aplica tras la lectura física del
  2026-09-07.

## Evidencia y validaciones

- Tests de `tests/measurements`: `61/61 PASS` tras actualizar la expectativa
  histórica del plan de `living-room-main`.
- `GENERATION_VALID`: PASS en el checkpoint Blender histórico; no se ha
  reejecutado tras incorporar la altura medida.
- `SCENE_VALID`: PASS en el checkpoint Blender histórico; no se ha reejecutado
  tras incorporar la altura medida.
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

- La altura general real de la habitación está medida: `3.00 m ±0.01 m`,
  `manual_tape`, sesión vertical `2026-09-07`.
- El fallback general de altura no se aplica actualmente a `living-room-main`.
- P1, P2, V1, V2, V3 y V4 siguen sin alturas verticales reales.
- Las alturas verticales de los openings son proxies visuales.
- No hay booleanos ni geometría constructiva de openings.
- No se ha realizado una nueva generación Blender tras incorporar esta altura.
- La profundidad `unknown` usa el fallback proxy de `0.06 m`.
- El espesor `unknown` de pared usa el fallback proxy de `0.10 m`.
- No se ha añadido mobiliario ni decoración.
- No se ha inferido geometría a partir de fotografías.
- No se han incorporado assets externos.

El checkpoint Blender histórico queda como:

`ESCENA REAL HISTÓRICA APTA PARA REVISIÓN; REGENERACIÓN PENDIENTE TRAS ACTUALIZAR LA ALTURA`
