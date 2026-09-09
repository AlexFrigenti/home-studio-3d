# Especificación: Furniture Placement v1

> Clasificación: T2 — nuevo dominio de datos, plan determinista, validación espacial y overlay Blender derivado.
> Rama: `spec/004-furniture-placement-v1`
> Estado: T4.01–T4.06 — contrato, schema, validators, fixture sintético,
> furniture plan puro, validación espacial, overlay Blender reversible,
> normalizer/comparator furniture, acceptance canónica, artefacto derivado,
> preview técnico y documentación implementados y validados.

## Objetivo

Añadir una capa independiente de colocación de mobiliario proxy para una
habitación arquitectónica ya validada. El sistema debe permitir declarar uno
o varios layouts para `living-room-main`, construir un furniture plan puro y
determinista, validar sus límites espaciales, generar un overlay Blender
reversible y comparar el overlay normalizado con el plan sin modificar la
arquitectura ni convertir el mobiliario en medición arquitectónica.

El resultado de v1 es una base reproducible para experimentar con
distribuciones sintéticas. No es todavía un catálogo, un sistema de assets,
una interfaz de usuario ni un sistema de optimización de layouts.

## Problema

Los Slices 001–003 proporcionan una habitación real validada, un generation
plan determinista, una escena arquitectónica Blender y comparaciones
room→plan y plan→scene. Todavía no existe una fuente de verdad separada para
probar distribuciones de muebles. Añadir muebles a `measurements/` contaminaría
la autoridad arquitectónica; añadirlos al generator o al normalizer de room
mezclaría dos dominios con ownership y ciclos de vida distintos.

Furniture Placement v1 debe introducir ese dominio sin romper los contratos
existentes, sin sobrescribir el `.blend` arquitectónico y sin presentar
dimensiones sintéticas como observaciones reales.

## Alcance

### Incluye

- Contrato conceptual versionado `furniture-layout-1` para layouts externos a
  `measurements/`.
- Múltiples layouts independientes para un mismo `room_id`, sin alias mutable
  `current`.
- Validación pura del layout y construcción de un
  `furniture-placement-generator-1` determinista.
- Coordenadas `canonical_room` en metros, anchor `bottom_center` y yaw
  horizontal finito; el furniture plan normaliza el yaw.
- Validación espacial contractual contra el floor polygon, wall proxies,
  opening proxies y otros furniture proxies cuando la geometría efectiva del
  room plan permite demostrar el resultado.
- Warnings separados para reglas de diseño que no pueden probarse como
  colisión física con los datos actuales.
- Overlay Blender separado, reversible y generado sobre una copia derivada de
  la escena arquitectónica.
- Namespace y ownership furniture independientes del dominio
  `HS3D_ROOM_<room_id>`.
- Normalized furniture scene independiente con versión
  `furniture-scene-adapter-1`.
- Comparación pura furniture plan→scene con versión
  `furniture-scene-comparison-1`.
- Anti-cascade, anti-false-pass, determinismo, no mutación y protección
  contractual de la arquitectura.
- Una acceptance real pequeña sobre `living-room-main` con dos o tres proxies
  de dimensiones sintéticas explícitamente marcadas.
- Evidencia de un `.blend` derivado y un preview técnico sin sobrescribir la
  escena fuente.

### Fuera de alcance

- Modificar `measurements/rooms/living-room-main.json`, los schemas room o el
  generation plan actual.
- Modificar `generate_room.py`, `normalize_room_scene.py`,
  `compare_room_scene.py` o `validate_generated_room.py` para que gestionen
  furniture.
- Modelos 3D reales, catálogo, `model_ref`, asset manager, descargas externas,
  licencias de assets o texturas.
- Materiales realistas, decoración, iluminación artística, render final o UI.
- Booleanos, openings constructivos, física o simulación.
- Optimización automática, IA de layouts, reglas ergonómicas automáticas o
  clearance humano presentado como colisión.
- Multi-room como producto; el contrato conserva `room_id`, pero la primera
  acceptance solo cubre `living-room-main`.
- Nuevas mediciones físicas obligatorias; las dimensiones de acceptance son
  sintéticas y no representan muebles reales del usuario.

## Modelo de autoridad

La autoridad queda separada por dominio:

1. `measurements/` conserva las observaciones arquitectónicas y la provenance
   del room.
2. El generation plan room interpreta un room validado y define la geometría
   arquitectónica efectiva.
3. `layouts/<room_id>/<layout_id>.json` es la autoridad de una propuesta de
   colocación, sus dimensiones de furniture y sus transformaciones manuales.
4. El furniture plan interpreta el layout contra un room generation plan; no
   modifica ninguno de los dos inputs.
5. El overlay Blender es un artefacto derivado del furniture plan y no puede
   corregir ni redefinir la arquitectura.

Un mueble situado dentro de una habitación no se convierte por ello en una
medición del room. `source_id` y `dimensions_status` deben conservar el origen
de sus dimensiones. El generator de furniture nunca puede promocionar
`unknown` a `measured` ni rellenar datos arquitectónicos desde Blender.

## Autoridad y ubicación de layouts

La forma canónica prevista es:

```text
layouts/<room_id>/<layout_id>.json
```

Ejemplo conceptual, no creado en este checkpoint:

```text
layouts/living-room-main/experiment-01.json
```

El layout es un documento independiente del room. Un room puede tener varios
layouts que se validan y generan por separado. No existe un alias mutable
`current`; seleccionar un layout requiere proporcionar su `layout_id` y su
archivo explícito. Esta elección permite comparar variantes, conservar
rollback por archivo y evitar que un experimento cambie otro.

## Contrato `furniture-layout-1`

El contrato inicial es deliberadamente pequeño y cerrado. La forma conceptual
de un documento válido es:

```json
{
  "layout_schema_version": "furniture-layout-1",
  "layout_id": "experiment-01",
  "room_id": "living-room-main",
  "units": "m",
  "coordinate_system": "canonical_room",
  "placement_method": "manual",
  "items": [
    {
      "id": "sofa-01",
      "type": "sofa",
      "dimensions_m": [2.20, 0.95, 0.85],
      "dimensions_status": "synthetic",
      "source_id": "slice-004-acceptance-sofa-01",
      "position_xy_m": [-3.10, 1.20],
      "anchor": "bottom_center",
      "yaw_deg": 0.0
    }
  ]
}
```

### Reglas de entrada

- `layout_schema_version` es obligatorio y debe ser exactamente
  `furniture-layout-1`.
- `layout_id` y cada `items[].id` son identificadores estables, no vacíos, con
  sintaxis slug `^[a-z][a-z0-9_-]*$`. Los IDs son únicos dentro del layout.
- `source_id` es obligatorio y sigue el token ASCII
  `^[a-z0-9][a-z0-9._-]*$`; no es una ruta personal ni se infiere desde una
  ruta.
- `room_id` es obligatorio y debe identificar el room que se proporciona al
  pipeline; no se acepta inferirlo desde una ruta.
- `units` es obligatorio y debe ser `m`.
- `coordinate_system` es obligatorio y debe ser `canonical_room`.
- `placement_method` es obligatorio y en v1 solo admite `manual`.
- `items` es obligatorio; cada item debe tener los campos definidos abajo.
- Se rechazan campos desconocidos (`additionalProperties=false`). La política
  evita que datos futuros parezcan soportados silenciosamente.
- Números de dimensiones, posición y yaw deben ser finitos; no se admiten
  `NaN`, infinito, strings numéricas ni `-0.0` en la serialización canónica.

### Campos de item

| Campo | Estado | Autoridad y propósito | Firma |
| --- | --- | --- | --- |
| `id` | obligatorio | identidad estable del item dentro del layout | sí |
| `type` | obligatorio | categoría proxy cerrada y estable; v1 acepta `sofa`, `coffee_table`, `armchair`, `shelf`, `tv_unit` | sí |
| `dimensions_m` | obligatorio | `[width, depth, height]` del proxy en metros | sí |
| `dimensions_status` | obligatorio | origen explícito de las dimensiones | sí |
| `source_id` | obligatorio | referencia estable de origen, sin ruta personal | sí |
| `position_xy_m` | obligatorio | centro de la base en `canonical_room` | sí |
| `anchor` | obligatorio | en v1 debe ser `bottom_center` | sí |
| `yaw_deg` | obligatorio | giro horizontal finito en grados; T4.02 lo normaliza a `[0, 360)` | sí |

En v1 no se añaden `label`, `notes`, `floor_contact`, `model_ref`,
`asset_ref`, pitch, roll, escalado libre ni campos de catálogo. Un futuro
contrato puede añadirlos con un bump explícito; no se reservan como datos
silenciosamente aceptados.

### Dimensiones y provenance

`dimensions_m` siempre está ordenado como `[width, depth, height]`, debe tener
tres valores estrictamente positivos y define la geometría del proxy. Los
valores permitidos de `dimensions_status` son:

- `measured`: dimensiones tomadas físicamente del mueble; no significa que
  procedan del room.
- `estimated`: dimensiones aproximadas y explícitamente no medidas.
- `manufacturer`: dimensiones declaradas por fabricante; la futura evidencia
  de fabricante no forma parte de v1.
- `synthetic`: dimensiones de prueba o diseño, como las de la acceptance; no
  son datos reales del usuario.

`unknown` se rechaza en v1 porque un proxy no puede generarse de forma
determinista sin dimensiones. Rechazarlo no promociona ningún dato: obliga a
la persona autora del layout a elegir un estado explícito y una dimensión
usable. `source_id` sigue la sintaxis de token indicada, no puede ser una ruta
absoluta ni contener credenciales; la provenance rica de measurements no se
copia si no aporta significado al mueble.

## Sistema de coordenadas, anchor y rotación

Furniture reutiliza el sistema arquitectónico `canonical_room` del room plan:

- origen: el origen `corner-00` del room;
- ejes: `x` y `y` en el plano de planta del room, `z` vertical;
- unidades: metros;
- mano y semántica: las del room plan validado;
- posición de entrada: `position_xy_m` en el plano horizontal;
- anchor: `bottom_center`;
- pivot local: centro de la base del proxy;
- límites locales del proxy: `x=[-width/2,+width/2]`,
  `y=[-depth/2,+depth/2]`, `z=[0,height]`;
- rotación: `yaw_deg` alrededor de Z; pitch y roll no existen en v1;
- ángulos: grados finitos en JSON; T4.02 los normaliza determinísticamente
  mediante módulo 360 a `[0,360)` sin mutar el layout de entrada.

Así, para un sofá de `2.20 × 0.95 × 0.85 m`, `position_xy_m` representa el
centro de su base, no una esquina ni el centro geométrico de altura. La misma
semántica se conserva al cambiar el yaw y al sustituir el proxy por un modelo
real futuro que respete el mismo anchor.

## Relación layout ↔ room plan

El layout lleva solo la identidad y el sistema de coordenadas necesarios para
validar que pertenece al room. El pipeline recibe el room plan por separado y
comprueba:

- `layout.room_id == room_plan.room_id`;
- `layout.units == room_plan.units == "m"`;
- `layout.coordinate_system == room_plan.coordinate_system` en su proyección
  canónica;
- el room plan está en la versión esperada y tiene la firma lógica esperada.

El layout de entrada no duplica walls, openings, alturas, espesores ni
provenance arquitectónica. El furniture plan derivado sí incorpora de forma
explícita `room_plan_version` y `room_logical_signature` para que una misma
colocación no pueda confundirse con otra geometría arquitectónica.

## Furniture plan

El plan es una estructura JSON-serializable y Blender-independent con, como
mínimo:

```text
furniture_plan_version = furniture-placement-generator-1
layout_schema_version
layout_id
room_id
room_plan_version
room_logical_signature
units = m
coordinate_system = canonical_room
items ordenados por id
effective_geometry por item
provenance
logical_signature
```

Cada `effective_geometry` materializa dimensions `[width, depth, height]`,
anchor, posición, yaw normalizado, footprint/OBB y los vértices locales
derivados del proxy. La provenance conserva al menos `source_id`,
`dimensions_status` y `placement_method=manual`; no inventa provenance de
Blender ni del room. T4.02 no emite `spatial_validation`: esa validación
contractual comienza en T4.03 sobre el plan ya construido.

La función conceptual es:

```text
build_furniture_plan(layout, room_plan) -> furniture_plan
```

Debe ser pura: no lee archivos, no importa `bpy`, no muta `layout` ni
`room_plan`, y para el mismo room plan y la misma serialización canónica del
layout produce el mismo plan y `logical_signature`.

## Serialización, ordering y firmas

La entrada se canoniza con claves ordenadas, UTF-8, separadores compactos,
números finitos, `-0.0` normalizado a `0.0` y arrays sin reordenar salvo
`items`, que se ordena por `id` para el plan. La serialización canónica de la
firma incluye identidad, tipo, dimensiones, estado, source ID, posición,
anchor, yaw, identidad/versiones del room plan y geometría efectiva. No
incluye timestamps, rutas personales, orden incidental de objetos Blender ni
warnings variables.

T4.02 soporta explícitamente el room plan actual
`room-v1.1-generator-2`. Los planes `room-v1-generator-1` y
`room-v1.1-generator-1` no se promocionan silenciosamente y se rechazan hasta
que exista una decisión de compatibilidad específica.

La tolerancia computacional reutiliza el principio de `1e-6 m` para comparar
valores lineales; no se interpreta como incertidumbre física ni relaja los
estados de provenance. Las firmas se calculan sobre representación
normalizada, no sobre el texto arbitrario del archivo de entrada.

## Validación espacial

### Errores contractuales demostrables

La validación pura debe producir `valid=false` ante:

- dimensiones no positivas, no finitas o mal ordenadas;
- IDs duplicados o entidad malformada;
- room, unidades o sistema de coordenadas incompatibles;
- footprint/OBB del proxy fuera del floor polygon efectivo;
- intersección del proxy con la geometría efectiva de un wall proxy;
- overlap entre furniture proxies de suelo cuando v1 no admite stacking;
- intersección con un opening proxy según la geometría efectiva representada.

Estos resultados significan una intersección en la representación geométrica
disponible, no una afirmación de construcción física exacta.

Si el room plan aporta un `fixed_element` con geometría efectiva soportada,
su footprint se trata como otro obstáculo geométrico del plan. Si no aporta
esa geometría, el validador no la inventa y registra la condición como no
verificable. `living-room-main` tiene cero fixed elements, por lo que la
acceptance inicial no introduce ni mide ninguno.

### Warnings y heurísticas

En v1 son warnings o capacidades futuras, nunca errores físicos automáticos:

- clearance humano o ancho de paso;
- giro de hoja de puerta, porque `opening_direction` es `unknown`;
- espacio de uso frente a sofá, mesa o mueble;
- reglas de diseño frente a ventanas;
- tolerancias ergonómicas o accesibilidad;
- intención de “bloqueo” funcional de una apertura sin una geometría
  constructiva disponible.

Openings continúan siendo `proxy_only=true` y
`constructive_geometry=false`. El sistema puede comparar su proyección lógica
y sus proxies, pero no afirmar booleanos, espesor constructivo real ni
clearance de hoja.

## Namespace y ownership Blender

Se compararon tres alternativas:

- `HS3D_LAYOUT_*`: coherente visualmente con la marca, pero el adapter actual
  trata cualquier entidad `HS3D_*` fuera de `HS3D_ROOM_*` como ownership
  gestionado inválido. Adoptarlo exigiría cambiar el contrato cerrado del
  adapter room.
- `HSLAYOUT_*`: mantiene la separación semántica, no colisiona con el dominio
  `HS3D_ROOM_*` y permite que el adapter room clasifique el overlay como
  auxiliar no gestionado.
- `FURNITURE_*`: evita el prefijo room, pero pierde la identidad de layout y
  deja un namespace más genérico y susceptible de colisiones futuras.

La elección v1 es `HSLAYOUT_*`:

- root: `HSLAYOUT_<room_id>_<layout_id>`;
- collection hija gestionada lógicamente: `Furniture`; como los nombres de
  datablock de Collection son globales en Blender, el datablock físico usa el
  nombre determinista `HSLAYOUT_<room_id>_<layout_id>_Furniture` y conserva
  `hs3d_layout_collection_role=Furniture`;
- objeto proxy físico: `HSLAYOUT_FURNITURE_<room_id>_<layout_id>_<item_id>`;
  `item_id` continúa siendo la identidad semántica independiente almacenada
  en metadata; la cualificación evita colisiones globales de nombres Blender
  entre layouts que contienen el mismo item.
- metadata propia: claves `hs3d_layout_*`, sin reutilizar `hs3d_role` del
  dominio room.

El `furniture-scene-adapter-1` buscará exactamente su root y collection. El
`room-scene-adapter-1` no se amplía y no interpreta los objetos HSLAYOUT como
entidades arquitectónicas. Un namespace futuro no puede sustituir esta
decisión sin un cambio de versión explícito.

## Escena derivada y regeneración

El flujo seguro es:

```text
room-v1.1-generator-2 .blend versionado
  → abrir/validar como fuente read-only
  → añadir únicamente root HSLAYOUT y Furniture
  → guardar un .blend derivado nuevo
```

El nombre previsto es
`<room-artifact-stem>-layout-<layout_id>.blend`, con un preview paralelo
`renders/previews/<room-artifact-stem>-layout-<layout_id>/qa-top-orthographic.png`.
La fuente arquitectónica nunca se sobrescribe. La generación debe rechazar un
output o preview existente salvo una operación explícita y segura sobre el
mismo layout; en v1 la política preferida es fail-if-exists para evitar
reemplazos silenciosos.

Regenerar el mismo layout desde la misma fuente y plan debe borrar/recrear
solo el root HSLAYOUT de ese `layout_id` en la copia de trabajo y producir el
mismo estado lógico. No se elimina otro layout, no se eliminan objetos
externos/manuales y no se llama `read_factory_settings`. El rollback consiste
en descartar el `.blend` derivado y conservar intacta la fuente.

## Normalized furniture scene

El adapter independiente implementado es
`normalize_furniture_scene(scene, room_id, layout_id)`. Su core puro
`normalize_scene(scene_data, room_id, layout_id)` consume una extracción
estructural sin Blender; el adapter Blender es read-only. Su salida versionada
`furniture-scene-adapter-1` contiene únicamente el dominio del layout:

```text
furniture_scene_adapter_version
room_id
layout_id
units
root { name, role=managed_layout_root, metadata }
collections [{ name=Furniture, role, metadata }]
entities [{ entity_type=furniture_proxy, entity_id, name, object_type,
             transform, geometry, metadata }]
ownership { managed_root, unmanaged_auxiliary }
```

Las entidades se ordenan por `(entity_type, entity_id)`, usan metros y
transformaciones finitas, y exponen vértices/footprints suficientes para
comparar dimensiones, posición y yaw. El adapter rechaza root ausente o
duplicado, collection inesperada, ID duplicado, entidad malformada, unidades
incorrectas, roles desconocidos, parent transforms y geometría no finita. No
reconstruye provenance ausente en Blender y excluye claves de ruta de la
serialización normalizada.

Las entidades arquitectónicas no aparecen en este NormalizedScene. La
protección de arquitectura se ejecuta como una comprobación paralela sobre la
proyección arquitectónica antes y después.

El ownership es estricto: un objeto o collection con metadata furniture del
mismo `room_id` y `layout_id` solicitado que este fuera de ese root exacto se
rechaza con `furniture_ownership_outside_root`. Los objetos ordinarios sin
metadata furniture relevante y los dominios de otros layouts se ignoran.

## Furniture ComparisonReport

El comparador conceptual es:

```text
compare_furniture_plan_to_scene(furniture_plan, normalized_furniture_scene)
  -> FurnitureComparisonReport
```

No recibe el room como tercer input ni regenera el plan. El report
`furniture-scene-comparison-1` comprueba versiones, `room_id`, `layout_id`,
`room_plan_version`, `room_logical_signature`, unidades, ownership, IDs,
tipos, dimensions, geometría efectiva, posición, yaw, anchor, metadata
materializada, provenance materializada y firma lógica.

La protección de arquitectura queda fuera de la identidad del furniture
report, pero forma parte de la acceptance del pipeline derivado: una
acceptance no es válida si el furniture overlay pasa y la proyección
arquitectónica cambia.

## Evidencia de T4.05

T4.05 queda implementada sin extender el dominio room:

- normalizer: `blender/scripts/furniture/normalize_furniture_scene.py`;
- comparator: `blender/scripts/furniture/compare_furniture_scene.py`;
- tests puros: `tests/furniture/test_normalize_furniture_scene.py` y
  `tests/furniture/test_furniture_scene_comparison.py`;
- integración Blender read-only: `tests/furniture/blender_test_furniture_scene_normalization.py`;
- acceptance temporal: `tests/furniture/blender_test_furniture_scene_real_acceptance.py`;
- resultado: 26/26 tests puros y 6/6 tests Blender sintéticos;
- acceptance temporal sobre generator-2: report válido, tres entidades,
  mutación de geometría rechazada, arquitectura antes/después equivalente,
  `room plan→scene` válido y fuente intacta;
- entidades ordenadas por `(entity_type, entity_id)`, `item_id` semántico
  separado del nombre físico, metadata y geometría comprobadas
  independientemente, sin consulta al layout original ni a spatial validation;
- no se crea artefacto canónico, preview final ni se inicia T4.06.

## Findings y estrategia anti-cascada

Los códigos iniciales propuestos son:

```text
layout_schema_version_mismatch
furniture_plan_version_mismatch
furniture_scene_adapter_version_mismatch
room_id_mismatch
layout_id_mismatch
room_plan_signature_mismatch
units_mismatch
missing_furniture
unexpected_furniture
duplicate_furniture_id
malformed_furniture_entity
furniture_type_mismatch
furniture_dimensions_mismatch
furniture_position_mismatch
furniture_yaw_mismatch
furniture_anchor_mismatch
furniture_geometry_mismatch
furniture_metadata_mismatch
furniture_provenance_mismatch
furniture_ownership_mismatch
furniture_ownership_outside_root
furniture_logical_signature_mismatch
furniture_out_of_floor
furniture_wall_intersection
furniture_overlap
furniture_opening_intersection
```

`furniture-scene-comparison-1` es metadata del report generado. La
compatibilidad futura de reports deserializados no se finge como una mutación
de input del comparador.

La estrategia anti-cascada valida primero identidad, versiones, unidades,
root y ownership. Si el contexto es incompatible, no inventa findings de
geometría dependientes. Un item ausente produce un finding estable sin
veintenas de errores de campos; uno inesperado produce un finding estable; los
findings restantes se ordenan por stage, entidad, campo y código.

La cobertura anti-false-pass debe demostrar por separado:

- metadata correcta + geometría corrupta → `valid=false` y
  `furniture_geometry_mismatch`;
- geometría correcta + metadata corrupta → `valid=false` y finding de metadata,
  provenance u ownership correspondiente.

## Protección contractual de arquitectura

Antes de generar el overlay se normaliza o proyecta el dominio arquitectónico
de la fuente. Después se repite la operación sobre la escena derivada y se
compara la serialización/proyección estable, incluyendo floor, walls,
openings, fixed elements, collections, ownership y metadata arquitectónica.

La acceptance debe demostrar:

- mismo conjunto de entidades arquitectónicas;
- mismas geometrías world-space dentro de la tolerancia del room pipeline;
- mismas unidades, versiones y firmas arquitectónicas;
- ningún objeto `HS3D_ROOM_*` movido, eliminado o alterado;
- fuente `.blend` sin cambios de SHA-256.

El generator furniture solo puede crear/reemplazar su root HSLAYOUT propio.
No puede llamar `read_factory_settings`, eliminar `HS3D_ROOM_*`, modificar
collections de arquitectura ni guardar sobre la ruta fuente. Esta protección
es una condición verificable del report de acceptance y no una confianza en el
código.

## Acceptance real inicial

La primera acceptance usará exclusivamente:

- room: `living-room-main`;
- fuente arquitectónica:
  `blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend`;
- SHA-256 esperado de la fuente:
  `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`;
- room plan: `room-v1.1-generator-2`;
- firma lógica room:
  `182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a`;
- layout sintético pequeño de dos o tres proxies: `sofa`, `coffee_table` y
  `armchair` si sus footprints permiten una colocación inequívoca;
- todos los items con `dimensions_status=synthetic` y `source_id` con prefijo
  `slice-004-acceptance-`.

La evidencia futura debe demostrar layout válido, furniture plan válido,
spatial validation válida, proxies y transforms correctos, arquitectura
intacta, dos generaciones lógicamente idénticas, normalized furniture scene
válida, furniture plan→scene válido, mutaciones anti-false-pass, preview
técnico, `.blend` derivado y fuente arquitectónica no sobrescrita. Las
dimensiones no se presentarán como medidas reales.

## Evidencia de T4.02

T4.02 queda implementada sin Blender ni cambios al room pipeline:

- plan puro: `blender/scripts/furniture/build_furniture_plan.py`;
- tests: `tests/furniture/test_furniture_plan.py`;
- resultado: `30/30 PASS`;
- soporte de room plan: `room-v1.1-generator-2`;
- yaw normalizado a `[0,360)` y items ordenados por ID;
- footprint local/world, OBB 2D, z mínimo/máximo y provenance del layout;
- firma SHA-256 determinista y no mutación de inputs;
- no se ejecuta spatial validation, no se usa Blender y no se crea furniture
  overlay.

## Evidencia de T4.03

T4.03 queda implementada como una capa pura y Blender-independent:

- validador: `blender/scripts/furniture/validate_furniture_spatial.py`;
- tests: `tests/furniture/test_furniture_spatial.py`;
- resultado: `54/54 PASS`;
- report serializable `furniture-spatial-validation-1` con binding bloqueante,
  findings estables, summary, entidades comprobadas y limitations agregadas;
- containment sobre el floor polygon efectivo, intersecciones SAT/OBB 2D y
  solape Z cuando la geometría efectiva lo permite;
- `world_footprint_m` es la autoridad geométrica furniture; `obb_2d` se valida
  como representación derivada consistente en center, axes, half-extents y
  corners;
- footprints/OBBs degenerados y room geometry necesaria malformada producen
  findings estructurados sin crashes ni checks derivados;
- la tolerancia lineal `1e-6 m` se convierte en tolerancia de orientación
  `m²` mediante `tolerance_m * max(vector_lengths, tolerance_m)`;
- touching dentro de `MATH_TOLERANCE_M=1e-6` no produce error y los inputs no
  se mutan;
- wall thickness fallback, opening proxy/direction unknown y fixed elements
  sin geometría efectiva se registran como limitations, nunca como claims
  físicos adicionales; `fixed_elements=[]` no infiere obstáculos;
- fuera de alcance: clearance humano, door swing, ergonomía, constructive
  openings, Blender overlay, normalizer y comparator.

## Evidencia de T4.04

T4.04 queda implementada como un overlay Blender derivado y ownership-safe:

- generator: `blender/scripts/furniture/generate_furniture.py`;
- core puro y contrato: `tests/furniture/test_furniture_generation_contract.py`;
- integración sintética Blender: `tests/furniture/blender_test_furniture_generation.py`;
- acceptance CLI real temporal: `tests/furniture/blender_test_furniture_real_acceptance.py`;
- resultado puro: `9/9 PASS`;
- resultado Blender sintético: `4/4 PASS` en Blender `5.2.1 LTS`;
- fuente generator-2 abierta como read-only y salida derivada temporal creada
  sin sobrescribirla;
- fuente SHA antes/después:
  `352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280`;
- root gestionado `HSLAYOUT_<room_id>_<layout_id>`, role lógico `Furniture` y
  proxies físicos `HSLAYOUT_FURNITURE_<room_id>_<layout_id>_<item_id>` con
  metadata `hs3d_layout_*`;
- `item_id` semántico se conserva sin derivarlo del nombre físico; dos layouts
  pueden contener el mismo `item_id` con objetos Blender globalmente distintos;
- regeneración limitada al root del mismo layout; otros layouts y objetos
  externos se conservan; colisiones de ownership fallan de forma segura;
- proxies cúbicos respetan dimensiones, `bottom_center`, posición, yaw
  canónico, `z_min=0` y `z_max=height`;
- `normalize_blender_scene` sigue clasificando HSLAYOUT como auxiliar externo;
  la proyección arquitectónica antes/después es idéntica y
  `compare_plan_to_scene` permanece válido antes y después;
- no se implementan `normalize_furniture_scene`, comparator, ComparisonReport,
  assets, preview ni artefacto canónico de T4.06.

## Versiones

| Contrato | Versión inicial |
| --- | --- |
| Layout | `furniture-layout-1` |
| Furniture plan | `furniture-placement-generator-1` |
| Furniture scene adapter | `furniture-scene-adapter-1` |
| Furniture comparison report | `furniture-scene-comparison-1` |
| Room schema/generator actual | `room-v1.1-generator-2` |
| Room scene adapter existente | `room-scene-adapter-1` |

No se modifican `room-v1-generator-1`, su golden histórica, `room-v1.1` ni
los contratos `room-scene-*` del Slice 003.

## Compatibilidad, privacidad y provenance

- `measurements/` continúa siendo la autoridad arquitectónica.
- La presencia de furniture no cambia el schema room ni la firma del room
  plan.
- `room-scene-adapter-1` permanece cerrado al dominio room; HSLAYOUT se
  normaliza aparte.
- No se versionan fotos, EXIF, LiDAR, fotogrametría, tokens, credenciales ni
  rutas personales.
- `source_id` de furniture es una referencia estable y no una ruta privada.
- `hs3d_input_path` y cualquier ruta runtime no se incorporan a la salida
  normalizada.
- `measured`, `estimated`, `manufacturer` y `synthetic` no son intercambiables.
- provenance no materializada por Blender no se reconstruye desde el room ni
  se exige como si existiera.

### Assets

El repositorio solo contiene directorios `assets/` vacíos con `.gitkeep`; v1
no añade modelos, texturas, licencias ni referencias externas. Los proxies se
generan desde dimensiones del layout. La sustitución futura por un asset real
debe ser un slice separado que documente procedencia, licencia y dimensiones
sin cambiar la semántica de placement.

## Riesgos e invariantes

- **Riesgo:** contaminar measurements con layouts. **Mitigación:** rutas,
  validación y firmas de dominio separadas.
- **Riesgo:** que un overlay altere la arquitectura. **Mitigación:** namespace
  HSLAYOUT, generator sin reset de escena, snapshot antes/después y comparación
  de proyección arquitectónica.
- **Riesgo:** que el proxy sugiera precisión física inexistente. **Mitigación:**
  `dimensions_status` obligatorio, acceptance `synthetic` y warnings separados
  de errores geométricos.
- **Riesgo:** hacer crecer los módulos room ya grandes. **Mitigación:** módulos
  independientes bajo `blender/scripts/furniture/` y `tests/furniture/`.
- **Invariante:** ningún input se muta durante validación o construcción del
  plan.
- **Invariante:** same canonical layout + same room plan produce same plan,
  signature y overlay lógico.
- **Invariante:** regenerar un layout no elimina otro layout ni objetos
  externos.
- **Invariante:** la fuente arquitectónica nunca se sobrescribe.
- **Invariante:** las medidas del room y sus estados no se reescriben desde
  furniture.

## Criterios de aceptación

- [x] Existe un contrato validable `furniture-layout-1` fuera de
  `measurements/`, con IDs, unidades, coordenadas, dimensiones, estados y
  política de campos desconocidos definidos.
- [x] `build_furniture_plan(layout, room_plan)` es puro, no muta inputs,
  canoniza ordering/yaw y produce `furniture-placement-generator-1` con firma
  lógica estable.
- [x] La validación espacial distingue errores demostrables sobre geometría
  efectiva de warnings heurísticos y conserva los límites de thickness
  fallback y openings proxy.
- [x] El overlay utiliza el namespace HSLAYOUT, no ejecuta reset de escena, no
  modifica `HS3D_ROOM_*`, no sobrescribe el `.blend` fuente y es regenerable por
  layout.
- [x] `normalize_furniture_scene` y
  `compare_furniture_plan_to_scene` son independientes del room adapter y
  detectan entidades ausentes/inesperadas, geometry-vs-metadata, ownership,
  versiones, IDs, transforms y signatures.
- [x] La acceptance real de `living-room-main` demuestra arquitectura antes
  igual a después, fuente intacta, determinismo, report válido, preview y
  `.blend` derivado sin presentar dimensiones sintéticas como reales.
- [x] Los tests cubren schema/contract, plan, spatial validation, ordering,
  signatures, no mutación, regeneración, ownership, malformed input y
  anti-false-pass; los gates existentes de Slices 001–003 siguen pasando.
- [x] La documentación de setup registra comandos, hashes, límites,
  privacidad, provenance parcial y rollback sin modificar los contratos room.

## Evidencia visual

- Requerida: sí, únicamente como preview técnico de la acceptance real.
- Debe comprobarse que los proxies son visibles, sus dimensiones y orientación
  son legibles, el overlay está separado de la arquitectura y el encuadre no
  implica que el proxy sea un modelo real.
- No se exige render artístico ni materiales.

## Evidencia de T4.06

La acceptance canónica usa `layouts/living-room-main/slice-004-acceptance-v1.json`
con tres proxies sintéticos. El `.blend` derivado es
`blender/scenes/review/2026-09-09-living-room-main-slice-004-acceptance-v1-furniture-v1.blend`
con SHA-256
`7A0F5683D11C5203A9A01D8243C3173FE53022217AC7C00F36FB2DE9A18D422F`; el
preview técnico es
`renders/previews/2026-09-09-living-room-main-slice-004-acceptance-v1-furniture-v1/qa-top-orthographic.png`
con SHA-256
`0184EBD44140BB91178FB38E11B800C09B671B4366D95C0D50C4DE26AEA6F773`.
The preview is sanitized by removing non-contractual textual PNG metadata,
including Blender's local `tEXt/File` path, without changing decoded pixels;
the runner checks this privacy invariant.
La fuente generator-2 conserva su SHA esperado antes y después. El detalle de
comandos, reportes, determinismo lógico, anti-false-pass, privacidad,
provenance y rollback está en
`docs/setup/004-furniture-placement-validation.md`.

## Decisiones posteriores a T4.01

- El conjunto inicial cerrado de `type` queda fijado en `sofa`, `coffee_table`,
  `armchair`, `shelf` y `tv_unit`.
- El layout acepta cualquier `yaw_deg` finito en grados; T4.02 normaliza el
  plan a `[0,360)`.
- La política exacta de intersección con wall/opening proxies queda
  implementada y validada en T4.03 usando las primitivas efectivas del room
  plan; el resultado sigue limitado a la geometría proxy representada.
- Los nombres definitivos del artefacto de acceptance y preview versionados se
  cerrarán en T4.06; T4.04 solo genera salidas derivadas nuevas y temporales.

## Evidencia de T4.01

T4.01 queda implementada sin abrir Blender ni tocar el room pipeline:

- schema: `layouts/schema/furniture-layout-v1.schema.json`;
- validator puro: `blender/scripts/furniture/validate_furniture_layout.py`;
- fixture sintético: `layouts/fixtures/furniture-layout-v1-synthetic.json`;
- tests contractuales: `tests/furniture/test_furniture_layout.py`;
- resultado: `26/26 PASS`;
- no se construye furniture plan, no se ejecuta spatial validation y no existe
  todavía overlay, normalizer ni comparator furniture.
