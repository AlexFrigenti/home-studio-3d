# Procedimiento de toma de medidas reales para `room-v1`

Estado: propuesta operativa para revisión; no autoriza todavía la captura ni la
incorporación de datos reales al repositorio.

Este procedimiento define cómo levantar una habitación real de forma repetible
y cómo conservar la trazabilidad necesaria para transcribirla posteriormente al
schema `room-v1`. La fuente de verdad futura será el archivo de medidas; Blender
solo será una representación derivada. No se deben corregir lecturas para que
encajen en una geometría, ni usar una fotografía como medida exacta sin escala,
puntos de control e incertidumbre documentados.

## 1. Preparación

### 1.1 Herramientas

Equipo mínimo:

- cinta métrica rígida o flexible, preferiblemente de al menos 5 m;
- lápiz, goma, regla y una hoja cuadriculada o una plantilla de croquis;
- cinta de carrocero o etiquetas removibles para marcar esquinas y elementos;
- teléfono o cámara para referencias visuales, sin activar ni conservar ubicación
  si las imágenes fueran a salir del dispositivo;
- nivel pequeño, plomada o una referencia vertical fiable para alturas y
  antepechos.

Equipo opcional para contraste:

- medidor láser doméstico, comprobado contra la cinta en varias distancias;
- flexómetro corto para huecos y elementos próximos;
- regla o tarjeta de escala visible en fotografías de detalle.

La cinta es el camino canónico mínimo. El láser, un plano existente, LiDAR o
fotogrametría son fuentes de contraste, no sustituyen los anclajes manuales sin
una calibración y una incertidumbre explícitas.

### 1.2 Identificación de la sesión

Antes de medir, registrar en la hoja de campo:

- un `room_id` estable, en minúsculas, sin espacios ni acentos, compatible con
  el patrón del schema, por ejemplo `salon_principal`;
- el nombre humano de la habitación;
- fecha `YYYY-MM-DD` y un `session_id` de captura;
- las personas o instrumentos participantes solo si son necesarios para la
  trazabilidad, sin introducir datos personales en el repositorio;
- el método general, por ejemplo `manual_tape` o
  `manual_tape_with_laser_crosscheck`.

En la hoja de campo escribir la unidad junto a cada lectura. Se puede medir en
centímetros si el instrumento o el hueco lo hacen más cómodo, pero antes de
transcribir hay que convertir cada valor a metros: `250 cm` se registra como
`2.500 m`, nunca como `250` dentro de un campo cuya unidad es `m`. No mezclar
centímetros y metros en una misma suma, croquis o control.

No crear todavía un JSON real ni decidir una ruta de medidas real solo por
haber completado esta preparación. La ubicación y el nombre del primer archivo
real requieren la aprobación específica de la tarea T2.12.

### 1.3 Origen, ejes y sentido de recorrido

El sistema local debe quedar decidido antes de tomar offsets:

1. Preferir una esquina interior permanente del suelo terminado, sin un hueco
   que nazca en la esquina.
2. Si la entrada es inequívoca, recorrer el perímetro desde el umbral hacia el
   interior y elegir la primera esquina del lado derecho.
3. Si no hay entrada inequívoca, elegir el extremo de la pared de referencia
   más larga e ininterrumpida. Resolver empates por el identificador de captura
   menor y anotarlo.
4. Si la elección no es clara, marcar varios candidatos y detener la
   transcripción hasta obtener una decisión humana.

Marcar físicamente la esquina elegida como `corner-01` y registrar las dos
paredes adyacentes. Esa esquina es `(0, 0, 0)` en el suelo terminado:

- `Z` apunta verticalmente hacia arriba;
- `X` sigue desde el origen el primer segmento de referencia;
- `Y` completa un sistema dextrógiro con `Z`;
- el boundary se recorre en sentido antihorario visto desde arriba, dejando el
  interior a la izquierda de cada segmento.

El sentido antihorario no describe una dirección de marcha obligatoria: fija un
winding único para distinguir interior y exterior, hacer comparables las
capturas y permitir que el validador compruebe el cierre y la orientación.

El sentido del recorrido es geométrico, no depende de estar mirando hacia la
puerta. Si se cambia de sentido durante la captura, anotar el cambio y
normalizarlo antes de transcribir.

### 1.4 Etiquetas

Usar identificadores estables desde el primer croquis:

- esquinas: `corner-01`, `corner-02`, ...;
- segmentos del perímetro: `wall-01`, `wall-02`, ...;
- puertas: `door-01`, `door-02`, ...;
- ventanas: `window-01`, `window-02`, ...;
- elementos fijos: `pillar-01`, `radiator-01`, `socket-01`, etc.

Una etiqueta debe seguir describiendo el mismo punto o segmento aunque se repita
la medida. No renumerar al descubrir un retranqueo: insertar el segmento nuevo
en el croquis y conservar los identificadores ya utilizados, salvo que el
registro todavía no se haya compartido.

Desde `corner-01`, seguir el primer segmento hasta la siguiente esquina y
marcarla como `corner-02`; cada cambio posterior recibe el siguiente número en
el orden del recorrido. Así, `wall-01` va de `corner-01` a `corner-02`,
`wall-02` de `corner-02` a `corner-03`, y el último segmento termina de nuevo en
`corner-01`. Los segmentos de `coordinate_system.origin.adjacent_segment_ids`
son el primero y el último del recorrido.

## 2. Perímetro y coordenadas

### 2.1 Orden de captura

Seguir siempre este orden:

1. fotografiar y dibujar la habitación sin obstruir las referencias;
2. marcar origen, sentido antihorario, esquinas y primer segmento;
3. recorrer la frontera interior desde el origen hasta volver al origen;
4. en cada cambio de dirección, saliente, retranqueo o pilar que cambie el
   contorno, cerrar el segmento actual y abrir el siguiente;
5. para cada segmento anotar inicio, final, longitud directa, instrumento,
   incertidumbre y `source_id`;
6. repetir las esquinas críticas y comprobar el cierre antes de desmontar las
   marcas.

El `offset` de un hueco o de un elemento anclado se mide desde `start_m` del
segmento, avanzando en la dirección del segmento, hasta el primer borde del
elemento. No se mide desde una esquina visual distinta ni desde el origen global
si el elemento está en otra pared.

### 2.2 Habitaciones no rectangulares

Una pared recta entre dos cambios de dirección es un segmento. Una habitación
rectangular son cuatro segmentos; una L, un retranqueo o un ángulo no recto
requieren tantos segmentos como cambios de dirección haya. No convertir la
habitación en una caja ni repartir un error de cierre entre las paredes.

- Un retranqueo se registra como la secuencia de segmentos que entra, recorre y
  sale del hueco.
- Un saliente se registra con la secuencia que lo rodea.
- Un pilar que forma parte del contorno se representa con los segmentos del
  contorno, no como una longitud negativa o una corrección del área.
- Un pilar exento o adosado que no cambia el boundary se registra además como
  elemento fijo anclado a pared o a punto, conservando sus dimensiones en la
  hoja de campo aunque v1 no tenga campos para ellas.
- Una pared inclinada o no paralela se conserva con sus puntos locales; no se
  fuerza a 90 grados.

Un retranqueo o pilar que cambie el contorno conserva la misma cadena de
esquinas y segmentos: no se crea un sistema de coordenadas secundario. Para un
elemento exento, medir su posición desde `corner-01` mediante un `point_anchor`
o desde una pared etiquetada mediante `wall_anchor`; las dimensiones físicas se
mantienen en la hoja de campo porque v1 no las estructura.

Si una forma no puede describirse sin ambigüedad con segmentos, detener la
transcripción y conservar un croquis acotado. El schema v1 no contiene ángulos
explícitos: la orientación queda implícita en los puntos `start_m`/`end_m` y en
las medidas de control.

### 2.3 Cierre geométrico y controles redundantes

Antes de abandonar la habitación:

- comprobar que el final de cada segmento coincide con el inicio del siguiente;
- comprobar que el último segmento vuelve a la esquina de origen;
- calcular y anotar el residual de cierre, sin corregirlo distribuyéndolo;
- repetir en sentido inverso las paredes largas, obstruidas o con retranqueos;
- medir al menos dos diagonales o distancias cruzadas en cada zona cuya forma
  no quede determinada de manera inequívoca por los lados;
- contrastar las lecturas críticas de cinta con láser o con una segunda lectura;
- volver a medir los offsets y anchos de huecos desde las referencias de pared;
- comparar, cuando sea posible, sumas de tramos con una medición directa del
  recorrido completo.

Cada diagonal o control cruzado debe anotar sus dos referencias, por ejemplo
`corner-01 -> corner-05`, y su unidad. No usar una distancia entre dos puntos
visualmente aproximados como sustituto de una esquina etiquetada.

La tolerancia matemática de `1e-6 m` sirve para comparar datos ya calculados,
no para declarar exacta una pared real. Como regla operativa inicial, un
residual mayor que la incertidumbre combinada genera `warning`; un residual
mayor que dos veces esa incertidumbre o que `0.010 m` genera `fail` y exige
repetir o revisar la captura. Una decisión distinta debe quedar aprobada y
anotada por habitación.

Si dos lecturas repetidas no coinciden, repetirlas desde las mismas referencias
y comprobar instrumento, tensión, perpendicularidad y unidad. Si la diferencia
queda dentro de la incertidumbre combinada, conservar ambas lecturas en la hoja
de campo, declarar el valor elegido y sus fuentes, y no presentarlo con más
precisión de la justificada. Si persiste una diferencia mayor, no promediar ni
escoger la lectura que cierre el dibujo: dejar el campo pendiente como
`unknown`, o `estimated` solo con `uncertainty` y `note` explícitos si existe
una razón operativa para usar una aproximación. La decisión debe quedar
registrada antes de publicar el JSON.

## 3. Alturas y cambios de cota

Medir la altura desde el suelo terminado hasta el punto más bajo que limite el
espacio útil. Para una habitación aparentemente uniforme, tomar una lectura en
el origen, otra en el lado opuesto y una tercera en el centro o en una zona
representativa.

Si el techo no es uniforme:

- medir una cuadrícula o una serie de puntos en cada zona con cota distinta;
- identificar vigas, dinteles, falsos techos, cajones y cambios de plano;
- registrar para cada punto su ubicación respecto a una esquina o segmento y
  su incertidumbre;
- medir también la altura libre bajo la viga o falso techo, no solo la altura
  máxima.

`height` en v1 es una única medida obligatoria. No colapsar varias cotas en un
único valor sin declarar la regla: altura general, altura mínima libre o una
altura de referencia. Si la no uniformidad importa, conservar todas las
lecturas en la hoja de campo y dejar la representación adicional pendiente de
una decisión de contrato. El suelo terminado sigue siendo `floor_z_m: 0`; las
desviaciones del suelo se registran como observaciones, no se convierten en un
nuevo origen sin aprobación.

## 4. Puertas

Para cada puerta registrar:

- `wall_id` del segmento donde está el hueco;
- offset desde `start_m` hasta la primera jamba, medido en la dirección del
  segmento;
- ancho del hueco y alto desde el suelo terminado hasta el dintel;
- la referencia canónica es el vano libre terminado entre jambas y desde el
  suelo terminado; si solo se puede medir marco visible o hueco constructivo,
  etiquetarlo así en la nota y no mezclarlo silenciosamente con el vano libre;
- profundidad del hueco, marco o jambas si afecta al futuro estudio;
- sentido de apertura observado, usando la enumeración v1 solo cuando su
  interpretación sea inequívoca; en caso contrario, `unknown`;
- `source_id`, instrumento, incertidumbre y una referencia fotográfica de la
  sesión.

Medir el offset y el ancho de modo que `offset + width` quede dentro de la
longitud del segmento. Si una puerta está pegada a una esquina, confirmar qué
pared contiene el hueco y no duplicarlo en los dos segmentos. No inferir la
profundidad ni el sentido de apertura a partir de una foto ambigua.

## 5. Ventanas

Para cada ventana registrar:

- `wall_id` y offset desde `start_m` hasta el primer lateral del hueco;
- ancho y alto del vano libre terminado entre jambas; si solo se puede medir
  `marco_visible` o `hueco_constructivo`, indicar esa referencia en la nota;
- altura de antepecho desde el suelo terminado;
- profundidad del hueco, retranqueo, alféizar o jambas si afecta a la
  colocación posterior;
- obstáculos, radiadores o elementos que invadan el hueco;
- `source_id`, instrumento, incertidumbre y fotografía relacionada.

Comprobar `sill_height + height` frente a la altura de la habitación. La cota
superior puede calcularse como derivada, pero no se debe introducir como una
medida independiente ni redondearla para que encaje.

## 6. Elementos fijos y prioridades

Capturar un elemento si cambia el contorno, reduce el volumen útil, condiciona
la colocación del estudio o sirve como punto de control. Separar lo que se mide
ahora de lo que v1 puede representar:

| Prioridad | Capturar en la visita | Tratamiento en v1 |
| --- | --- | --- |
| Imprescindible para geometría | boundary completo, retranqueos, salientes, pilares que alteran el contorno, puertas, ventanas, altura y cambios de cota relevantes | Segmentos, huecos y `height`; la información sin campo específico queda en notas de campo y como gap explícito |
| Útil para colocación posterior | pilares exentos, radiadores, enchufes, interruptores, cajas, rodapiés, conductos, unidades de climatización y obstáculos permanentes | `fixed_elements` cuando el tipo y anclaje encajen; posición, altura, estado y nota; dimensiones detalladas pueden quedar fuera de v1 |
| Fuera del slice 002 | circuitos y cargas eléctricas, cableado, materiales y colores, mobiliario, decoración, acústica detallada, instalaciones ocultas, planos privados y fotos personales versionadas | No crear campos ni datos reales; conservar solo una nota de alcance si afecta a una decisión futura |

Para cada elemento útil registrar tipo, identificador, pared o punto de anclaje,
offset o coordenadas, altura, ancho/profundidad/volumen en la hoja de campo,
obstrucciones y fotografías. El schema v1 solo permite los tipos `pillar`,
`recess`, `radiator`, `socket`, `switch` y `fixed`, y exige `height`; no tiene
campos de ancho, profundidad, forma, orientación, `source_id` propio ni
geometría detallada para un elemento fijo. No introducir propiedades adicionales
en el JSON. Si un conducto, una unidad de climatización o una caja no encaja,
registrar su información fuera del JSON y dejar el gap documentado, o usar
`fixed` únicamente como clasificación provisional explícita en `note`.

La `height` obligatoria de un elemento fijo debe referirse a un punto de anclaje
vertical definido en la hoja de campo, por ejemplo el centro del enchufe o el
centro del radiador. No existe una semántica universal para todos los tipos en
v1: escribir el punto elegido en `note`, mantener su unidad en metros y no
interpretarlo como altura, ancho o cota superior sin esa aclaración.

## 7. Estados de las medidas

Cada objeto de medida debe tener `status` y `method`. Las reglas son:

| Estado | Usarlo cuando | Obligaciones |
| --- | --- | --- |
| `measured` | lectura directa de cinta, láser u otra fuente primaria validada | `value`, método, incertidumbre si se conoce y `source_id` cuando aporte trazabilidad |
| `estimated` | aproximación necesaria porque no se puede observar o medir directamente | `value`, `uncertainty` y `note` obligatorios; explicar por qué no es lectura directa |
| `derived` | resultado calculado desde otras medidas | `value`, `formula` y `depends_on` obligatorios; no repetirlo como lectura directa |
| `unknown` | dato no capturado, no fiable o todavía no decidido | `method` obligatorio, normalmente `not_captured`; omitir `value`, no usar cero |

La incertidumbre se expresa como semirango positivo en metros. Como referencia
inicial del slice, una cinta puede usar aproximadamente `±0.005 m` en tramos
despejados y `±0.010 m` en tramos largos u obstruidos; un láser doméstico puede
estar alrededor de `±0.002–0.005 m` en buenas condiciones. Son referencias de
método, no valores automáticos: la observación concreta prevalece.

Si dos lecturas independientes discrepan más que la incertidumbre combinada,
conservar ambas observaciones, repetir la captura y no escoger la que haga
cerrar el polígono. La precisión escrita a tres decimales no convierte una
lectura en milimétrica.

## 8. Protocolo fotográfico y referencias

Las fotografías documentan identidad, contexto, obstáculos y estado visual. No
son la autoridad métrica por sí solas.

### 8.1 Secuencia mínima

Tomar, sin incluir personas, documentos ni información privada innecesaria:

1. dos o tres fotos generales desde esquinas opuestas;
2. una foto de cada pared, lo más perpendicular posible;
3. cada esquina y cada cambio de dirección del boundary;
4. cada puerta completa y un detalle de sus jambas, umbral y sentido de
   apertura;
5. cada ventana completa y un detalle de antepecho, jambas y retranqueo;
6. cada pilar, radiador, enchufe, interruptor, caja, rodapié, conducto o
   equipo fijo que afecte al estudio;
7. detalles adicionales de zonas ambiguas, obstruidas o discrepantes.

En detalles métricos puede aparecer una cinta o tarjeta de escala, siempre que
no sustituya la lectura anotada. Anotar desde qué punto y con qué `source_id`
se relaciona la imagen; una imagen puede documentar varias lecturas, pero la
relación debe ser explícita.

### 8.2 Nomenclatura y privacidad

Usar una convención estable, por ejemplo:

`<room_id>_<session_id>_<subject>_<sequence>.<ext>`

Ejemplos abstractos: `salon_principal_s01_wall-03_general_01.jpg` o
`salon_principal_s01_window-02_detail_01.jpg`. El `source_id` puede seguir la
misma base, por ejemplo `capture-s01-wall-03`; no usar rutas personales ni
nombres de personas.

Los originales permanecen fuera del repositorio. Antes de versionar una
referencia seleccionada bajo `assets/references/<room_id>/` se requiere una
decisión explícita, revisión de procedencia, eliminación de EXIF de ubicación,
revisión de rostros/documentos y un identificador de evidencia. Esta tarea no
introduce fotos reales ni define todavía un registro JSON de evidencias; el
schema v1 solo ofrece `source_id` en objetos de medida.

## 9. Control de calidad in situ

No abandonar la habitación hasta marcar cada punto:

- [ ] `room_id`, fecha, método y sesión están anotados.
- [ ] Origen, esquina, paredes adyacentes, ejes y sentido antihorario están
      marcados y fotografiados.
- [ ] El perímetro está completo, con un segmento por cambio de dirección.
- [ ] Retranqueos, salientes, pilares y cambios de cota tienen identificador.
- [ ] Cada segmento tiene longitud, método, incertidumbre y fuente.
- [ ] El último segmento vuelve al origen; el residual de cierre está anotado.
- [ ] Se han repetido paredes largas, obstruidas y medidas críticas.
- [ ] Existen diagonales o controles redundantes para las zonas ambiguas.
- [ ] La altura general está medida en varios puntos.
- [ ] Vigas, falsos techos, desniveles y alturas libres están registrados.
- [ ] Cada puerta tiene pared, offset, ancho y alto; profundidad y apertura
      están capturadas o marcadas como desconocidas.
- [ ] Cada ventana tiene pared, offset, ancho, alto y antepecho; profundidad
      está capturada o marcada como desconocida.
- [ ] Cada elemento fijo relevante tiene tipo, ubicación, altura y notas; las
      dimensiones no representables en v1 están en la hoja de campo.
- [ ] No quedan huecos o elementos sin referencia inequívoca.
- [ ] Las fotos generales, de paredes, esquinas, huecos y ambigüedades están
      numeradas y relacionadas con `source_id`.
- [ ] No hay rostros, documentos, ubicación GPS u otros datos personales que
      deban entrar en el repositorio.
- [ ] Las discrepancias están repetidas o conservadas como discrepancias; no
      se han ajustado números para cerrar el dibujo.

## 10. Transcripción posterior a JSON v1

La transcripción se hará en una sesión separada, conservando primero la hoja de
campo original y una copia de trabajo. No se sobrescribe la evidencia primaria
para hacer pasar el validador.

### 10.1 Orden recomendado

1. Definir `schema_version`, `room_id`, `name`, `units`, `measured_at` y
   `measurement_method`.
2. Registrar `coordinate_system`, origen, segmentos adyacentes, ejes,
   `boundary_orientation` y `floor_z_m: 0`.
3. Convertir el croquis en `boundary.segments` ordenados, con puntos locales,
   longitudes, estados, métodos, incertidumbres y `source_id`.
4. Añadir `height` y, solo si procede, `floor_area` como `derived` con fórmula
   y dependencias.
5. Añadir puertas y ventanas con `wall_id`, offset y dimensiones en metros.
6. Añadir solo los elementos fijos que encajen en el contrato y completar
   `notes` con limitaciones y decisiones pendientes.
7. Mantener `openings.doors`, `openings.windows`, `fixed_elements` y `notes`
   aunque las listas estén vacías.

Los valores son números en metros; no escribir unidades dentro de las cadenas.
Las coordenadas se expresan en el sistema local. Las superficies derivadas se
documentan como tales y no sustituyen al boundary.

Los campos `origin.point_m`, `start_m`, `end_m` y `point_anchor.point_m` son
coordenadas, no objetos de medida con `status`. Se calculan en el sistema local
a partir del origen, la cadena de segmentos y los controles cruzados; la hoja de
campo debe conservar las referencias y su incertidumbre. Si la posición no puede
determinarse con confianza, no inventar coordenadas para satisfacer el schema:
dejar la medida que la sustenta como `unknown` o detener la transcripción hasta
resolverla.

### 10.2 Valores que pueden quedar desconocidos

Siempre que el schema lo permita, usar un objeto con `status: "unknown"`, un
`method` explícito como `not_captured` y sin `value`. Esto aplica, por ejemplo,
a profundidad de puerta/ventana, espesor de pared no medido, apertura de una
puerta o altura de un elemento fijo no observado. `floor_area` es opcional y
puede omitirse hasta disponer de una frontera fiable.

No inferir silenciosamente longitudes, ángulos, espesores, alturas, offsets,
dimensiones de elementos fijos, apertura de puertas, cotas de techo no
uniformes o datos métricos a partir de una fotografía sin escala. No rellenar
con cero, no añadir propiedades no definidas y no convertir un valor estimado
en medido.

### 10.3 Validación previa a cualquier generación

Antes de autorizar una generación posterior, revisar en este orden:

1. parseo JSON y validación contra `measurements/schema/room-v1.schema.json`;
2. IDs únicos, unidades, estados, incertidumbres, `derived` y `unknown`;
3. conexión, cierre, orientación y auto-intersecciones del boundary;
4. límites de offsets y huecos frente a sus segmentos y altura;
5. revisión de trazabilidad de `source_id`, notas y fotografías externas;
6. revisión humana de privacidad y de cualquier dato no representable en v1;
7. solo después, validación del generador y comparación datos ↔ Blender.

La ejecución de validadores, generator, Blender o MCP requiere una autorización
separada y no forma parte de este procedimiento documental.

## 11. Límites conocidos del schema v1

El procedimiento captura más información de la que v1 puede representar para
evitar perder observaciones en la visita. En particular:

- `fixed_elements` no tiene campos de ancho, profundidad, forma, orientación ni
  `source_id` propio;
- solo existen categorías cerradas para algunos elementos fijos;
- no existe un objeto canónico de evidencias o fotografías;
- `height` representa una única medida obligatoria, no una malla de techo;
- `point_m` y el origen no llevan un objeto de incertidumbre propio;
- los huecos tienen offsets y dimensiones, pero el significado geométrico de
  `opening_direction` todavía no dirige la generación constructiva.

Estos límites no se resuelven añadiendo campos ad hoc al JSON real. Se
registran en la hoja de campo, `notes` y la revisión del contrato que proceda.
