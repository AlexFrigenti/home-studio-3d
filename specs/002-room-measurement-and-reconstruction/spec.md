# Especificación: Room Measurement and Reconstruction

> Clasificación: T2 — contrato canónico de medidas, unidades y coordenadas
> Rama: `spec/002-room-measurement-and-reconstruction`
> Estado: schema JSON v1 y v1.1, fixtures sintéticos, validador y generación de planes implementados; `measurements/rooms/living-room-main.json` contiene ahora la altura general y las medidas verticales autorizadas de P1/P2/V1/V2, pero no se ha regenerado Blender tras esa actualización.

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
- Arquitectura `measurement file → parser/validator → bpy generator → .blend`.
- Schema JSON v1 estricto en `measurements/schema/room-v1.schema.json`.
- Fixture sintético en `measurements/fixtures/room-v1-synthetic.json`.
- Validación estructural/determinista mínima y tests con Python estándar.
- Generador Blender v1 para el fixture, escena derivada, validación numérica y preview técnico.
- Validaciones futuras, riesgos, invariantes y decisiones pendientes.

### Fuera de alcance

- Transcribir o versionar nuevas medidas reales en `measurements/` fuera de autorizaciones específicas; la altura general autorizada de `living-room-main` ya está registrada bajo `measurements/`.
- Modelar el salón real o modificar cualquier escena canónica.
- Generar geometría a partir de medidas reales o modelar el salón real.
- Integración MCP o cambios en la configuración de Blender/Codex.
- Modelar el salón real o añadir nuevas medidas reales bajo `measurements/` fuera de las autorizaciones específicas del slice.
- Instalar Blender, MCP, Python, paquetes, addons, LiDAR o herramientas de captura.
- Cambiar `README.md`, `PROJECT_CONTEXT.md` o la configuración local; no modificar
  otras medidas reales fuera de los campos autorizados de este slice.
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
- Las coordenadas terminan en `_m`; las magnitudes escalares usan las unidades
  declaradas por el campo y `units: "m"` como base (por ejemplo, `floor_area`
  representa m²).
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

El archivo debe guardar `corner_id`, `adjacent_segment_ids`, `selection_rule` y
el punto local. El generador no puede inferir silenciosamente otro origen.

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

## Modelo de datos implementado: schema v1

Cada archivo representa una habitación y se valida contra
`measurements/schema/room-v1.schema.json`. La estructura canónica de nivel
superior es:

- `schema_version`, `room_id`, `name`, `units`, `measured_at` y
  `measurement_method`.
- `coordinate_system`, `height` y `boundary.segments`.
- `openings.doors` y `openings.windows`.
- `fixed_elements` y `notes`.
- `floor_area` es opcional y puede ser una medida `derived`.

El fixture ejecutable de este slice, que muestra todos los estados y un
retranqueo, está en `measurements/fixtures/room-v1-synthetic.json`. El JSON
real autorizado de `living-room-main` conserva la altura suelo-techo medida e
incorpora las medidas verticales autorizadas de P1, P2, V1 y V2. V3 y V4 no
añaden todavía medidas verticales canónicas.

### Evolucion aditiva room-v1.1

Cuando una captura observada necesita una geometria reconciliada para cerrar
el perimetro, `measurements/schema/room-v1.1.schema.json` permite conservar
ambas capas. `length` sigue siendo la observacion fisica y
`reconciled_geometry.length` es un valor `derived` trazable que el generador
puede usar como longitud efectiva. El bloque `boundary.reconciliation`
documenta residuos, tolerancias, segmentos ajustados y dependencias; no hay
optimizacion automatica ni sobrescritura silenciosa. Los archivos v1 siguen
siendo validos e intactos para capturas que no necesitan reconciliacion.

### Campos obligatorios y opcionales

En v1 son obligatorios `schema_version`, `room_id`, `name`, `units`,
`measured_at`, `measurement_method`, `coordinate_system`, `height`, `boundary`,
`openings`, `fixed_elements` y `notes`. La información del origen, los ejes,
`boundary.winding` y los segmentos también son obligatorios; `boundary.segments`
debe contener al menos tres segmentos y `openings` debe conservar las listas
`doors` y `windows`, aunque estén vacías.

`floor_area` es opcional. Si se incluye `fixed_elements`, cada elemento debe
cumplir su contrato y los enchufes/interruptores siguen siendo opcionales dentro
de esa colección. Una propiedad métrica no disponible se expresa dentro de su
objeto de medida con `status: "unknown"` y sin `value`.

### Objeto de medida

Las longitudes, alturas, offsets, espesores y dimensiones usan un objeto común.
El campo que contiene la medida determina su magnitud; el objeto usa siempre
`value` y `uncertainty` numéricos en las unidades declaradas. No se mezclan
unidades dentro de un objeto:

- `value`: obligatorio para `measured`, `estimated` y `derived`.
- `status`: obligatorio y limitado a `measured`, `estimated`, `derived`, `unknown`.
- `uncertainty`: obligatorio cuando se conozca o sea relevante; no se inventa
  para `unknown`.
- `method`: método concreto o `not_captured`.
- `source_id`: referencia a una observación, sesión o evidencia cuando aporte
  trazabilidad.
- `note`: contexto humano breve, especialmente para estimaciones.
- `formula` y `depends_on`: obligatorios para `derived`.
- `unknown` no lleva `value`; omitir el valor es distinto de medir cero.

Reglas: una medida `estimated` no puede convertirse en `measured` por el
generador; una medida `derived` debe poder recalcularse; una medida `unknown`
impide afirmar una validación exacta del atributo que depende de ella.

### Habitaciones y segmentos

`boundary.segments` es una lista ordenada de segmentos, no una caja implícita. Cada segmento
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
simplemente una secuencia de cuatro segmentos. `floor_area` puede guardar un
resumen derivado, pero los segmentos mandan sobre cualquier resumen.

## Puertas y ventanas

Los huecos se referencian a una pared/segmento y a su inicio, no a coordenadas
globales arbitrarias. Todos los offsets y dimensiones son objetos de medida.

### Puerta

```json
{
  "id": "door-01",
  "wall_id": "wall-01",
  "offset": {"value": 1.25, "status": "measured", "uncertainty": 0.005, "method": "tape", "source_id": "capture-001-door"},
  "width": {"value": 0.82, "status": "measured", "uncertainty": 0.003, "method": "laser", "source_id": "capture-001-door"},
  "height": {"value": 2.03, "status": "measured", "uncertainty": 0.003, "method": "laser", "source_id": "capture-001-door"},
  "depth": {"status": "unknown", "method": "not_captured"},
  "opening_direction": "unknown"
}
```

La validación comprueba que `offset + width` queda dentro de la
longitud del segmento. `opening_direction` es opcional y no se usa para crear
geometría canónica hasta definir su semántica.

### Ventana

```json
{
  "id": "window-01",
  "wall_id": "wall-02",
  "offset": {"value": 0.80, "status": "measured", "uncertainty": 0.005, "method": "tape", "source_id": "capture-001-window"},
  "width": {"value": 1.20, "status": "measured", "uncertainty": 0.003, "method": "laser", "source_id": "capture-001-window"},
  "height": {"value": 1.00, "status": "measured", "uncertainty": 0.003, "method": "laser", "source_id": "capture-001-window"},
  "sill_height": {"value": 0.90, "status": "measured", "uncertainty": 0.005, "method": "tape", "source_id": "capture-001-window"},
  "depth": {"status": "unknown", "method": "not_captured"}
}
```

La validación comprueba los límites laterales y `sill_height + window.height <=
room.height` cuando la altura de la habitación está disponible.

## Pilares, radiadores, enchufes y elementos fijos

`fixed_elements` contiene solo elementos relevantes para la arquitectura o para
la validación de espacio. En v1 se permiten `pillar`, `recess`, `radiator`,
`socket`, `switch` y `fixed`. Los enchufes e interruptores se incluyen solo si
aportan valor al primer caso real; son elementos fijos opcionales y no son
obligatorios para considerar una habitación modelable.

Cada elemento tiene `id`, `type`, un anclaje (`wall_id` y `offset`, o un punto
local), dimensiones opcionales, altura y medidas
de incertidumbre. Un enchufe o interruptor debe poder registrar como mínimo
`type`, pared/segmento asociado, posición u offset, altura, `status`,
`uncertainty` y `note`. No se modelan circuitos, cargas ni cableado en v1.
Un pilar puede anclarse a una pared; un retranqueo se expresa preferentemente
en la secuencia de segmentos para conservar su topología.

## Incertidumbre y trazabilidad

Toda medida relevante debe tener uno de estos estados:

- `measured`: lectura directa de un instrumento o fuente primaria validada.
- `estimated`: aproximación explícita; exige `uncertainty` y `note`.
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

## Generación Blender v1 y límites futuros

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
- Las colecciones deben distinguir arquitectura medida/derivada,
  huecos, elementos fijos y decoración.
- Las transformaciones se aplican y se verifican tras crear la geometría.
- Nunca se sobrescribe una escena canónica sin snapshot, destino explícito y
  autorización.
- El generador debe conservar el vínculo entre objeto y `source_id` cuando sea
  posible mediante nombres/metadata no ambiguos.

Este slice materializa el primer generador en
`blender/scripts/measurements/generate_room.py`. Consume únicamente el fixture
validado y guarda la escena derivada en
`blender/scenes/tests/002-room-v1-generated.blend`. Las paredes y el suelo se
construyen desde los puntos ordenados de `boundary.segments`; el espesor
desconocido usa un fallback de proxy explícito de `0.10 m`, conservando el
estado original `unknown`. Las puertas y ventanas se representan como proxies
geométricos coloreados y colocados sobre su segmento, no como booleanos que
recorten la pared. Los elementos fijos usan proxies simples y metadata de
trazabilidad. Esta limitación queda documentada y deberá resolverse antes de
admitir geometría real que requiera huecos constructivos.

## Cobertura actual y validaciones futuras

El validador y el generador cubren estas reglas para el fixture sintético; las
reglas deberán ampliarse antes de admitir datos reales adicionales o geometría real:

- JSON válido, `schema_version` compatible e IDs únicos.
- Unidades explícitas y semántica de magnitudes coherente con cada campo.
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

## Primer test del slice: fixture sintético 002

El fixture ejecutable está en `measurements/fixtures/room-v1-synthetic.json` y
valida contra el schema v1. Representa una habitación sintética de
aproximadamente 5 × 4 m y altura 2.50 m, con ocho segmentos de boundary, un
retranqueo de 1 × 0.3 m, una puerta, una ventana y un enchufe opcional como
elemento fijo. Incluye medidas `measured`, una altura `estimated` con
incertidumbre explícita, una superficie `derived` con fórmula y dependencias, y
profundidad `unknown` sin valor fingido. No contiene decoración, datos reales ni
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
9. La arquitectura parser/validator/generator y sus validaciones futuras están definidas, con un primer generador sintético ejecutable.
10. El fixture sintético 002 versionado incluye retranqueo, `estimated`, `derived` y un elemento fijo opcional.
11. El plan separa diseño, fixture, validador, generador, validaciones y procedimiento real.
12. El flujo no depende de rutas personales, no contiene medidas reales adicionales fuera de las autorizaciones explícitas para `living-room-main`, no modifica MCP/Codex y mantiene fuera de alcance el modelado real.
13. La escena sintética derivada conserva unidades, colecciones, metadata, determinismo y validación numérica documentados.

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
- La geometría derivada es regenerable a partir del archivo validado.
- El flujo no depende de rutas personales.
- Blender no redefine medidas reales.
- Toda discrepancia queda registrada como warning/fail o decisión explícita.
- Las fotos no sustituyen medidas sin escala conocida y trazabilidad.
- No se modela el salón real en este slice.

## Decisiones pendientes

- Revisar el contrato implementado de schema v1 antes de admitir datos reales.
- Revisar la estrategia de proxies de openings y fallback de espesores antes de
  admitir geometría real.
- Revisar el baseline de tolerancias con evidencia de una primera sesión real,
  sin confundir esa revisión con la precisión almacenada o matemática.
- Mantener fuera de alcance nuevas medidas reales y decisiones de modelado fuera
  de las autorizaciones explícitas; el archivo canónico de `living-room-main` y
  su ubicación ya están decididos para la altura y las lecturas verticales
  autorizadas. V3/V4 y otras capturas siguen pendientes.
- Revisar y aprobar la implementación sintética del parser/validador y del
  generador Blender antes de admitir datos reales adicionales o generar una
  escena real actualizada.
