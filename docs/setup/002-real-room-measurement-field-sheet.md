# Hoja de campo para la primera medición real de `room-v1`

Estado: plantilla reutilizable para imprimir o rellenar digitalmente. No contiene
datos reales, no fija decisiones pendientes y no autoriza la captura, la
transcripción, el versionado de datos o fotografías, la validación ni Blender/MCP.

La hoja debe seguir el procedimiento canónico de
`docs/setup/002-real-room-measurement-procedure.md`. La unidad canónica del
pipeline y del JSON v1 es el metro (`m`). Si una lectura física se toma en
centímetros, conservar la lectura original, anotar explícitamente la unidad y
registrar su conversión a metros antes de transcribirla.

Una copia cumplimentada es evidencia primaria de campo. No se incorpora al
repositorio junto con datos reales sin autorización específica posterior.

## Cómo usar esta hoja

La hoja separa tres momentos para evitar que una decisión pendiente se confunda
con una lectura de campo:

1. **Decisiones previas a la sesión:** identidad, sesión, instrumentos,
   tolerancias, política fotográfica y ruta prevista del JSON. Se completan o se
   dejan explícitamente como `PENDIENTE` antes de empezar a medir.
2. **Captura in situ:** perímetro, controles, alturas, huecos, elementos fijos,
   fotografías y discrepancias. Se registran en las secciones D–L con sus IDs,
   unidades, estados, incertidumbres y `source_id`.
3. **Autorizaciones posteriores:** transcripción, versionado, validator y
   Blender/MCP. Se registran únicamente en la sección M; rellenar la hoja no las
   concede.

Para imprimir, usar orientación horizontal y duplicar las páginas de una
sección si faltan filas. En formato digital, duplicar filas conservando la
misma convención de IDs.

## A. Identidad de la sesión

| Campo | Valor |
| --- | --- |
| `room_id` |  |
| Nombre humano de la habitación |  |
| `session_id` |  |
| Fecha (`YYYY-MM-DD`) |  |
| Operador |  |
| Ubicación lógica/no sensible, si procede |  |
| Versión del procedimiento utilizado |  |
| Política fotográfica aplicable |  |
| Ruta prevista del JSON real (decisión previa) |  |
| Observaciones de identidad |  |

El `room_id` debe ser estable, estar en minúsculas y no contener espacios ni
acentos. Si todavía no está aprobado, dejarlo vacío y registrar la decisión
como pendiente; no inventar un identificador para la captura.

## B. Instrumentación y unidades

| Campo | Valor | Observaciones |
| --- | --- | --- |
| Instrumento principal |  |  |
| Instrumento secundario/control |  |  |
| Resolución indicada por el instrumento |  |  |
| Tolerancia/incertidumbre adoptada |  |  |
| Método de medición |  |  |
| Unidad de trabajo del pipeline | `m` | Fijada por schema v1 |
| Unidad física usada en cada lectura |  | `m`, `cm` u otra, siempre explícita |
| Regla de conversión a metros |  |  |

No rellenar instrumentos, método o tolerancias hasta que estén decididos para
la sesión. Una lectura en centímetros no se copia como si ya estuviera en
metros: conservar ambos valores y su conversión.

## C. Sistema de referencia

| Campo | Registro |
| --- | --- |
| Descripción del origen |  |
| Esquina inicial / `corner_id` |  |
| Paredes adyacentes al origen |  |
| Regla de selección del origen |  |
| Eje `+X` |  |
| Eje `+Y` |  |
| Eje `+Z` | Vertical hacia arriba |
| Winding | Antihorario visto desde arriba |
| Croquis manual | Adjuntar o dibujar fuera de esta plantilla |
| Regla de etiquetado de esquinas |  |
| Regla de etiquetado de segmentos |  |

Usar dos niveles de identificación, sin mezclarlos:

- **Notación de campo:** `C0` es la esquina inicial, `C1` la siguiente, y así
  sucesivamente. `S0` es siempre el segmento `C0→C1`, `S1` es `C1→C2`, etc.; el
  último segmento vuelve a `C0`.
- **Etiqueta compatible con schema:** marcar físicamente y registrar la esquina
  inicial como `corner-01`, luego `corner-02`, `corner-03`, etc. Los IDs que se
  transcriban al schema deben cumplir su patrón en minúsculas. Registrar la
  correspondencia `C0 ↔ corner-01` y `S0 ↔ ID de segmento` en la hoja; no copiar
  automáticamente `C0`/`S0` como IDs JSON si no cumplen el contrato.

Cada segmento une dos esquinas consecutivas. El recorrido geométrico es
antihorario, con el interior a la izquierda; no depende de estar mirando hacia
la puerta.

## D. Perímetro

Registrar un segmento por cada tramo recto y por cada cambio de dirección,
retranqueo, saliente o transición alrededor de un pilar que forme parte del
boundary. Los offsets posteriores se miden desde el extremo inicial del
segmento.

| ID de campo (`S0`, `S1`...) | Esquina inicial (`C0`, `C1`...) | Esquina final | Lectura | Unidad original | Valor convertido a metros | Estado | Incertidumbre (m) | `source_id` | Observaciones/correspondencia schema |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |

Comprobaciones del perímetro:

- [ ] La cadena de segmentos conecta todos los extremos.
- [ ] El último segmento cierra contra `corner-01`.
- [ ] El residual de cierre está anotado sin redistribuirlo silenciosamente.
- [ ] Cada retranqueo, saliente, pilar de contorno o cambio de dirección tiene ID.
- [ ] Las medidas que no se pueden obtener con confianza están como `unknown` o
      pendientes, no como cero.

En `Observaciones/correspondencia schema`, anotar el tipo de tramo
(`recto`, `retranqueo`, `saliente` o `pilar de contorno`) y la correspondencia
entre el ID corto `Sx` y el ID de segmento que se use finalmente en el JSON.
Un retranqueo o saliente que afecte al boundary se representa como uno o más
segmentos consecutivos; un pilar interior que no forme parte del boundary se
registra en I.

## E. Controles geométricos y redundancias

| ID control | Tipo (`diagonal`, repetición, etc.) | Referencias (esquinas/segmentos) | Lectura 1 | Unidad | Lectura 2 / redundante | Unidad | Discrepancia | Tolerancia admitida | Resolución/decisión | `source_id` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |

Incluir, cuando proceda, diagonales de zonas ambiguas, mediciones repetidas de
tramos largos u obstruidos y contrastes entre instrumentos. Si una discrepancia
persiste por encima de la incertidumbre combinada, conservar las lecturas,
repetir la captura y registrar la decisión; no escoger el valor que haga cerrar
el polígono. Para una diagonal, asignar un ID de control, escribir
`tipo=diagonal`, anotar las dos referencias inequívocas y conservar ambas
lecturas si se repite.

## F. Alturas y cambios de cota

### Altura principal

| Campo | Lectura | Unidad original | Valor en metros | Estado | Incertidumbre (m) | `source_id` | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Altura principal |  |  |  |  |  |  |  |

### Lecturas repetidas y zonas

| Zona/punto | Lectura | Unidad | Valor en metros | Estado | Incertidumbre (m) | `source_id` | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |

### Cambios de cota, vigas y falsos techos

| ID/zona | Tipo de cambio | Referencia física | Lectura/cota | Unidad | Estado | Incertidumbre (m) | `source_id` | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |

Schema v1 representa una única cota principal en `height`. Las lecturas
adicionales, vigas, falsos techos y cambios no estructurados completamente se
conservan como evidencia de campo y notas hasta que exista una decisión de
contrato. No colapsar varias cotas en una sola sin documentar la regla.

## G. Puertas

El offset se mide desde el extremo inicial de `Sx` hasta la primera jamba. En la
tabla, `Segmento de referencia` contiene el ID corto `Sx` y, si ya existe, su
correspondencia con `wall_id`. La referencia física debe indicar si se midió el
vano libre terminado entre jambas, el marco, el hueco bruto u otra referencia;
no mezclar referencias. El ancho y el alto deben usar la misma referencia
física. Si solo se pudo observar una referencia distinta, anotarlo y no
convertirlo silenciosamente en vano libre.

| ID | Segmento de referencia | Extremo de referencia | Offset (lectura → m) | Ancho (lectura → m) | Alto (lectura → m) | Referencia física del vano | Estado offset/ancho/alto | Incertidumbre offset/ancho/alto (m) | `source_id` | Apertura/orientación observada | Notas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |

Profundidad, sentido de apertura y orientación pueden quedar desconocidos si no
se observan con confianza. Los campos estructurados correspondientes en v1 son
`wall_id`, `offset`, `width`, `height`, `depth` y
`opening_direction`, cuando proceda.

## H. Ventanas

El offset se mide desde el extremo inicial de `Sx` hasta el primer lateral del
vano. En la tabla, `Segmento` contiene el ID corto `Sx` y, si ya existe, su
correspondencia con `wall_id`. Registrar el antepecho desde el suelo terminado
y distinguir vano libre, marco y retranqueo. El ancho y el alto deben usar la
misma referencia física; si no, dejar la diferencia en Notas.

| ID | Segmento | Extremo de referencia | Offset (lectura → m) | Ancho (lectura → m) | Alto (lectura → m) | Antepecho/elevación (lectura → m) | Profundidad/retranqueo | Estados de las medidas | Incertidumbres (m) | `source_id` | Notas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |

En v1, una ventana requiere `wall_id`, `offset`, `width`, `height` y
`sill_height`. La profundidad o el retranqueo pueden quedar en la hoja y en
notas si no se capturan o no tienen representación suficiente.

## I. Elementos fijos

Registrar también elementos que afecten a la reconstrucción o a la colocación
posterior. Usar la posición sobre pared o punto local sin crear un sistema de
coordenadas secundario.

Un pilar que cambia el contorno del suelo se descompone en segmentos
consecutivos en D y puede repetirse aquí para documentar su colocación. Un
pilar interior que no forma parte del boundary se registra aquí con su anchor
de pared o punto, altura y observaciones. Sus dimensiones completas permanecen
en la hoja si v1 no puede estructurarlas.

| ID | Tipo observado | Pared/segmento asociado | Posición/anchor | Medidas disponibles | Estado | Incertidumbre (m) | `source_id` | Notas y limitaciones v1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |

Schema v1 solo permite los tipos `pillar`, `recess`, `radiator`, `socket`,
`switch` y `fixed`, además de un anchor por pared o punto y una altura. No tiene
campos estructurados completos para ancho, profundidad, forma, orientación ni
`source_id` propio del elemento. Conservar esos detalles en esta hoja y en
`notes` cuando proceda; no añadir propiedades ad hoc al JSON.

## J. Registro fotográfico

Usar identificadores neutros. No escribir rutas personales, nombres de archivo
locales, nombres de personas ni coordenadas privadas en esta hoja.

| `source_id` | Subject | Secuencia | Qué muestra | Escala conocida sí/no | Referencia de escala | Privacidad revisada sí/no | EXIF en original privado | Original fuera del repo sí/no | Candidato futuro a versionado sí/no | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |

> **Ninguna fotografía real se versionará en Git sin autorización explícita posterior.**

Las fotografías son referencia visual y se relacionan con medidas mediante
`source_id`. No sustituyen una medida física salvo que exista una escala
conocida, puntos de control e incertidumbre documentados.

## K. Incertidumbres y datos no medibles

| Elemento/dato | Estado (`estimated`/`derived`/`unknown`) | Valor, si procede | Incertidumbre (m) | Fórmula | `depends_on` | Motivo | `source_id` | Acción pendiente |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |

Reglas para la posterior transcripción:

- `measured`: lectura física observada con método y fuente.
- `estimated`: valor aproximado con incertidumbre y nota obligatorias.
- `derived`: valor calculado con `formula` y `depends_on`.
- `unknown`: sin valor; no sustituir por cero.
- Las coordenadas `point_m`, incluido el origen, no son objetos de medida con
  estado propio en v1; su incertidumbre queda documentada en esta hoja y en la
  revisión de trazabilidad.

## L. Checklist antes de abandonar la habitación

- [ ] Identidad, fecha, método y sesión completos.
- [ ] `room_id` y nombre humano confirmados o marcados como pendientes.
- [ ] Origen, esquina inicial, paredes adyacentes, ejes y winding definidos.
- [ ] Croquis manual completado y legible.
- [ ] Perímetro completo, con segmentos para retranqueos, salientes y cambios.
- [ ] Cierre geométrico comprobado y residual anotado.
- [ ] Diagonales y controles redundantes tomados donde corresponda.
- [ ] Altura principal medida y repetida.
- [ ] Vigas, falsos techos y cambios de cota registrados.
- [ ] Puertas completas: pared, extremo, offset, ancho, alto y referencia física.
- [ ] Ventanas completas: pared, extremo, offset, ancho, alto y antepecho.
- [ ] Retranqueos y profundidades observables registrados o marcados como desconocidos.
- [ ] Pilares y elementos fijos relevantes identificados.
- [ ] Medidas críticas repetidas.
- [ ] Discrepancias conservadas y decisiones anotadas; no se han ajustado valores para cerrar.
- [ ] Incertidumbres y estados registrados.
- [ ] Fotografías autorizadas, si las hay, relacionadas con `source_id`.
- [ ] Privacidad revisada; no se han buscado ni conservado elementos identificativos innecesarios.
- [ ] Campos `unknown` y acciones pendientes identificados.
- [ ] Revisión final visual del croquis y de la hoja completada.

## M. Autorizaciones posteriores

Estas casillas son constancia de decisiones posteriores y no se consideran
autorizadas por completar la hoja de campo.

| Acción | Estado | Quién autoriza | Fecha | Observaciones |
| --- | --- | --- | --- | --- |
| Transcribir a JSON real | PENDIENTE |  |  |  |
| Versionar JSON real | PENDIENTE |  |  |  |
| Versionar fotografías seleccionadas | PENDIENTE |  |  |  |
| Ejecutar validator | PENDIENTE |  |  |  |
| Generar con Blender/MCP | PENDIENTE |  |  |  |

## N. Compatibilidad y límites de schema v1

| Dato de campo | Tratamiento compatible con v1 |
| --- | --- |
| Identidad, unidades, fecha y método | Campos estructurados `room_id`, `name`, `units`, `measured_at` y `measurement_method` |
| Origen, ejes, suelo y winding | `coordinate_system`, con `origin`, ejes, `floor_z_m` y orientación fija |
| Boundary y segmentos | `boundary.segments`, con puntos, longitudes y mediciones de inicio/fin cuando proceda |
| Estados, incertidumbre y trazabilidad | Campos de medición; `formula` y `depends_on` son obligatorios cuando el estado sea `derived` |
| Puertas y ventanas | `openings` con pared, offset y dimensiones requeridas por cada tipo |
| Altura principal | Una única medida estructurada en `height` |
| Elementos fijos básicos | Tipo v1, anchor y altura; detalles adicionales pueden requerir `notes` |
| Croquis, controles, fotos, sesión y evidencias | Datos de campo y notas; v1 no ofrece un registro estructurado completo de evidencias |
| Dimensiones/orientación completas de elementos fijos | No estructuradas completamente en v1; conservar en la hoja y notas |
| Incertidumbre de `origin.point_m` y otros `point_m` | No tiene objeto estructurado propio en v1; conservar en la hoja y trazabilidad |
| Alturas no uniformes y semántica constructiva completa de apertura | Limitaciones conocidas de v1; no añadir campos no definidos |
