# Especificación: Real-room Scene Comparison and Validation v1

> Clasificación: T2 — comparación determinista entre medidas, plan de generación y escena derivada.
> Estado: contrato, política matemática, comparación pura room → plan y
> extensión de provenance T3.05-P implementados; el adapter Blender y la
> integración de escena siguen pendientes.

## Objetivo

Definir una comparación general, determinista y reutilizable que compruebe la
relación completa:

```text
room JSON canónico → generation plan → representación normalizada de escena
```

El comparador debe detectar pérdida de medidas, estados, provenance,
reconciliaciones, fallbacks, geometría o metadata sin convertir nunca una
escena Blender en fuente de verdad.

El caso de aceptación inicial es `living-room-main`, pero el contrato debe
servir también para room-v1 y para futuras habitaciones autorizadas sin
acoplarse a sus identificadores concretos.

## Problema

El repositorio valida actualmente el JSON, construye un plan determinista y
valida escenas generadas. Sin embargo, la relación entre esas capas no está
expuesta como un informe reutilizable. La validación existente en
`generate_room.py` comprueba una escena Blender concreta, mientras que no
existe todavía una comparación separada que permita probar la lógica sin
lanzar Blender, clasificar discrepancias y preservar explícitamente la
diferencia entre observación y geometría autorizada.

## Alcance

### Incluye

- Contrato versionado de `ComparisonReport`.
- Comparación room ↔ generation plan.
- Comparación generation plan ↔ representación normalizada de escena.
- Adaptador Blender de solo lectura hacia esa representación normalizada.
- Comparación por identificadores canónicos, nunca por orden incidental de
  objetos.
- Clasificación estable de errores, warnings e información.
- Política separada para incertidumbre física y tolerancia computacional.
- Reglas explícitas para `measured`, `estimated`, `derived`, `unknown`,
  fallbacks y reconciliaciones.
- Metadata de paredes, openings, elementos fijos, root collection y escena.
- Tests puros de comparación y casos de mutación controlada.
- Caso real de aceptación `living-room-main` usando evidencia ya versionada.
- Documentación de gates, privacidad, reproducibilidad y rollback.

### Fuera de alcance

- Booleanos o geometría constructiva de puertas y ventanas.
- Cambiar `proxy_only=true` o `constructive_geometry=false` en el caso real.
- Nuevas medidas, nuevas sesiones físicas o nuevas habitaciones reales.
- Modificar el JSON canónico para hacer pasar una comparación.
- Mobiliario, decoración, materiales, iluminación artística o UX.
- LiDAR, fotogrametría, fotos nuevas o datos personales.
- Cambios en Blender MCP o resolución de `get_addon_status`.
- Inferencia `scene → measurement` o promoción de una escena a observación.
- Cambios en los schemas salvo una necesidad contractual demostrada y
  aprobada en una revisión posterior.

## Terminología

- **Room data:** JSON validado bajo schema v1 o v1.1 en `measurements/`.
- **Generation plan:** interpretación JSON-serializable producida por
  `build_generation_plan(room)`.
- **Scene representation:** estructura normalizada, independiente de `bpy`,
  con los objetos y metadatos necesarios para comparar una escena.
- **Observed/source value:** valor conservado en el room y con su `status`,
  método, incertidumbre y `source_id`.
- **Geometry value:** valor autorizado para construir la representación; puede
  ser observado, derivado o fallback explícito.
- **Fallback:** valor de materialización aplicado por el plan cuando el valor
  fuente es `unknown`; no es una observación.
- **Reconciliation:** transformación documentada que conserva la observación
  y produce una geometría efectiva derivada.

## Modelo de autoridad

La jerarquía obligatoria es:

1. `measurements/` es la fuente canónica de observaciones y provenance.
2. El generation plan interpreta un room validado y decide la geometría
   efectiva autorizada.
3. La escena Blender es un artefacto derivado del plan.

Solo el room puede introducir una lectura `measured`. El plan puede copiar un
estado de fuente o calcular un estado `derived`, pero no puede convertir
`unknown` o `estimated` en `measured`. La escena solo puede reflejar los
estados esperados por el plan; nunca puede crear una observación, cambiar el
JSON o corregir una discrepancia.

La comparación debe verificar ambos contextos cuando existan:

- `source_context.observed`: status, source_id, valor e incertidumbre;
- `source_context.effective_geometry`: status, valor efectivo, método de
  derivación, reconciliation_id y fallback;
- `source_context.scene`: status y metadata que la escena realmente conserva.

Un metadata genérico `status` solo será aceptable si su semántica coincide de
forma inequívoca con el campo comparado. Para una geometría derivada se exige
conservar también el contexto de fuente cuando el plan lo proporciona.

## Semántica de estados, unknown y fallback

- `measured`: el room y el plan conservan el valor y el estado `measured`; la
  escena debe conservar el valor efectivo y el estado de fuente. Una pérdida
  del valor, estado o provenance es error.
- `estimated`: conserva `estimated`, incertidumbre y nota. No se promociona a
  `measured`.
- `derived`: conserva fórmula/dependencias o metadata equivalente y se compara
  contra el valor geométrico derivado.
- `unknown`: no tiene valor fuente. El comparador no exige una igualdad de
  observación inexistente.
- Fallback: el plan puede materializar un valor geométrico derivado cuando la
  fuente sea `unknown`. Debe indicar `fallback=true`, el valor, el método y el
  motivo; la escena debe reflejar el mismo contexto.

Ejemplo válido para un espesor no capturado:

```text
room.thickness: status=unknown, sin value
plan.thickness_source_status: unknown
plan.thickness_m: 0.10, thickness_geometry_status=derived, fallback=true
scene: 0.10, source_context.scene.status=unknown,
geometry_status=derived, fallback=true
```

Si la escena etiqueta ese mismo espesor como `measured`, la comparación falla.
Si el room contiene `0.08 measured` y la escena materializa `0.10`, también
falla aunque ambos valores estén dentro de una incertidumbre física posible.

## Reconciliaciones

Cuando existe `reconciled_geometry`, la cadena válida es:

```text
observed value → reconciliation → effective geometry → scene
```

Para `wall-05` el comparador debe conservar `0.45 measured` como observado y
comparar la geometría de pared contra `0.47 derived`. Para `wall-16` debe
conservar `1.00 measured` y comparar la escena contra `0.99 derived`.

No se debe comparar ingenuamente la escena contra el valor observado cuando
existe una geometría reconciliada autorizada. El
`source_context.effective_geometry` debe conservar el `reconciliation_id`, la
indicación de reconciliación y, cuando corresponda, el `source_id` de la
geometría derivada; el contexto observado conserva el `source_id` físico.

## Fases de comparación

El report agregado puede contener findings de dos transiciones distintas, pero
cada finding debe declarar `comparison_stage`:

- `room_to_plan`: comprueba autoridad, estados, provenance, reconciliaciones,
  fallbacks y selección de geometría efectiva.
- `plan_to_scene`: comprueba entidades, geometría, metadata, unidades, flags y
  representación normalizada de la escena.

La fase `room_to_plan` está implementada en `compare_room_to_plan(room, plan)`.
Compara por IDs los segmentos, openings y elementos fijos, verifica la
identidad del plan, unidades, coordenadas, altura, suelo, valores efectivos,
estados, source IDs y flags de proxy/fallback disponibles en el plan. No lee
archivos, no importa `bpy` y no muta ninguna de las dos entradas. Para
`room-v1`, el valor duplicado `plan.height_status` no se usa como autoridad
porque el plan histórico puede sobrescribirlo al procesar metadata de un
elemento fijo; se verifican `height_m` y los estados de altura por pared. El
plan `room-v1.1` sí exige sus campos explícitos de altura observada y
geometría.

### Límite de provenance en T3.04

T3.04 no inventa provenance que el generation plan no transporte. La garantía
actual antes de la extensión T3.05-P era el subconjunto siguiente:

- completa y comprobable: IDs, valores geométricos, estados, unidades,
  source IDs expuestos por el plan, flags de fallback/proxy y metadata de
  reconciliación expuesta (`geometry_reconciled`, `geometry_source_id`);
- parcial/agregada: `source_ids` y `status_index` del plan, y el `source_id`
  único de cada opening/fixed element;
- no expuesta: `method`, `uncertainty`, `formula`, `depends_on`, `reason`,
  `reconciliation_id` y source IDs individuales de campos que no tienen una
  propiedad equivalente en el plan.

Para esos campos la condición es: **not verifiable at room_to_plan with
generation-plan contract current version**. El comparador no los reconstruye
desde otros campos ni genera findings afirmando que fueron preservados. La
provenance completa hasta escena requiere una ampliación posterior y explícita
del contrato del generation plan antes de cerrar la validación `plan_to_scene`.

La fase no se infiere del mensaje: forma parte del contrato y permite saber en
qué transición apareció la discrepancia.

### Extensión de provenance T3.05-P

T3.05-P añade un bloque top-level `provenance` únicamente a los planes de
schema `1.1`. El plan v1 histórico no recibe ese bloque. La versión publicada
antes de esta extensión era `room-v1.1-generator-1`; la versión nueva es
`room-v1.1-generator-2`. El bump es obligatorio porque cambia el contrato del
plan de forma aditiva al transportar metadata por campo; no cambia ninguna
geometría, reconciliación efectiva, fallback, orden de entidades ni consumidor
de las claves geométricas existentes.

La estructura es determinista y no duplica valores físicos que ya viven en el
plan:

```json
{
  "provenance": {
    "room": {
      "height": {"observed": {}, "effective_geometry": {}},
      "floor_area": {"observed": {}, "effective_geometry": {}},
      "measurement_method": "...",
      "measured_at": "..."
    },
    "boundary": {"reconciliation": {}},
    "walls": {"wall-id": {"length": {}, "thickness": {}}},
    "openings": {"opening-id": {"offset": {}, "width": {}, "height": {}, "sill_height": {}, "depth": {}}},
    "fixed_elements": {"element-id": {"height": {}, "anchor": {"offset": {}}}}
  }
}
```

Cada medición usa `observed` y `effective_geometry`. Se transportan
`status`, `uncertainty`, `method`, `note`, `formula`, `depends_on` y
`source_id` cuando existen en el room. La geometría efectiva añade solo
metadata de derivación o trazabilidad: `geometry_status`, `fallback`,
`fallback_value_m`, `reconciliation_id`, `delta_m` y `reason` cuando aplican.
No se añaden `value`, `value_m`, coordenadas, longitudes, alturas, offsets,
anchos, alféizares ni profundidades dentro de este bloque.

La ampliación cubre explícitamente altura de room, área de suelo, longitudes
observadas y reconciliadas de segmentos, reconciliación global, espesores de
pared, los cinco campos de opening y provenance de elementos fijos soportados
por el room. También transporta `measurement_method` y `measured_at` como
metadata de sesión bajo `provenance.room`, porque son campos obligatorios del
contrato room y aportan trazabilidad auditable. Las notas generales, nombres y
etiquetas del sistema de coordenadas siguen siendo datos del room o del plan,
no provenance de campo.

Para planes `room-v1.1-generator-2`, `compare_room_to_plan` verifica el bloque
por IDs y por campo. Una provenance ausente o mutada produce un finding
estructurado; no se reconstruye metadata desde agregados. Un plan
`room-v1.1-generator-1` se rechaza por incompatibilidad de versión y no se
trata silenciosamente como si transportara la extensión.

## ComparisonReport

El contrato conceptual es JSON-serializable, estable y sin timestamps
variables:

```json
{
  "report_version": "room-scene-comparison-1",
  "valid": true,
  "room_id": "living-room-main",
  "schema_version": "1.1",
  "generation_plan_version": "room-v1.1-generator-2",
  "scene_adapter_version": "room-scene-adapter-1",
  "comparison_stages": ["room_to_plan", "plan_to_scene"],
  "discrepancies": [],
  "warnings": [],
  "info": [],
  "summary": {
    "errors": 0,
    "warnings": 0,
    "info": 0,
    "checked_entities": 0
  }
}
```

`discrepancies` contiene findings bloqueantes. `warnings` contiene findings
no bloqueantes; ambos usan el mismo contrato de finding. `info` se reserva
para resultados útiles que no representan una divergencia. Las listas deben
estar ordenadas de forma determinista.

Cada finding contiene como mínimo:

```json
{
  "code": "wall_geometry_mismatch",
  "severity": "error",
  "comparison_stage": "plan_to_scene",
  "entity_type": "wall",
  "entity_id": "wall-05",
  "path": "walls[wall-05].geometry_length_m",
  "expected": 0.47,
  "actual": 0.45,
  "tolerance": {"kind": "computational", "value_m": 0.000001},
  "source_context": {
    "observed": {
      "status": "measured",
      "source_id": "living-room-main-2026-09-06-session-01-wall-05-length"
    },
    "effective_geometry": {
      "status": "derived",
      "source_id": "living-room-main-2026-09-06-session-01-wall-05-reconciled-length",
      "reconciliation_id": "living-room-main-boundary-closure-01",
      "fallback": false
    },
    "scene": {
      "status": "derived",
      "source_id": null,
      "geometry_status": "derived",
      "fallback": false
    }
  },
  "message": "scene geometry does not match the reconciled generation value"
}
```

`expected` procede del plan o de la regla contractual; `actual` procede de la
representación normalizada de escena. `source_context` distingue el contexto
observado, la geometría efectiva y la escena sin duplicar sus valores
numéricos; cada `source_id` puede ser `null` cuando no aplique, pero nunca se
sustituye por una ruta personal. Los valores no disponibles se expresan como
`null`, no como cero. Los mensajes son estables y no incluyen rutas personales,
timestamps ni valores no deterministas.

El resultado `valid` es `false` si existe al menos un finding con severity
`error`. Warnings e info no invalidan la comparación, pero deben quedar
contabilizados.

## Severidades y códigos mínimos

### Error / bloqueante

- `expected_object_missing`
- `unexpected_object`
- `geometry_value_mismatch`
- `room_height_mismatch`
- `opening_value_mismatch`
- `wall_thickness_mismatch`
- `metadata_status_mismatch`
- `unknown_promoted`
- `measured_downgraded`
- `provenance_missing`
- `provenance_mismatch`
- `fallback_mismatch`
- `reconciliation_mismatch`
- `proxy_flag_mismatch`
- `constructive_geometry_mismatch`
- `logical_signature_mismatch`
- `scene_units_mismatch`
- `duplicate_managed_entity_id`
- `malformed_normalized_entity`
- `report_version_mismatch`
- `scene_adapter_version_mismatch`
- `generation_plan_version_mismatch`
- `reconciliation_metadata_missing`
- `fallback_provenance_mismatch`

### Warning / no bloqueante

- `optional_metadata_missing`, solo para metadata no requerida por el contrato
  actual.
- `future_field_not_consumed`, solo si el campo es explícitamente futuro y no
  afecta a la geometría ni a la trazabilidad actual.

Una diferencia numérica fuera de la tolerancia computacional es error, no
warning. Una diferencia dentro de tolerancia no crea finding salvo que se
registre como `info` para diagnóstico.

## Política de tolerancias

La incertidumbre física y la tolerancia computacional son conceptos distintos:

- La incertidumbre `±0.01 m` describe la confianza de una lectura física.
- La comparación plan → escena verifica que Blender represente el plan, no
  que vuelva a medir la habitación.
- El comparador reutiliza `MATH_TOLERANCE_M = 1e-6 m`, ya usado por el
  validator y `validate_generated_scene`, para longitudes, offsets, alturas,
  alféizares, profundidades, espesores y coordenadas derivadas.
- Los vectores se comparan componente a componente con esa tolerancia.
- Las áreas se comparan en `m²`, nunca con una tolerancia expresada en metros.
  Para un polígono esperado con coordenadas `(x_i, y_i)` y tolerancia lineal
  `τ = 1e-6 m`, se calcula una referencia única `r = (r_x, r_y)` como el
  centro de su bounding box:

  `r_x = (min_i x_i + max_i x_i) / 2`,
  `r_y = (min_i y_i + max_i y_i) / 2`.

  Se usan las coordenadas recentradas `x'_i = x_i - r_x` y
  `y'_i = y_i - r_y`. La tolerancia computacional derivada es:

  `τ_area = 0.5 × Σ_i(τ × (|x'_i| + |y'_i| + |x'_(i+1)| + |y'_(i+1)|) + 2τ²)`.

  La misma referencia calculada desde el polígono esperado debe reutilizarse
  para el polígono actual; no se recalcula independientemente. La traslación
  común conserva las diferencias de coordenadas y el área de Shoelace, por lo
  que la cota es invariante ante traslación y sigue siendo conservadora. La
  fórmula expresa propagación dimensional de coordenadas a área. Si una
  comparación de área no puede derivarse de coordenadas normalizadas, debe
  declarar una tolerancia explícita en `m²` y no reutilizar `1e-6 m`.
- Estados, flags, IDs, fórmulas, dependencias y nombres se comparan
  exactamente.
- La incertidumbre del room no se suma automáticamente a la tolerancia de la
  escena. Solo una regla contractual de reconciliación puede autorizar una
  diferencia de observación, y esa diferencia debe estar registrada en el
  room/plan.
- Si una limitación concreta de serialización Blender exige otra tolerancia,
  debe probarse, documentarse y aprobarse antes de cambiar esta política; no
  se introduce una tolerancia global arbitraria.

## Openings

El comparador verifica la representación actual, no la futura. Para cada uno
de los seis openings de `living-room-main` comprueba:

- `wall_id`;
- offset y status;
- width y status;
- height y status;
- `sill_height` y status cuando aplica;
- depth y status;
- `geometry_height_proxy`, `geometry_sill_height_proxy` y
  `geometry_depth_proxy`;
- `proxy_only` y `constructive_geometry`;
- `source_id` y metadata de geometría.

En el caso real los proxies verticales activos son cero, mientras que
`proxy_only=true` y `constructive_geometry=false` son valores esperados. El
comparador no exige booleanos ni crea geometría constructiva.

## Entidades Blender gestionadas

El dominio gestionado no es todo `bpy.data`. Se limita a la colección raíz
determinista `HS3D_ROOM_<room_id>` y a sus colecciones hijas con los roles que
ya usa el generator: `Architecture`, `Openings`, `FixedElements` y
`Validation`.

Dentro de ese dominio son entidades gestionadas los objetos con roles
`floor`, `wall`, `opening_proxy`, `fixed_element_proxy`, `preview_camera` y
`preview_light`, junto con sus IDs/nombres `HS3D_*` y metadata `hs3d_*`.
Las cámaras y luces de preview son auxiliares permitidos porque pertenecen a
`Validation` y llevan su role explícito. Un objeto no gestionado fuera de la
raíz, sin prefijo/role Home Studio 3D, se ignora. Un objeto `HS3D_*` fuera de
la raíz, un role Home Studio 3D desconocido dentro de la raíz o una entidad
gestionada duplicada es error.

Por tanto:

- entidad gestionada esperada ausente → error;
- entidad gestionada inesperada → error;
- auxiliar no gestionado permitido → ignorado, o info si se solicita un
  inventario diagnóstico;
- auxiliar con metadata Home Studio 3D malformada → error.

La regla reutiliza la raíz, colecciones, prefijos y metadata existentes; no
crea una convención paralela.

## Determinismo y versionado

El orden canónico de findings es:

1. severidad (`error`, `warning`, `info`);
2. `comparison_stage` (`room_to_plan`, `plan_to_scene`);
3. `entity_type`;
4. `entity_id`, usando cadena vacía para `null`;
5. `path`;
6. `code`.

Las entidades se normalizan por ID antes de comparar. Las listas que
representan colecciones de entidades se ordenan por ID; las listas que son
vectores conservan su orden semántico. Los mapas se serializan con claves
ordenadas. Los floats deben ser finitos y se normaliza `-0.0` a `0.0`; no se
redondean antes de comparar. La serialización estable usa claves ordenadas,
separadores compactos y no incluye timestamps, handles Blender ni rutas
locales. `expected` y `actual` deben usar la misma normalización recursiva.

Una golden hash nueva del report no es requisito inicial: el contrato exige
serialización estable y tests de igualdad, mientras que la golden histórica
obligatoria continúa siendo la firma lógica de room-v1.

Las versiones tienen responsabilidades separadas:

- `report_version` cambia cuando cambia la forma o semántica de
  `ComparisonReport`, findings, severidades u orden canónico.
- `scene_adapter_version` cambia cuando cambia la normalización Blender,
  ownership, roles, campos extraídos o su interpretación.
- `generation_plan_version` se copia del plan (`room-v1-generator-1` o
  `room-v1.1-generator-2`) y cambia cuando cambia el contrato del plan.
- `schema_version` identifica el room de entrada y no se usa como alias de
  `report_version`.

Un informe debe conservar las cuatro versiones cuando sean aplicables para
permitir reproducir qué contrato produjo el resultado.

## Arquitectura y testabilidad

La implementación futura separará:

1. **Comparison core:** recibe room validado, generation plan y una
   representación normalizada de escena; no importa `bpy`.
2. **Blender adapter:** lee una escena abierta en Blender, extrae solo objetos,
   nombres, geometría, unidades y custom properties autorizadas, y produce la
   representación normalizada.
3. **Report:** ordena findings, calcula `valid` y genera la firma estable del
   informe si se necesita.

El core debe ser la parte principal de los tests. El adapter y la integración
Blender se validan con la evidencia disponible y con una ejecución controlada
solo cuando la tarea de implementación tenga autorización explícita.

La política pura compartida de fallbacks y el cálculo Shoelace viven en
`blender/scripts/measurements/generation_policy.py`. El generator conserva sus
nombres históricos mediante aliases; el comparador consume la misma fuente.

## Compatibilidad y determinismo

- room-v1 se soporta desde el inicio usando sus campos históricos; no se exige
  metadata v1.1 que no exista.
- room-v1.1 añade comprobaciones de observed/geometry, reconciliación,
  fallbacks y provenance de campo mediante `room-v1.1-generator-2`.
- El fixture v1 debe conservar exactamente la golden signature:
  `1105946a0dfe0088f5ad59da4178939644305b0d09b94022bfe5c87d9dde36f0`.
- El comparador no cambia schemas ni altera el room recibido.
- La comparación se hace por `id`; el orden de objetos y colecciones no
  modifica el resultado.
- T3.04 mantiene la compatibilidad v1 sin exigir campos exclusivos de v1.1;
  la limitación documentada de `height_status` histórico no cambia el plan ni
  su golden signature.
- Findings, summary y cualquier firma usan orden estable, claves ordenadas y
  representación numérica normalizada.

## Privacidad y provenance

El informe solo puede contener IDs canónicos, estados, valores, fórmulas,
metadata de escena y mensajes técnicos. No debe incluir rutas personales,
fotos, EXIF, secretos, tokens ni contenido de archivos externos. `source_id`
preserva trazabilidad sin convertir una ruta local en provenance versionable.

## Caso de aceptación: living-room-main

El caso real debe verificar:

El core no contiene IDs de esta habitación: usa `entity_type`, IDs canónicos,
paths y capacidades del schema. `living-room-main` es un acceptance case que
ejercita reconciliación, medidas, unknown/fallback y proxies; los fixtures
synthetic v1/v1.1 y cualquier habitación compatible deben usar el mismo
contrato.

- 22 segmentos y 6 openings.
- Altura `2.50 m measured`, con geometry height `2.50 m measured` y fallback
  desactivado.
- `wall-05`: `0.45 observed` frente a `0.47 geometry derived`.
- `wall-16`: `1.00 observed` frente a `0.99 geometry derived`.
- V2: offset `0.64 m derived`, width `2.40 m measured`.
- Seis espesores `0.08 m measured`.
- Dieciséis espesores `unknown` con fallback `0.10 m derived`.
- Cero proxies verticales activos.
- `proxy_only=true` y `constructive_geometry=false` para los openings.
- Artefactos existentes sin regenerarlos:
  - `blender/scenes/review/2026-09-07-living-room-main-v1.1-regenerated.blend`
    SHA-256 `79D9ECCFE874A0DFA507638871462F260C6BD678C8A5E78860461B3A71911DC5`.
  - `renders/previews/2026-09-07-living-room-main-v1.1-regenerated/qa-top-orthographic.png`
    SHA-256 `E11C9C6B17D0B243705217EC0A73D8523A5F02C46342333131B0421ED4818072`.

## Failure cases de regresión

La implementación futura tendrá mutaciones controladas para wall missing,
opening missing, unexpected managed object, duplicate managed entity ID,
normalized entity malformada, longitud de pared incorrecta, altura de
habitación incorrecta, espesor incorrecto, width/height/sill/depth/offset de
opening incorrectos, unidades incorrectas, versión de report/adapter/plan
incompatible, `measured → derived`, `unknown → measured`, fallback perdido,
provenance de fallback incorrecta, reconciliación ignorada, metadata de
reconciliación ausente, flags `proxy_only` o `constructive_geometry`
incorrectos y provenance perdida.

También debe existir un caso positivo con auxiliares no gestionados permitidos
fuera de la colección raíz.

También tendrá un caso positivo donde el orden de objetos cambie sin cambiar
los IDs; ese caso debe seguir siendo válido.

## Criterios de aceptación

1. Existe un `ComparisonReport` versionado y determinista con errores,
   warnings, info y summary.
2. El core funciona sin Blender y cubre room-v1 y room-v1.1.
3. La jerarquía room → plan → scene está aplicada sin promoción scene →
   measurement.
4. Las reconciliaciones de `wall-05` y `wall-16` se comparan contra la
   geometría efectiva, conservando las observaciones.
5. Unknown/fallback, provenance y estados producen los resultados definidos.
6. Los seis openings reales pasan con sus flags actuales y sin booleanos.
7. Todas las mutaciones bloqueantes producen `valid=false` y un código estable.
8. El orden incidental no afecta al informe.
9. room-v1 y su golden signature permanecen intactos.
10. Los gates de calidad, privacidad, documentación y reproducibilidad quedan
    registrados con evidencia real.

## Riesgos y rollback

El principal riesgo es mezclar incertidumbre física con exactitud de la
representación derivada. También existe riesgo de acoplar el comparador a
`living-room-main` o a nombres Blender concretos. La mitigación es mantener un
core por IDs, un adapter explícito y fixtures sintéticos.

El rollback elimina el comparador y sus tests/documentación sin tocar schemas,
JSON reales, escenas ni previews. Los artefactos derivados continúan siendo
regenerables desde los contratos existentes.

## Decisiones no pendientes para implementar

- El comparador soporta v1 y v1.1 desde el inicio.
- `1e-6 m` es la tolerancia computacional inicial heredada.
- La incertidumbre física no relaja la comparación plan → escena.
- `unknown` nunca adquiere un valor observado por efecto de la escena.
- No se implementan booleanos en este slice.
- Los datos reales y artefactos del slice 002 no se modifican.
