# Especificación: Blender + Codex + MCP Foundation

> Clasificación: T2 — complejo o sensible
> Rama: `spec/001-blender-codex-mcp-foundation`
> Estado: propuesta documental para aprobación antes de instalar o configurar nada

## Objetivo del slice

Definir una base local, segura y reproducible para que Codex CLI pueda trabajar con Blender 5.2.1 LTS, dentro de la línea de soporte 5.2 LTS, mediante un MCP de Blender limitado a localhost, usar `bpy` como capacidad privilegiada y validar escenas mediante comprobaciones numéricas y evidencia visual.

El primer entorno objetivo será el portátil. Después, la instalación y la configuración se documentarán para replicarlas en el PC de sobremesa sin convertir ninguna máquina en autoridad sobre las medidas del proyecto.

## Problema

El proyecto todavía no tiene un procedimiento aprobado para instalar Blender, elegir y aislar el MCP, conectar Codex CLI, limitar el acceso a archivos o verificar que una operación agentic produjo una escena válida. Sin una base común, pueden aparecer puertos expuestos, rutas locales frágiles, instalaciones no reproducibles, escenas corruptas o resultados visualmente plausibles pero dimensionalmente incorrectos.

## Alcance

### Incluye

- Inventario reproducible del entorno inicial del portátil.
- Procedimiento futuro para Blender 5.2.1 LTS, Codex CLI y el MCP candidato.
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
- `execute_blender_code`/`bpy` puede modificar la escena y por eso se trata como capacidad privilegiada: el código se inspecciona, se ejecuta solo con autorización y validación proporcionales, y queda sujeto a la política de no acceder fuera del workspace sin autorización. Esta política no implica que Blender/Python ofrezca por sí mismo un sandbox técnico del workspace.
- Viewport/render produce evidencia visual, pero no sustituye las comprobaciones numéricas.
- La verificación contrasta dimensiones, transformaciones, unidades, integridad de la escena y límites de seguridad.

## Seguridad: política frente a garantía técnica

### A. Invariante de política

El agente tiene prohibido acceder, modificar o borrar archivos fuera del workspace sin autorización expresa. Esta restricción es una regla operativa del proyecto y se aplica aunque el proceso tenga permisos más amplios.

### B. Garantía técnica

No se asumirá que Blender, Python o `bpy` impidan técnicamente el acceso fuera del workspace. El proceso puede conservar las capacidades que le otorguen el sistema operativo y sus permisos.

La validación técnica puede comprobar, cuando exista instrumentación suficiente:

- el código y los comandos realmente ejecutados;
- las rutas explícitas y el directorio de trabajo;
- la configuración de sandbox, contenedor o permisos del proceso, si existe;
- registros de auditoría de acceso a archivos, si el sistema los ofrece;
- los bindings y conexiones de red efectivos.

La política de `AGENTS.md` por sí sola nunca permite marcar como `PASS` un control técnico de “acceso limitado al workspace”. Si no hay una garantía técnica o evidencia de auditoría disponible, el control se marca como `PENDIENTE DE INFRAESTRUCTURA` o `NO EJECUTADO`; una operación `bpy` de solo lectura sin llamadas de filesystem demuestra únicamente el alcance de esa operación concreta.

## Decisiones técnicas y operativas

- Línea de soporte de Blender: **Blender 5.2 LTS**. Versión inicial objetivo: **Blender 5.2.1 LTS**.
- En Windows, T2.03 comparará antes de descargar o instalar el instalador tradicional y la distribución portable ZIP oficial. La opción portable será preferente si cumple los criterios de versión, funcionamiento, rutas reproducibles, ausencia de cambios globales innecesarios y rollback sencillo. T2.03 debe registrar la decisión; este documento no la fija todavía.
- MCP candidato principal: **`ahujasid/blender-mcp`**. No se instalará desde una rama mutable sin pin: debe fijarse a una versión, tag o commit exacto aprobado y registrar el commit elegido antes de instalar. El pin definitivo queda pendiente de T2.05; cualquier actualización posterior obliga a repetir el smoke y el test de aceptación.
- Referencia específica de integración con Codex: **`webita/blender-codex-mcp`**. Se usará para entender el acoplamiento Codex/MCP, no como permiso para copiar código sin inspección.
- Transporte: solo conexión local mediante loopback; no se aceptan binds a `0.0.0.0`, interfaces LAN o exposición pública.
- Telemetría opcional: deshabilitarla si el MCP permite hacerlo razonablemente; registrar la limitación si no existe esa opción.
- Codex es el agente principal. GPT-6 Astra no es un requisito de funcionamiento; la integración debe dejar una ruta compatible para adoptarlo en el futuro.
- Las medidas estructuradas siguen siendo la fuente de verdad. Las escenas Blender son representaciones verificables y no redefinen las medidas.
- Las unidades internas serán metros, con unidades explícitas en escena y documentación.
- La primera estación validada será el portátil; el PC con RTX 3080 de 10 GB de VRAM y 32 GB de RAM se usará posteriormente como segunda estación.

## Criterios de aceptación

La fundación será válida cuando, con evidencia real y sin secretos:

1. Blender 5.2.1 LTS pueda iniciarse correctamente.
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

- Volumen interior determinista: `X: 0.00 → 5.00 m`, `Y: 0.00 → 4.00 m`, `Z: 0.00 → 2.50 m`.
- Las caras interiores `x=0`, `x=5`, `y=0`, `y=4`, `z=0` y `z=2.50` son la referencia de validación.
- Si se modela grosor, las paredes crecen hacia fuera del volumen interior: `x=0` hacia `x<0`, `x=5` hacia `x>5`, `y=0` hacia `y<0` y `y=4` hacia `y>4`; un grosor de prueba de `0.20 m` se ubica en esos sentidos y no altera las caras interiores. El suelo puede crecer hacia `z<0` y el techo hacia `z>2.50`.
- Suelo y paredes simples con una puerta y una ventana. Todos los valores siguientes son sintéticos, no medidas reales de la vivienda:

  | Elemento | Dimensiones `X × Y × Z` | Centro `(X, Y, Z)` | Contrato geométrico |
  | --- | --- | --- | --- |
  | `door` | `0.90 × 0.05 × 2.10 m` | `(1.45, -0.025, 1.05) m` | Abertura en la cara interior `y=0`, `x=1.00..1.90 m`, `z=0.00..2.10 m`; hoja hacia fuera en `-Y`. |
  | `window` | `0.05 × 1.20 × 1.00 m` | `(5.025, 2.00, 1.50) m` | Abertura en la cara interior `x=5`, `y=1.40..2.60 m`, `z=1.00..2.00 m`; panel hacia fuera en `+X`. |
  | `sofa_proxy` | `1.80 × 0.80 × 0.90 m` | `(2.50, 2.00, 0.45) m` | Rotación `(0, 0, 0)`; límites `x=1.60..3.40`, `y=1.60..2.40`, `z=0.00..0.90 m`. |

- Una cámara y una luz.
- Escena prevista para el área de pruebas `blender/scenes/tests/001-foundation-room.blend`; nunca debe sustituir una escena canónica.
- Captura de viewport o render preview, sin render final pesado.
- La escena debe recrearse de forma determinista en portátil y sobremesa usando los mismos nombres, constantes, sistema de coordenadas y transformaciones, sin aleatoriedad ni assets externos.

### Comprobaciones mínimas

El agente debe comprobar numéricamente, y dejar evidencia de los valores:

- largo interior: `5.00 m`;
- ancho interior: `4.00 m`;
- altura interior: `2.50 m`;
- posición y tamaño de `sofa_proxy`.

La validación debe comprobar también que la escena usa metros, que las caras interiores mantienen el contrato sin que el grosor de pared las desplace, que puerta, ventana y `sofa_proxy` coinciden con sus dimensiones y posiciones sintéticas, que el archivo abre y guarda, y que la inspección visual no muestra una desviación concreta en suelo, paredes, puerta, ventana, sofá proxy, cámara o luz.

### Primera operación `bpy` del smoke

En T2.08, la primera operación `bpy` será una inspección de solo lectura, inocua y reversible (no cambia el estado), por ejemplo consultar `bpy.context.scene.name` y el número de objetos de la escena. No realizará llamadas de filesystem, red ni procesos externos. Después, cualquier guardado deberá ser una operación explícita a una escena de prueba dentro del workspace; la ausencia de llamadas en esta primera operación no constituye un sandbox técnico general.

## Riesgos T2 y mitigaciones

| Riesgo | Mitigación exigida |
| --- | --- |
| Ejecución arbitraria de Python | Inspeccionar el código, aplicar la política de no acceso fuera del workspace, no asumir sandbox técnico, usar escenas desechables y exigir revisión/evidencia antes de operaciones sensibles. |
| Acceso a archivos | La política prohíbe acceso fuera del workspace salvo autorización expresa; la garantía técnica depende de permisos, sandbox o auditoría del proceso y debe validarse por separado. |
| Addons de terceros | Revisar procedencia, licencia, versión, permisos y código antes de instalar; instalar solo con autorización. |
| Integridad de escenas | Guardar snapshots o variantes, no sobrescribir escenas canónicas y validar apertura/guardado antes de aceptar. |
| Exposición de puertos | Comprobar binding efectivo en loopback; rechazar `0.0.0.0`, interfaces LAN y túneles no aprobados. |
| Instalaciones no reproducibles | Fijar versión, fuente, configuración, rutas portables y pasos repetibles; documentar hashes cuando sea posible. |
| Diferencias entre portátil y sobremesa | Validar primero el portátil, registrar hardware/rutas y repetir el smoke en el sobremesa con las mismas invariantes. |
| Rutas locales distintas | Usar rutas relativas al repo o variables documentadas; no versionar rutas absolutas personales. |
| Consumo de GPU/VRAM | Usar previews, observar el presupuesto de 10 GB de VRAM del PC y registrar cualquier operación costosa antes de ejecutarla. |
| Dependencia de MCP de terceros | Mantenerlo como candidato revisado, fijar un tag/versión/commit exacto antes de instalar y registrar incompatibilidades conocidas. |
| Cambios upstream del MCP | No seguir una rama mutable sin pin; cualquier actualización exige repetir el smoke y la aceptación antes de adoptarse. |
| Incompatibilidades con Blender 5.2.1 LTS | Verificar versión exacta, API usada, apertura de escena y operación `bpy` mínima antes de avanzar. |

## Invariantes

- El MCP solo escucha en localhost/loopback.
- El MCP no se instala desde una rama mutable sin pin; el tag/versión/commit aprobado se registra antes de instalar y sus actualizaciones repiten smoke y aceptación.
- Ninguna credencial, secreto, token o configuración sensible se versiona.
- `measurements/` sigue siendo la fuente de verdad.
- Blender representa las medidas y no las redefine.
- Las escenas canónicas nunca se sobrescriben con pruebas.
- Los tests iniciales usan escenas sintéticas y desechables.
- Política: el agente tiene prohibido acceder, modificar o borrar fuera del workspace sin autorización expresa.
- Garantía técnica: no se asume que Blender/Python/`bpy` impidan por sí mismos ese acceso; un `PASS` requiere evidencia técnica de permisos, sandbox o auditoría, no solo una regla de `AGENTS.md`.
- No se realizan operaciones destructivas irreversibles sin snapshot o una reversibilidad equivalente.
- No se realizan renders finales pesados durante el setup.
- La primera operación `bpy` de T2.08 es de solo lectura, reversible y sin filesystem; los guardados posteriores son explícitos y quedan dentro del workspace.
- La habitación sintética usa exactamente el contrato de coordenadas, objetos, dimensiones y posiciones documentado, sin aleatoriedad.
- Los tests no dependen de GPT-6 Astra para funcionar.
- No se incorporan assets externos ni modelos descargados en este slice.

## Autorizaciones explícitas requeridas

Antes de cada etapa sensible se debe solicitar autorización para descargar o instalar Blender 5.2.1 LTS, seleccionar e instalar el pin del MCP, modificar configuración de Codex o Blender, instalar addons, ejecutar código `bpy` privilegiado, abrir puertos aunque sean locales, borrar escenas de prueba o repetir el setup en el sobremesa. La aprobación de esta especificación no autoriza por sí sola esas operaciones futuras.
