# Validación de la primera reconstrucción real: `living-room-main`

## Alcance y fuente

Este documento registra el checkpoint de la primera reconstrucción real del
salón principal dentro del slice `002-room-measurement-and-reconstruction`.
La escena y el preview descritos aquí son evidencia histórica; las actualizaciones
de altura, geometría vertical y espesores de la sesión del 2026-09-07 no los
regeneran ni añaden modelado adicional.

- Input canónico: `measurements/rooms/living-room-main.json`
- Schema: `1.1`
- HEAD fuente del checkpoint Blender histórico: `69b39a69cadd36a07f8b674bf993a64c86c2e228`
- Unidades: metros (`m`)
- Boundary: 22 segmentos, winding antihorario
- Openings: 6

## Actualización de altura real (sesión vertical 2026-09-07)

- Altura suelo terminado → techo terminado: `2.50 m`, incertidumbre `±0.01 m`.
- Estado y método: `measured` / `manual_tape`.
- `source_id`: `living-room-main-2026-09-07-vertical-session-02-height-floor-to-ceiling-correction`.
- El generation plan actual de `living-room-main` usa `2.50 m` como medida
  observada y geométrica `measured`; el fallback general de altura no se activa.
- Esta segunda comprobación física corrige la lectura anterior de `3.00 m`, que
  queda superseded como autoridad observada.

## Reconciliaciones y generation plan

- `wall-05`: observado `0.45 m` (`measured`); geometría `0.47 m` (`derived`, reconciliada).
- `wall-16`: observado `1.00 m` (`measured`); geometría `0.99 m` (`derived`, reconciliada).
- `V2` (`window-v2`): `wall-14`, offset observado `0.64 m`, width `2.40 m`.

## Actualización de espesores reales (sesión vertical 2026-09-07)

- Se midió físicamente con cinta métrica el espesor visible en la jamba de cada
  uno de los seis huecos autorizados: `0.08 m ±0.01 m`, `measured`,
  `manual_tape`.
- Muros actualizados: `wall-00` (P1), `wall-06` (P2), `wall-07` (V3),
  `wall-08` (V4), `wall-14` (V2) y `wall-20` (V1).
- Los otros 16 segmentos conservan `thickness.status=unknown`; no se extrapola
  el valor de las jambas.
- El espesor de muro y la profundidad del opening son magnitudes distintas;
  por ejemplo, P2 conserva `depth=0.05 m` aunque `wall-06.thickness=0.08 m`.
- En el checkpoint Blender histórico, la altura observada era `unknown`, valor
  `null`, y la altura geométrica era `3.00 m`, `derived`, con fallback explícito.
- Estado actual del JSON: altura observada `2.50 m` (`measured`) y altura
  geométrica efectiva `2.50 m` (`measured`), sin fallback.

La segunda medida física sustituye la lectura anterior de `3.00 m` y deja sin
efecto el fallback únicamente para `living-room-main`. El fallback permanece
disponible en el generador para otros documentos v1.1 con altura `unknown`.

Los seis openings conservan sus offsets y widths canónicos y siguen siendo
proxies visuales sin booleanos constructivos (`proxy_only=true`,
`constructive_geometry=false`). P1, P2, V1, V2, V3 y V4 tienen sus medidas
verticales y profundidades observadas como `measured`; ya no quedan proxies
verticales activos en el generation plan de `living-room-main`.

Openings generados:

| Identificador | Pared | Offset | Width |
| --- | --- | ---: | ---: |
| P1 (`door-main`) | `wall-00` | 0.45 m | 1.60 m |
| P2 (`door-terrace`) | `wall-06` | 0.00 m | 0.55 m |
| V1 (`window-v1`) | `wall-20` | 0.10 m | 0.74 m |
| V2 (`window-v2`) | `wall-14` | 0.64 m | 2.40 m |
| V3 (`window-v3`) | `wall-07` | 0.00 m | 3.69 m |
| V4 (`window-v4`) | `wall-08` | 0.00 m | 1.32 m |

Estado vertical canónico:

- P1: altura `2.00 m` y profundidad `0.08 m`, `measured`.
- P2: altura `2.30 m` y profundidad `0.05 m`, `measured`.
- V1: alféizar `0.92 m`, altura `1.39 m` y profundidad `0.08 m`, `measured`.
- V2: alféizar `0.92 m`, altura `1.39 m` y profundidad `0.08 m`, `measured`.
- V3: alféizar `0.86 m`, altura `1.25 m` y profundidad `0.06 m`, `measured`.
- V4: alféizar `0.86 m`, altura `1.25 m` y profundidad `0.06 m`, `measured`.

Fallbacks explícitos:

- Espesor de pared desconocido: proxy derivado de `0.10 m`.
- Altura general de `living-room-main`: no aplica tras la lectura física del
  2026-09-07.

## Evidencia y validaciones

- Tests de `tests/measurements`: `61/61 PASS` tras actualizar la expectativa
  histórica del plan de `living-room-main`.
- `GENERATION_VALID`: PASS en el checkpoint Blender histórico; no se ha
  reejecutado tras incorporar las nuevas medidas verticales y espesores.
- `SCENE_VALID`: PASS en el checkpoint Blender histórico; no se ha reejecutado
  tras incorporar las nuevas medidas verticales y espesores.
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

- La altura general real de la habitación está medida: `2.50 m ±0.01 m`,
  `manual_tape`, sesión vertical `2026-09-07`; la lectura previa de `3.00 m`
  fue corregida por una segunda comprobación física.
- El fallback general de altura no se aplica actualmente a `living-room-main`.
- P1, P2, V1, V2, V3 y V4 tienen alturas, alféizares y profundidades reales
  transcritas al JSON canónico.
- Los seis openings siguen siendo proxies visuales, pero ya no quedan proxies
  verticales activos.
- El espesor observado `0.08 m ±0.01 m` está transcrito para `wall-00`,
  `wall-06`, `wall-07`, `wall-08`, `wall-14` y `wall-20`; los otros 16 muros
  permanecen `unknown` y usan el fallback geométrico `0.10 m`.
- Las profundidades de los openings no se han cambiado por estas lecturas de
  espesor de jamba.
- No hay booleanos ni geometría constructiva de openings.
- No se ha realizado una nueva generación Blender tras incorporar estas
  nuevas medidas verticales y espesores.
- No se ha añadido mobiliario ni decoración.
- No se ha inferido geometría a partir de fotografías.
- No se han incorporado assets externos.

El checkpoint Blender histórico queda como:

`ESCENA REAL HISTÓRICA APTA PARA REVISIÓN; REGENERACIÓN PENDIENTE TRAS INCORPORAR LAS NUEVAS MEDIDAS VERTICALES`
