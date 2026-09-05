# Especificación: Room Measurement and Reconstruction

> Clasificación: T2 — contrato canónico de medidas, unidades y coordenadas
> Rama: `spec/002-room-measurement-and-reconstruction`
> Estado: cierre documental; JSON v1 y baseline inicial aprobados; no se han capturado medidas reales ni generado geometría del salón

## Objetivo

Definir un sistema reproducible para pasar de medidas reales tomadas en casa a
una representación 1:1 en Blender. El slice establece el formato canónico de
`measurements/`, el sistema de coordenadas por habitación, la forma de
registrar incertidumbre, el flujo de captura, las validaciones y la arquitectura
futura de generación. No modela todavía el salón real.

## Problema

Las medidas de una vivienda pueden proceder de métodos con precisiones distintas
y una habitación puede no ser un rectángulo perfecto. Sin un contrato común,
una estimación puede convertirse silenciosamente en una medida, una puerta puede
quedar referenciada a coordenadas ambiguas o Blender puede terminar corrigiendo
los datos para que la geometría encaje. El contrato debe conservar la trazabilidad
entre observación, incertidumbre, geometría derivada y evidencia.

## Alcance

### Incluye

- Decisión entre YAML y JSON y definición del schema v1.
- Unidad canónica de almacenamiento, precisión y sistema de coordenadas local.
- Representación de segmentos de pared, habitaciones no rectangulares, huecos y elementos fijos.
- Clasificación obligatoria de cada medida como `measured`, `estimated`, `derived` o `unknown`.
- Propuesta de tolerancias físicas, matemáticas y visuales.
- Evaluación del flujo de captura y de la evidencia fotográfica.
- Arquitectura futura `measurement file → parser/validator → bpy generator → .blend`.
- Diseño de un segundo fixture sintético conceptual para probar el contrato.
- Validaciones futuras, riesgos, invariantes y decisiones pendientes.

### Fuera de alcance

- Capturar o registrar todavía medidas reales en `measurements/`.
- Modelar el salón real o modificar cualquier escena canónica.
- Crear `.blend`, previews, scripts, validadores o generadores en este slice.
- Instalar Blender, MCP, Python, paquetes, addons, LiDAR o herramientas de captura.
- Cambiar `README.md`, `PROJECT_CONTEXT.md`, `measurements/` o la configuración local.
- Convertir las tolerancias propuestas en estándar definitivo sin aprobación y validación.
- Añadir fotografías personales, planos privados o assets externos al repositorio.

## Principio de autoridad

`measurements/` es la fuente de verdad de las medidas reales. Blender es una
representación derivada y verificable de esos datos; no redefine sus valores.
Nunca se corregirá una medida real únicamente para que Blender “encaje”. Si la
geometría derivada no coincide con los datos dentro de la tolerancia aceptada,
el resultado debe registrar una discrepancia y solicitar revisión de los datos,
del método o del contrato.

Las escenas generadas a partir de medidas reales deberán poder rastrear cada
valor relevante hasta su registro, método y evidencia. Una escena de prueba
sintética no adquiere autoridad sobre `measurements/`.

## Sistema de unidades y precisión

- Unidad canónica de almacenamiento: metros (`m`).
- Los campos de longitud terminan en `_m`; áreas usan `_m2` y ángulos usan `_deg`.
- Los valores JSON se almacenan como números, no como cadenas con unidades.
- La precisión de almacenamiento mínima propuesta es `0.001 m` (1 mm); se pueden
  conservar más decimales cuando procedan del instrumento, sin presentarlos como
  precisión real.
- Blender debe usar `METRIC` con `scale_length = 1.0`.
- La precisión almacenada, la precisión real del método y la tolerancia de
  validación son conceptos distintos y se registran por separado.
- `unknown` no se representa como cero, aproximación silenciosa ni valor vacío
  interpretable como medida.

### Distinción obligatoria

| Concepto | Significado | Ejemplo |
| --- | --- | --- |
| Precisión almacenada | Resolución con la que se escribe el número | `0.001 m` |
| Incertidumbre de medición | Rango razonable del método y la observación | `±0.005 m` con cinta |
| Tolerancia de validación | Residual permitido al comprobar una regla concreta | `1e-6 m` para aritmética del parser |

## Sistema de coordenadas por habitación

Cada habitación tiene un sistema local, independiente de rutas, brújula o
orientación de una aplicación externa.

- Origen `(0, 0, 0)`: esquina interior del suelo terminado seleccionada y
  registrada como `origin.corner_id`.
- `Z`: vertical positiva desde el suelo terminado; `Z=0` es el suelo terminado.
- `X`: eje horizontal que sale del origen siguiendo el primer segmento de pared
  de referencia, en su dirección documentada.
- `Y`: eje horizontal perpendicular a `X` elegido para formar un sistema
  dextrógiro con `Z`; las paredes no tienen que ser paralelas a los ejes.
- La frontera se describe en sentido antihorario vista desde arriba. Los
  segmentos se orientan con el interior a su izquierda; esta convención permite
  distinguir retranqueos y validar la orientación sin asumir ángulos rectos.

### Regla reproducible para elegir el origen

1. Preferir una esquina interior permanente, claramente identificable y sin un
   hueco que empiece en la propia esquina.
2. Si existe una entrada inequívoca, recorrer la frontera desde el umbral hacia
   el interior y elegir la primera esquina del lado derecho; registrar la regla,
   la entrada y los segmentos adyacentes.
3. Si no hay entrada inequívoca, elegir el extremo de la pared de referencia más
   larga e ininterrumpida; en empate, usar la esquina con el identificador de
   captura menor y documentar el desempate.
4. Si ninguna opción es clara, no elegir visualmente: registrar varios candidatos
   y dejar la elección pendiente de aprobación humana.

El archivo debe guardar `corner_id`, `wall_ids`, `selection_rule` y el punto
local. El generador no puede inferir silenciosamente otro origen.

## Decisión de formato: JSON frente a YAML

Se adopta JSON v1 como formato canónico de medidas.

| Criterio | JSON | YAML |
| --- | --- | --- |
| Parseo | Estándar y disponible en Python sin dependencia adicional | Depende de una librería y su configuración |
| Ambigüedad | Tipos y sintaxis más estrictos | Tipos implícitos, anchors y dialectos pueden sorprender |
| Determinismo | Serialización canónica y hash sencillos | Requiere fijar parser y reglas adicionales |
| Lectura humana | Algo más verboso, pero claro con indentación | Más compacto y admite comentarios |
| Evolución | Compatible con validadores y herramientas externas | Flexible, con mayor superficie de interpretación |

La legibilidad se conserva con UTF-8, dos espacios, arrays ordenados por
identificador estable y una serialización determinista. JSON evita que un valor
como `no`, `01` o una fecha cambie de tipo según el parser. YAML no forma parte
del formato canónico v1; solo podrá existir en el futuro como vista o export
opcional y nunca como otra fuente de verdad.

## Modelo de datos propuesto: schema v1

Cada archivo representa una habitación. La estructura inicial es deliberadamente
pequeña y extensible:

```json
{
  "schema_version": "1.0",
  "room_id": "living_room",
  "name": "Nombre humano de la habitación",
  "units": "m",
  "measured_at": "2026-09-06",
  "capture": {
    "method": "mixed",
    "session_id": "capture-001",
    "notes": "Métodos y orden de captura"
  },
  "coordinate_system": {
    "origin": {
      "type": "interior_floor_corner",
      "corner_id": "corner-01",
      "point_m": [0.0, 0.0, 0.0],
      "wall_ids": ["wall-01", "wall-08"],
      "selection_rule": "entry_right_first_clear_corner"
    },
    "axes": {
      "x": "wall-01_start_to_end",
      "y": "right_handed_perpendicular_to_x",
      "z": "vertical_up",
      "handedness": "right"
    },
    "boundary_winding": "counterclockwise_viewed_from_above"
  },
  "dimensions": {
    "height": {
      "value_m": 2.5,
      "status": "measured",
      "uncertainty_m": 0.005,
      "method": "laser",
      "source_id": "capture-001-height"
    }
  },
  "walls": [
    {
      "id": "wall-01",
      "start_m": [0.0, 0.0, 0.0],
      "end_m": [5.0, 0.0, 0.0],
      "length": {
        "value_m": 5.0,
        "status": "measured",
        "uncertainty_m": 0.005,
        "method": "tape",
        "source_id": "capture-001-wall-01"
      },
      "thickness": {
        "status": "unknown",
        "method": "not_captured",
        "note": "No se rellena hasta medirla"
      }
    }
  ],
  "openings": {
    "doors": [],
    "windows": []
  },
  "fixed_elements": [],
  "notes": [],
  "evidence": []
}
```

### Campos obligatorios y opcionales

En v1 son obligatorios `schema_version`, `room_id`, `name`, `units`,
`measured_at`, `capture`, `coordinate_system`, `walls` y `openings`.
`capture.method`, la información del origen y los ejes también son obligatorios;
`capture.session_id` y `capture.notes` son opcionales. `walls` debe contener al
menos un segmento y `openings` debe conservar las listas `doors` y `windows`,
aunque estén vacías.

`dimensions`, `fixed_elements`, `notes` y `evidence` son opcionales. Si se
incluye `fixed_elements`, cada elemento debe cumplir su contrato y los
enchufes/interruptores siguen siendo opcionales dentro de esa colección. Si se
omite una colección opcional, equivale a una colección vacía, no a una medida
desconocida. Una propiedad métrica no disponible se expresa dentro de su objeto
de medida con `status: "unknown"` y sin `value_*`.

### Objeto de medida

Las longitudes, alturas, offsets, espesores y dimensiones usan un objeto común.
El sufijo del campo determina la magnitud: `value_m` para longitudes, `value_m2`
para áreas y `value_deg` para ángulos. No se mezclan unidades dentro de un
objeto:

- `value_m`, `value_m2` o `value_deg`: uno de ellos es obligatorio para
  `measured`, `estimated` y `derived`, según la magnitud del campo.
- `status`: obligatorio y limitado a `measured`, `estimated`, `derived`, `unknown`.
- `uncertainty_m`: obligatorio cuando se conozca o sea relevante; no se inventa
  para `unknown`.
- `method`: método concreto o `not_captured`.
- `source_id`: referencia a una observación, sesión o evidencia cuando aporte
  trazabilidad.
- `note`: contexto humano breve, especialmente para estimaciones.
- `formula` y `depends_on`: obligatorios para `derived`.
- `unknown` no lleva ningún `value_*`; omitir el valor es distinto de medir cero.

Reglas: una medida `estimated` no puede convertirse en `measured` por el
generador; una medida `derived` debe poder recalcularse; una medida `unknown`
impide afirmar una validación exacta del atributo que depende de ella.

### Habitaciones y segmentos

`walls` es una lista ordenada de segmentos, no una caja implícita. Cada segmento
incluye `id`, `start_m`, `end_m`, `length` y un `thickness` opcional. Los puntos
se expresan en el sistema local y heredan por defecto el estado, método,
incertidumbre y `source_id` del segmento. Si un punto tiene una observación
independiente o una incertidumbre distinta, el segmento debe incluir
`start_measurement`/`end_measurement` con el objeto de medida común; si se
calcula a partir de otros datos, debe ser `derived` con `formula` y
`depends_on`. Así tampoco las coordenadas quedan sin trazabilidad. Los
segmentos permiten:

- paredes no paralelas y ángulos distintos de 90°;
- habitaciones en L y retranqueos mediante varios segmentos consecutivos;
- pilares y huecos como elementos anclados a un segmento o como polígonos locales;
- longitudes diferentes sin forzar un rectángulo;
- cierres de frontera y comprobación de auto-intersecciones.

No se requiere un campo de “rectángulo” en v1: una habitación rectangular es
simplemente una secuencia de cuatro segmentos. `dimensions` puede guardar
resúmenes como largo, ancho, altura o área, cada uno con su objeto de medida;
son auxiliares y la lista de segmentos manda sobre esos resúmenes.

## Puertas y ventanas

Los huecos se referencian a una pared/segmento y a su inicio, no a coordenadas
globales arbitrarias. Todos los offsets y dimensiones son objetos de medida.

### Puerta

```json
{
  "id": "door-01",
  "wall_id": "wall-01",
  "distance_from_start": {"value_m": 1.25, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "capture-001-door"},
  "width": {"value_m": 0.82, "status": "measured", "uncertainty_m": 0.003, "method": "laser", "source_id": "capture-001-door"},
  "height": {"value_m": 2.03, "status": "measured", "uncertainty_m": 0.003, "method": "laser", "source_id": "capture-001-door"},
  "depth": {"status": "unknown", "method": "not_captured"},
  "opening_direction": "unknown"
}
```

La validación comprueba que `distance_from_start + width` queda dentro de la
longitud del segmento. `opening_direction` es opcional y no se usa para crear
geometría canónica hasta definir su semántica.

### Ventana

```json
{
  "id": "window-01",
  "wall_id": "wall-02",
  "distance_from_start": {"value_m": 0.80, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "capture-001-window"},
  "width": {"value_m": 1.20, "status": "measured", "uncertainty_m": 0.003, "method": "laser", "source_id": "capture-001-window"},
  "height": {"value_m": 1.00, "status": "measured", "uncertainty_m": 0.003, "method": "laser", "source_id": "capture-001-window"},
  "sill_height": {"value_m": 0.90, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "capture-001-window"},
  "depth": {"status": "unknown", "method": "not_captured"}
}
```

La validación comprueba los límites laterales y `sill_height + height <= room.height`
cuando la altura de la habitación está disponible.

## Pilares, radiadores, enchufes y elementos fijos

`fixed_elements` contiene solo elementos relevantes para la arquitectura o para
la validación de espacio. En v1 se permiten `pillar`, `recess`, `radiator`,
`socket`, `switch` y `fixed`. Los enchufes e interruptores se incluyen solo si
aportan valor al primer caso real; son elementos fijos opcionales y no son
obligatorios para considerar una habitación modelable.

Cada elemento tiene `id`, `type`, un anclaje (`wall_id` y
`distance_from_start`, o un punto/polígono local), dimensiones, altura y medidas
de incertidumbre. Un enchufe o interruptor debe poder registrar como mínimo
`type`, pared/segmento asociado, posición u offset, altura, `status`,
`uncertainty_m` y `note`. No se modelan circuitos, cargas ni cableado en v1.
Un pilar puede anclarse a una pared; un retranqueo se expresa preferentemente
en la secuencia de segmentos para conservar su topología.

## Incertidumbre y trazabilidad

Toda medida relevante debe tener uno de estos estados:

- `measured`: lectura directa de un instrumento o fuente primaria validada.
- `estimated`: aproximación explícita; exige `uncertainty_m` y `note`.
- `derived`: cálculo a partir de otros valores; exige `formula` y `depends_on`.
- `unknown`: no capturada o no fiable; no puede actuar como medida real.

La incertidumbre se expresa en metros como semirango positivo. Si dos lecturas
independientes difieren más que la incertidumbre combinada, se conservan ambas
observaciones o se repite la captura; no se elige silenciosamente la que haga
encajar la geometría. La fuente/evidencia puede ser un identificador de sesión,
un plano verificado o una fotografía con escala, pero una foto sin escala no
convierte una estimación en `measured`.

## Baseline inicial de tolerancias

Son tolerancias operativas iniciales aprobadas para orientar el proyecto, no
garantías universales del instrumento ni un estándar definitivo. Cada medida
concreta puede declarar una incertidumbre distinta; cuando se conozca, esa
incertidumbre explícita prevalece sobre este baseline.

### A. Captura física

- Cinta métrica doméstica: `±0.005 m` en tramos despejados y `±0.010 m` en
  tramos largos, flexibles u obstruidos.
- Medidor láser doméstico adecuado: `±0.002–0.005 m`, condicionado por superficie,
  incidencia, calibración y visibilidad.
- Plano existente, foto, LiDAR o fotogrametría: no reciben una incertidumbre
  universal; se registran como método y se calibran contra anclajes manuales.
- La incertidumbre concreta de cada campo prevalece sobre el valor por defecto.

### B. Validación matemática

- `1e-6 m` se propone solo para aritmética interna, cierre de segmentos,
  comparación de puntos derivados y determinismo del parser/generador.
- Esta tolerancia no representa la precisión de una pared real ni sustituye la
  incertidumbre de captura.
- Un residual mayor que la incertidumbre registrada genera `warning`; un
  residual mayor que `2 × incertidumbre` o que `0.010 m` genera `fail` para
  revisión, salvo una regla aprobada por habitación.

### C. Validación visual

- Es cualitativa y dependiente de resolución/cámara: no debe haber huecos,
  solapes o penetraciones visibles que contradigan los datos.
- Puede anotarse una diferencia de hasta aproximadamente 2 px solo como límite
  de presentación del preview; nunca corrige el dato ni reemplaza la validación
  numérica.
- El preview debe registrar resolución, encuadre y qué elementos se inspeccionaron.

## Métodos de captura

| Método | Precisión esperable | Ventajas | Riesgos | Papel recomendado |
| --- | --- | --- | --- | --- |
| Cinta métrica | ±5–10 mm según tramo y tensión | Barata, disponible, suficiente para empezar | Curvatura, lectura oblicua, referencias difíciles | Método canónico mínimo; repetir medidas críticas |
| Medidor láser | Aproximadamente ±2–5 mm en condiciones buenas | Rápido y útil para diagonales/alturas | Reflejos, superficies oscuras, punto final ambiguo | Preferido cuando se pueda contrastar con cinta |
| Plano existente | Variable; depende de fecha y escala | Da contexto y nombres de estancias | Reformas, redondeos y errores heredados | Evidencia secundaria; validar en casa |
| Fotos | No mide exactamente sin escala y calibración | Registra contexto, posiciones y estado | Perspectiva, privacidad, oclusiones | Referencia visual y trazabilidad, no autoridad métrica |
| LiDAR/escaneo móvil | Variable; bueno para forma global, peor en detalles/oclusiones | Captura rápida de geometría amplia | Drift, superficies y software propietario | Acelerador contrastado con anclajes manuales |
| Fotogrametría | Variable según escala, textura y control | Útil para superficies y contexto | Escala/orientación ambiguas, iluminación y privacidad | Complemento; nunca única fuente sin escala/control |

La geometría canónica debe poder construirse con cinta métrica y un procedimiento
repetible; LiDAR o fotogrametría son opcionales y no requisitos del proyecto.

## Evidencia fotográfica

Las fotos sirven para identificar paredes, huecos, obstáculos y estado visual.
No se extrae una medida exacta de una foto sin una escala conocida, puntos de
control y una incertidumbre documentada.

La convención futura será `assets/references/<room_id>/` para referencias
seleccionadas. Las fotos personales originales, EXIF con ubicación, rostros,
documentos y planos privados deben permanecer fuera del repositorio salvo una
decisión explícita. Una referencia versionada debe tener un `evidence_id`,
descripción, fecha, escala conocida (`true/false`) y relación con las medidas;
no se añadirá una foto solo para rellenar evidencia.

## Generación futura en Blender

La arquitectura objetivo es:

```text
measurement file → parser/validator → bpy generator → .blend
```

- El parser carga JSON v1, normaliza unidades y rechaza estados/IDs inválidos.
- El validador comprueba topología, límites, incertidumbre, unidades y reglas
  geométricas antes de crear la escena.
- El generador es determinista, regenerable y no depende de ajustes manuales
  ocultos. Acepta una entrada validada y produce una variante o escena controlada.
- La arquitectura se separa de decoración: la estructura y huecos no dependen
  de mobiliario, materiales o assets.
- Las colecciones futuras deben distinguir arquitectura medida/derivada,
  huecos, elementos fijos y decoración.
- Las transformaciones se aplican y se verifican tras crear la geometría.
- Nunca se sobrescribe una escena canónica sin snapshot, destino explícito y
  autorización.
- El generador debe conservar el vínculo entre objeto y `source_id` cuando sea
  posible mediante nombres/metadata no ambiguos.

## Validaciones futuras

El validador y el generador deberán cubrir, como mínimo:

- JSON válido, `schema_version` compatible e IDs únicos.
- Unidades explícitas y campos con sufijos correctos.
- Segmentos conectados dentro de la tolerancia matemática.
- Frontera cerrada, orientación consistente y ausencia de auto-intersecciones
  evidentes.
- Paredes no paralelas, L, retranqueos, pilares y segmentos múltiples.
- Huecos referenciados a paredes existentes y contenidos en sus límites.
- Alturas positivas y huecos por debajo de la altura conocida.
- `estimated` con incertidumbre/notas y `derived` con fórmula/dependencias;
  `unknown` nunca pasa como valor real.
- Comparación datos ↔ Blender usando incertidumbre de captura, no `1e-6 m`
  como tolerancia física.
- Regeneración determinista: mismo input y versión producen la misma firma de
  geometría y el mismo informe.
- Revisión visual de preview sin que esta sustituya la comprobación numérica.

## Primer test del slice: fixture conceptual 002

Antes del salón real se define un fixture sintético distinto del fixture 001.
No se crea todavía como archivo; el siguiente JSON describe el contenido que
deberá materializarse en una fase posterior, por ejemplo en
`measurements/fixtures/002-room-measurement.json`.

```json
{
  "schema_version": "1.0",
  "room_id": "fixture_002_recessed_room",
  "name": "Fixture sintético con retranqueo",
  "units": "m",
  "measured_at": "2026-09-06",
  "capture": {
    "method": "tape",
    "session_id": "synthetic-002",
    "notes": "Datos sintéticos; no representan una vivienda"
  },
  "coordinate_system": {
    "origin": {
      "type": "interior_floor_corner",
      "corner_id": "corner-01",
      "point_m": [0.0, 0.0, 0.0],
      "wall_ids": ["wall-01", "wall-08"],
      "selection_rule": "longest_uninterrupted_reference_wall"
    },
    "axes": {
      "x": "wall-01_start_to_end",
      "y": "right_handed_perpendicular_to_x",
      "z": "vertical_up",
      "handedness": "right"
    },
    "boundary_winding": "counterclockwise_viewed_from_above"
  },
  "dimensions": {
    "height": {
      "value_m": 2.48,
      "status": "estimated",
      "uncertainty_m": 0.03,
      "method": "existing_plan",
      "source_id": "synthetic-002-height",
      "note": "Estimación deliberada para probar el flujo de incertidumbre"
    },
    "floor_area": {
      "value_m2": 11.7,
      "status": "derived",
      "method": "shoelace_polygon",
      "source_id": "synthetic-002-boundary",
      "formula": "area from ordered wall endpoints",
      "depends_on": ["wall-01", "wall-02", "wall-03", "wall-04", "wall-05", "wall-06", "wall-07", "wall-08"]
    }
  },
  "walls": [
    {"id": "wall-01", "start_m": [0.0, 0.0, 0.0], "end_m": [4.0, 0.0, 0.0], "length": {"value_m": 4.0, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "synthetic-002-wall-01"}, "thickness": {"status": "unknown", "method": "not_captured"}},
    {"id": "wall-02", "start_m": [4.0, 0.0, 0.0], "end_m": [4.0, 3.0, 0.0], "length": {"value_m": 3.0, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "synthetic-002-wall-02"}, "thickness": {"status": "unknown", "method": "not_captured"}},
    {"id": "wall-03", "start_m": [4.0, 3.0, 0.0], "end_m": [2.5, 3.0, 0.0], "length": {"value_m": 1.5, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "synthetic-002-wall-03"}, "thickness": {"status": "unknown", "method": "not_captured"}},
    {"id": "wall-04", "start_m": [2.5, 3.0, 0.0], "end_m": [2.5, 2.7, 0.0], "length": {"value_m": 0.3, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "synthetic-002-wall-04"}, "thickness": {"status": "unknown", "method": "not_captured"}},
    {"id": "wall-05", "start_m": [2.5, 2.7, 0.0], "end_m": [1.5, 2.7, 0.0], "length": {"value_m": 1.0, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "synthetic-002-wall-05"}, "thickness": {"status": "unknown", "method": "not_captured"}},
    {"id": "wall-06", "start_m": [1.5, 2.7, 0.0], "end_m": [1.5, 3.0, 0.0], "length": {"value_m": 0.3, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "synthetic-002-wall-06"}, "thickness": {"status": "unknown", "method": "not_captured"}},
    {"id": "wall-07", "start_m": [1.5, 3.0, 0.0], "end_m": [0.0, 3.0, 0.0], "length": {"value_m": 1.5, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "synthetic-002-wall-07"}, "thickness": {"status": "unknown", "method": "not_captured"}},
    {"id": "wall-08", "start_m": [0.0, 3.0, 0.0], "end_m": [0.0, 0.0, 0.0], "length": {"value_m": 3.0, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "synthetic-002-wall-08"}, "thickness": {"status": "unknown", "method": "not_captured"}}
  ],
  "openings": {
    "doors": [
      {"id": "door-01", "wall_id": "wall-01", "distance_from_start": {"value_m": 1.0, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "synthetic-002-door"}, "width": {"value_m": 0.8, "status": "measured", "uncertainty_m": 0.003, "method": "laser", "source_id": "synthetic-002-door"}, "height": {"value_m": 2.1, "status": "measured", "uncertainty_m": 0.003, "method": "laser", "source_id": "synthetic-002-door"}, "depth": {"value_m": 0.12, "status": "estimated", "uncertainty_m": 0.02, "method": "visual", "source_id": "synthetic-002-door"}}
    ],
    "windows": [
      {"id": "window-01", "wall_id": "wall-02", "distance_from_start": {"value_m": 0.8, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "synthetic-002-window"}, "width": {"value_m": 1.0, "status": "measured", "uncertainty_m": 0.003, "method": "laser", "source_id": "synthetic-002-window"}, "height": {"value_m": 1.0, "status": "measured", "uncertainty_m": 0.003, "method": "laser", "source_id": "synthetic-002-window"}, "sill_height": {"value_m": 0.9, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "synthetic-002-window"}, "depth": {"status": "unknown", "method": "not_captured"}}
    ]
  },
  "fixed_elements": [
    {"id": "pillar-01", "type": "pillar", "wall_id": "wall-02", "distance_from_start": {"value_m": 1.8, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "synthetic-002-pillar"}, "dimensions": {"width": {"value_m": 0.2, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "synthetic-002-pillar"}, "depth": {"value_m": 0.2, "status": "measured", "uncertainty_m": 0.005, "method": "tape", "source_id": "synthetic-002-pillar"}, "height": {"value_m": 2.48, "status": "estimated", "uncertainty_m": 0.03, "method": "existing_plan", "source_id": "synthetic-002-height"}}}
  ],
  "notes": ["El retranqueo está formado por wall-04, wall-05 y wall-06.", "El fixture prueba una medida estimated y otra derived."],
  "evidence": [{"id": "synthetic-002-boundary", "kind": "synthetic_spec", "scale_known": true, "path": null}]
}
```

El fixture prueba una habitación no rectangular con retranqueo, un pilar, puerta,
ventana, una medida `estimated` y otra `derived`. No contiene decoración ni
datos personales.

## Criterios de aceptación

Este slice será válido cuando la documentación y las decisiones permitan ejecutar
las fases posteriores sin reinterpretación silenciosa:

1. El formato canónico está definido y JSON queda justificado frente a YAML.
2. El schema v1 y sus estados de medida están definidos con reglas de evolución.
3. La autoridad de `measurements/` frente a Blender queda explícita.
4. Las unidades, precisión almacenada, incertidumbre y tolerancias están separadas.
5. El origen, ejes, orientación y regla de selección de esquina son deterministas.
6. El modelo soporta rectángulos, paredes no paralelas, L, retranqueos, pilares,
   huecos y segmentos múltiples.
7. Puertas y ventanas se referencian por pared/segmento y offset.
8. Los métodos de captura y la política de fotos están documentados sin exigir LiDAR.
9. La arquitectura parser/validator/generator y sus validaciones futuras están definidas.
10. El fixture sintético 002 conceptual incluye retranqueo/pilar, `estimated` y `derived`.
11. El plan separa diseño, fixture, validador, generador, validaciones y procedimiento real.
12. El flujo no depende de rutas personales ni modifica todavía `measurements/` o Blender.

## Riesgos T2 y mitigaciones

| Riesgo | Mitigación |
| --- | --- |
| Error de medición | Repetir medidas críticas, guardar método/incertidumbre y conservar lecturas discrepantes. |
| Falsa precisión | Separar decimales almacenados de incertidumbre real; no usar más decimales como autoridad. |
| Paredes inconsistentes | Validar cierres, longitudes y conexiones; producir warning/fail, nunca ajustar silenciosamente. |
| Ángulos no rectos | Usar segmentos con puntos locales y no un modelo rectangular implícito. |
| Huecos mal referenciados | Anclar puertas/ventanas a `wall_id` y offset con límites verificables. |
| Unidades mezcladas | Metros en almacenamiento, sufijos explícitos y `METRIC`/`scale_length=1.0` en Blender. |
| Origen ambiguo | Regla registrada, IDs y aprobación humana si no existe esquina clara. |
| Arquitectura y decoración mezcladas | Colecciones y fases separadas; este slice solo define arquitectura medida. |
| Datos personales en fotos/planos | Referencias sanitizadas, originales fuera del repo y escala/evidencia explícitas. |
| Pérdida de trazabilidad | `source_id`, método, nota, fórmula y dependencias por medida. |
| Dependencia excesiva de escaneos | Cinta métrica como camino mínimo y escaneos solo como complemento contrastado. |
| Corregir datos para Blender | `measurements/` manda; discrepancias generan revisión. |

## Invariantes

- `measurements/` manda sobre Blender.
- Ninguna estimación se etiqueta como `measured`.
- Todas las unidades son explícitas y la unidad canónica es el metro.
- El sistema de coordenadas y el origen son deterministas y están registrados.
- La geometría futura es regenerable a partir del archivo validado.
- El flujo no depende de rutas personales.
- Blender no redefine medidas reales.
- Toda discrepancia queda registrada como warning/fail o decisión explícita.
- Las fotos no sustituyen medidas sin escala conocida y trazabilidad.
- No se modela el salón real en este slice.

## Decisiones pendientes

- Completar y aprobar el contrato detallado de schema v1 antes de materializar el
  fixture sintético.
- Revisar el baseline de tolerancias con evidencia de una primera sesión real,
  sin confundir esa revisión con la precisión almacenada o matemática.
- Mantener sin decidir el nombre y la ubicación exacta del primer archivo real:
  solo se abrirá esa decisión después de completar schema v1, fixture sintético,
  parser/validator, generación Blender sintética y validación determinista.
- Aprobar la primera implementación del parser/validador y del generador Blender.
