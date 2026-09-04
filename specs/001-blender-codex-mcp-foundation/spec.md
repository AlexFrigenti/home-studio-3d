# Especificación: Blender + Codex + MCP Foundation

> Clasificación: T2 — complejo o sensible
> Rama: `spec/001-blender-codex-mcp-foundation`
> Estado: propuesta documental para aprobación antes de instalar o configurar nada

## Objetivo del slice

Definir una base local, segura y reproducible para que Codex CLI pueda trabajar con Blender 5.2 LTS mediante un MCP de Blender limitado a localhost, usar `bpy` como capacidad privilegiada y validar escenas mediante comprobaciones numéricas y evidencia visual.

El primer entorno objetivo será el portátil. Después, la instalación y la configuración se documentarán para replicarlas en el PC de sobremesa sin convertir ninguna máquina en autoridad sobre las medidas del proyecto.

## Problema

El proyecto todavía no tiene un procedimiento aprobado para instalar Blender, elegir y aislar el MCP, conectar Codex CLI, limitar el acceso a archivos o verificar que una operación agentic produjo una escena válida. Sin una base común, pueden aparecer puertos expuestos, rutas locales frágiles, instalaciones no reproducibles, escenas corruptas o resultados visualmente plausibles pero dimensionalmente incorrectos.

## Alcance

### Incluye

- Inventario reproducible del entorno inicial del portátil.
- Procedimiento futuro para Blender 5.2 LTS, Codex CLI y el MCP candidato.
- Arquitectura y límites de confianza de la conexión local.
- Integración de Codex con MCP usando `webita/blender-codex-mcp` como referencia específica, sin asumir que sea una dependencia obligatoria.
- Uso controlado de `execute_blender_code`/`bpy` como capacidad privilegiada.
- Smoke técnico y test de aceptación de una habitación sintética mínima.
- Validación numérica de dimensiones, transformaciones y unidades.
- Captura de viewport o render preview e inspección visual explícita.
- Documentación para repetir el procedimiento posteriormente en el sobremesa.

### Fuera de alcance

- Cualquier instalación o configuración durante esta fase documental.
- Instalación de Blender, Python, `uv`, MCP, addons, paquetes o dependencias.
- Modificación de configuración global de Codex o Blender.
- Integración con servicios MCP remotos, LAN o Internet.
- Dependencia de GPT-6 Astra; el flujo debe funcionar con el agente disponible y ser compatible con Astra cuando esté disponible.
- Modelado del salón real o modificación de `measurements/` canónico.
- Uso de assets externos, modelos descargados, servicios de pago o créditos de generación.
- Git LFS, pipelines de producción, exports finales o renders finales pesados.

## Arquitectura objetivo

```text
Codex CLI -> MCP local -> Blender -> bpy -> viewport/render -> verificación
```

Responsabilidades y límites:

- Codex CLI inicia el trabajo desde el repositorio y mantiene el alcance del cambio.
- El MCP es un adaptador local; debe escuchar únicamente en `localhost`/loopback y no exponerse a LAN o Internet.
- Blender posee la escena abierta y ofrece el entorno de ejecución 3D.
- `execute_blender_code`/`bpy` puede modificar la escena y por eso se trata como capacidad privilegiada: el código se inspecciona, se limita al workspace y se ejecuta solo con autorización y validación proporcionales.
- Viewport/render produce evidencia visual, pero no sustituye las comprobaciones numéricas.
- La verificación contrasta dimensiones, transformaciones, unidades, integridad de la escena y límites de seguridad.

## Decisiones técnicas y operativas

- Línea de Blender elegida: **Blender 5.2 LTS**.
- MCP candidato principal: **`ahujasid/blender-mcp`**. Su fuente, versión, licencia, compatibilidad y configuración se revisarán antes de incorporarlo.
- Referencia específica de integración con Codex: **`webita/blender-codex-mcp`**. Se usará para entender el acoplamiento Codex/MCP, no como permiso para copiar código sin inspección.
- Transporte: solo conexión local mediante loopback; no se aceptan binds a `0.0.0.0`, interfaces LAN o exposición pública.
- Telemetría opcional: deshabilitarla si el MCP permite hacerlo razonablemente; registrar la limitación si no existe esa opción.
- Codex es el agente principal. GPT-6 Astra no es un requisito de funcionamiento; la integración debe dejar una ruta compatible para adoptarlo en el futuro.
- Las medidas estructuradas siguen siendo la fuente de verdad. Las escenas Blender son representaciones verificables y no redefinen las medidas.
- Las unidades internas serán metros, con unidades explícitas en escena y documentación.
- La primera estación validada será el portátil; el PC con RTX 3080 de 10 GB de VRAM y 32 GB de RAM se usará posteriormente como segunda estación.

## Criterios de aceptación

La fundación será válida cuando, con evidencia real y sin secretos:

1. Blender 5.2 LTS pueda iniciarse correctamente.
2. Codex CLI pueda trabajar desde el repositorio.
3. El MCP pueda arrancar localmente.
4. Codex pueda obtener información de la escena abierta.
5. Codex pueda crear una escena de prueba controlada.
6. Codex pueda ejecutar una operación `bpy` simple y acotada.
7. Codex pueda obtener una captura de viewport o evidencia visual equivalente.
8. Codex pueda verificar numéricamente una dimensión conocida.
9. Blender pueda guardar la escena de prueba dentro del workspace.
10. Ningún servicio MCP quede escuchando fuera de localhost.
11. No se introduzcan secretos, credenciales ni datos privados en código, configuración, escenas o commits.
12. No se utilicen servicios de pago ni créditos externos.
13. El procedimiento de instalación y validación pueda repetirse después en el sobremesa, registrando las diferencias de hardware y rutas.

## Test de aceptación funcional

El test final usa una escena sintética y desechable; no representa medidas reales de la vivienda y no usa assets externos.

### Habitación mínima

- Dimensiones interiores: `5.00 m × 4.00 m`.
- Altura interior: `2.50 m`.
- Sistema de coordenadas documentado: origen en una esquina interior del suelo; `x` recorre 5.00 m, `y` recorre 4.00 m y `z` recorre 2.50 m.
- Un suelo y paredes simples con una puerta y una ventana.
- Una puerta y una ventana pueden usar dimensiones sintéticas documentadas en la escena de prueba; no se presentan como medidas reales.
- Un cubo llamado `sofa_proxy` como sofá proxy, con tamaño conocido y posición conocida.
- Una cámara y una luz.
- Escena prevista para el área de pruebas `blender/scenes/tests/001-foundation-room.blend`; nunca debe sustituir una escena canónica.
- Captura de viewport o render preview, sin render final pesado.

### Comprobaciones mínimas

El agente debe comprobar numéricamente, y dejar evidencia de los valores:

- largo interior: `5.00 m`;
- ancho interior: `4.00 m`;
- altura interior: `2.50 m`;
- posición y tamaño de `sofa_proxy`.

La validación debe comprobar también que la escena usa metros, que el archivo abre y guarda, y que la inspección visual no muestra una desviación concreta en suelo, paredes, puerta, ventana, sofá proxy, cámara o luz.

## Riesgos T2 y mitigaciones

| Riesgo | Mitigación exigida |
| --- | --- |
| Ejecución arbitraria de Python | Inspeccionar el código, limitar el alcance al workspace, usar escenas desechables y exigir revisión/evidencia antes de operaciones sensibles. |
| Acceso a archivos | Prohibir acceso fuera del workspace salvo autorización expresa; no permitir rutas construidas desde entradas no confiables. |
| Addons de terceros | Revisar procedencia, licencia, versión, permisos y código antes de instalar; instalar solo con autorización. |
| Integridad de escenas | Guardar snapshots o variantes, no sobrescribir escenas canónicas y validar apertura/guardado antes de aceptar. |
| Exposición de puertos | Comprobar binding efectivo en loopback; rechazar `0.0.0.0`, interfaces LAN y túneles no aprobados. |
| Instalaciones no reproducibles | Fijar versión, fuente, configuración, rutas portables y pasos repetibles; documentar hashes cuando sea posible. |
| Diferencias entre portátil y sobremesa | Validar primero el portátil, registrar hardware/rutas y repetir el smoke en el sobremesa con las mismas invariantes. |
| Rutas locales distintas | Usar rutas relativas al repo o variables documentadas; no versionar rutas absolutas personales. |
| Consumo de GPU/VRAM | Usar previews, observar el presupuesto de 10 GB de VRAM del PC y registrar cualquier operación costosa antes de ejecutarla. |
| Dependencia de MCP de terceros | Mantenerlo como candidato revisado, fijar una versión/commit cuando se adopte y registrar incompatibilidades conocidas. |
| Cambios upstream del MCP | No seguir una rama mutable sin revisión; repetir el smoke tras actualizar y mantener la configuración reversible. |
| Incompatibilidades con Blender 5.2 | Verificar versión exacta, API usada, apertura de escena y operación `bpy` mínima antes de avanzar. |

## Invariantes

- El MCP solo escucha en localhost/loopback.
- Ninguna credencial, secreto, token o configuración sensible se versiona.
- `measurements/` sigue siendo la fuente de verdad.
- Blender representa las medidas y no las redefine.
- Las escenas canónicas nunca se sobrescriben con pruebas.
- Los tests iniciales usan escenas sintéticas y desechables.
- No existe acceso fuera del workspace salvo autorización expresa.
- No se realizan operaciones destructivas irreversibles sin snapshot o una reversibilidad equivalente.
- No se realizan renders finales pesados durante el setup.
- Los tests no dependen de GPT-6 Astra para funcionar.
- No se incorporan assets externos ni modelos descargados en este slice.

## Autorizaciones explícitas requeridas

Antes de cada etapa sensible se debe solicitar autorización para instalar Blender o componentes MCP, modificar configuración de Codex o Blender, instalar addons, ejecutar código `bpy` privilegiado, abrir puertos aunque sean locales, borrar escenas de prueba o repetir el setup en el sobremesa. La aprobación de esta especificación no autoriza por sí sola esas operaciones futuras.
