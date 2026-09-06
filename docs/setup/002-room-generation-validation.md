# Validación del generador de room-v1

Este documento describe el primer flujo ejecutable del slice
`002-room-measurement-and-reconstruction`. Es una prueba sintética y no
representa el salón real.

## Flujo y entrada

La entrada canónica es:

`measurements/fixtures/room-v1-synthetic.json`

El flujo es:

`JSON de measurements → validate_measurements.py → generate_room.py → .blend derivado`

`blender/scripts/measurements/generate_room.py` carga el JSON, reutiliza
`validate_measurements.py` y no crea ni modifica la escena hasta que la
validación pasa. También rechaza longitudes que no coincidan con las
coordenadas, límites imposibles y salidas/previews ya existentes.

La ejecución controlada desde la raíz del repositorio es equivalente a:

```text
<BLENDER_HOME>\blender.exe --background --factory-startup --offline-mode --python blender\scripts\measurements\generate_room.py -- --input measurements\fixtures\room-v1-synthetic.json --output blender\scenes\tests\002-room-v1-generated.blend --preview renders\previews\002-room-v1-generated\viewport-overview.png
```

El generador no usa red, subprocess, addons, assets externos ni MCP. La
escena usa `METRIC`, `scale_length=1.0` y metros como unidad interna.

## Estructura y geometría

La colección raíz es `HS3D_ROOM_<room_id>` y contiene:

- `Architecture`: un suelo poligonal y una pared prismática por segmento
  ordenado del boundary;
- `Openings`: un proxy geométrico por puerta o ventana;
- `FixedElements`: un proxy por elemento fijo anclado;
- `Validation`: cámara y luz técnica del preview.

Las caras interiores de las paredes coinciden con los segmentos del boundary.
Para un boundary antihorario, el espesor se extiende hacia la derecha del
segmento, es decir, hacia el exterior. El suelo conserva todos los puntos del
polígono y por eso representa el retranqueo del fixture, en lugar de reducirlo
a un rectángulo.

El fixture no captura espesor de pared. El generador usa `0.10 m` únicamente
como geometría derivada de proxy, conserva `hs3d_thickness_source_status =
unknown` y marca el fallback explícitamente. No se convierte en una medida
`measured`.

Los openings se representan en v1 como cuboides de proxy, colocados en el
segmento referenciado usando `offset`, `width`, `height` y `sill_height`.
Quedan en el lado interior de la pared y no ejecutan booleanos ni pretenden
ser huecos constructivos. La profundidad desconocida usa un proxy derivado
de `0.06 m`. Esta limitación debe resolverse antes de admitir geometría real
que requiera carpintería o cortes constructivos.

El elemento fijo sintético se genera como proxy simple. Para un anclaje de
pared, su posición usa `wall_id` y `anchor.offset`; `height` se interpreta
como altura del centro del proxy. Sus dimensiones visuales (`0.12 × 0.06 ×
0.12 m`) son de representación, no nuevas medidas del fixture.

## Metadata y trazabilidad

La raíz, subcolecciones y objetos guardan propiedades `hs3d_*`, entre ellas:

- `room_id`, versión del generador, schema y unidades;
- ruta de input relativa al repositorio, nunca una ruta personal absoluta;
- `source_id`, estado original y estado geométrico derivado;
- `wall_id`, offset, width, height, sill height y sus estados para openings;
- fórmula/dependencias del área derivada;
- firma lógica del plan y el índice de estados presentes.

Los cuatro estados del contrato (`measured`, `estimated`, `derived`,
`unknown`) permanecen distinguibles en la escena. Un valor `unknown` no se
lee como medida real; solo puede aparecer un fallback explícito donde esta
v1 lo documenta.

## Determinismo y validación numérica

`build_generation_plan(room)` es una representación JSON-serializable estable
y `logical_signature(plan)` la canoniza con claves ordenadas. Cada ejecución
controlada elimina únicamente la colección raíz y datablocks con prefijo
`HS3D_`, crea nombres estables y deja transformaciones de malla aplicadas.

`generate_room.py` realiza dos generaciones dentro de la misma escena limpia,
valida ambas y compara sus firmas de escena. Solo después guarda el archivo
de prueba:

`blender/scenes/tests/002-room-v1-generated.blend`

`blender/scripts/measurements/validate_generated_room.py` abre el `.blend` en
modo background y comprueba sin guardar cambios:

- unidades y colecciones;
- puntos del boundary, suelo, paredes y altura;
- posiciones/offsets y referencias de puerta/ventana;
- elemento fijo, estados, source IDs y ausencia de duplicados.

La tolerancia de estas comparaciones de geometría derivada es `1e-6 m`. Es
una tolerancia matemática de comparación y no una afirmación sobre la
incertidumbre física de las medidas.

## Preview y limitaciones

El preview técnico se guarda en:

`renders/previews/002-room-v1-generated/viewport-overview.png`

Usa una cámara fija y Eevee Next (Workbench queda como fallback); no usa
Cycles. La inspección visual busca forma de la habitación, retranqueo,
proxies de openings y fixed elements, penetraciones graves y objetos
residuales. No es una validación estética.

Quedan fuera de esta fase los datos reales, el modelado del salón, decoración,
assets externos, booleanos constructivos, integración MCP/Codex y cualquier
redefinición de medidas canónicas.
