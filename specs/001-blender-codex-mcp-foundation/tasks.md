# Tareas: Blender + Codex + MCP Foundation

Todas las tareas están pendientes porque este slice documenta primero el cambio T2. Cada tarea debe ejecutarse en orden cuando exista autorización para comenzar la instalación. La política de `AGENTS.md` sigue vigente: no convertir cada microtarea en un subagente; usar el agente principal y mantener el proceso proporcional.

Estados: `[ ]` pendiente · `[~]` en curso · `[x]` validada · `[!]` bloqueada.

## T2.01 — Aprobar alcance y contrato

- **Estado:** `[ ]`
- **Objetivo:** confirmar que `spec.md`, `plan.md` y `tasks.md` reflejan un único objetivo y todos los límites T2.
- **Evidencia esperada:** aprobación del alcance, exclusiones, criterios, riesgos e invariantes.
- **Validación:** revisión cruzada de los tres artefactos y del diff completo.
- **Autorización del usuario:** sí, aprobación de la especificación antes de instalar o configurar.

## T2.02 — Inventariar el portátil

- **Estado:** `[ ]`
- **Objetivo:** registrar sistema, hardware, rutas y componentes existentes sin cambiar el entorno.
- **Evidencia esperada:** inventario reproducible sin secretos ni rutas privadas innecesarias.
- **Validación:** comprobación de versiones, rutas y ausencia/presencia documentada; `NO APLICA` para componentes no instalados.
- **Autorización del usuario:** no para lectura; sí para modificar o limpiar instalaciones existentes.

## T2.03 — Fijar la distribución de Blender

- **Estado:** `[ ]`
- **Objetivo:** confirmar Blender 5.2 LTS, fuente aprobada, versión y ruta reproducible.
- **Evidencia esperada:** fuente, versión, hash cuando sea posible y decisión de ruta.
- **Validación:** revisión de procedencia y compatibilidad con el portátil.
- **Autorización del usuario:** sí antes de descargar o instalar.

## T2.04 — Instalar y verificar Blender

- **Estado:** `[ ]`
- **Objetivo:** instalar Blender 5.2 LTS en el portátil.
- **Evidencia esperada:** Blender inicia, muestra la versión esperada y guarda una escena vacía en el área de pruebas.
- **Validación:** smoke de apertura/guardado y comprobación de no exposición de servicios no solicitados.
- **Autorización del usuario:** sí.

## T2.05 — Revisar el MCP candidato

- **Estado:** `[ ]`
- **Objetivo:** inspeccionar `ahujasid/blender-mcp` y contrastar su integración con la referencia `webita/blender-codex-mcp`.
- **Evidencia esperada:** procedencia, licencia, versión/commit, permisos, transporte y compatibilidad documentados.
- **Validación:** revisión del código y de la configuración; no ejecutar código externo sin inspección.
- **Autorización del usuario:** sí antes de instalar o ejecutar el MCP.

## T2.06 — Configurar el MCP solo en localhost

- **Estado:** `[ ]`
- **Objetivo:** arrancar el MCP candidato con una frontera de red local.
- **Evidencia esperada:** configuración local, telemetría opcional deshabilitada si procede y puerto identificado.
- **Validación:** handshake real y comprobación de binding solo en `localhost`/loopback; rechazo de LAN/Internet.
- **Autorización del usuario:** sí antes de abrir el servicio local.

## T2.07 — Integrar Codex CLI desde el repo

- **Estado:** `[ ]`
- **Objetivo:** permitir que Codex opere desde el workspace y conecte con el MCP local.
- **Evidencia esperada:** configuración reproducible y separada de credenciales/globales.
- **Validación:** Codex obtiene información de la escena y no requiere GPT-6 Astra para funcionar.
- **Autorización del usuario:** sí antes de modificar configuración global o habilitar capacidades privilegiadas.

## T2.08 — Ejecutar el smoke técnico

- **Estado:** `[ ]`
- **Objetivo:** probar la cadena Codex CLI → MCP local → Blender con una escena vacía/desechable.
- **Evidencia esperada:** información de escena, una operación `bpy` simple y archivo de smoke guardado.
- **Validación:** apertura/guardado, operación reversible, rutas dentro del workspace y diff/artefactos revisados.
- **Autorización del usuario:** sí antes de ejecutar `execute_blender_code`/`bpy`.

## T2.09 — Crear la habitación sintética mínima

- **Estado:** `[ ]`
- **Objetivo:** crear suelo, paredes, puerta, ventana, `sofa_proxy`, cámara y luz con `5.00 × 4.00 × 2.50 m`.
- **Evidencia esperada:** escena en `blender/scenes/tests/001-foundation-room.blend` o área equivalente.
- **Validación:** escena abrible/guardable, sin assets externos y sin sobrescribir escenas canónicas.
- **Autorización del usuario:** sí antes de crear y guardar la escena de aceptación.

## T2.10 — Validar dimensiones y transformaciones

- **Estado:** `[ ]`
- **Objetivo:** comprobar largo, ancho, altura, posición y tamaño del `sofa_proxy`.
- **Evidencia esperada:** valores numéricos registrados con unidad metros.
- **Validación:** contraste con los criterios de aceptación y comprobación de unidades/transformaciones.
- **Autorización del usuario:** no adicional si la tarea T2.09 fue aprobada; sí si aparece una discrepancia que requiera cambiar el contrato.

## T2.11 — Obtener e inspeccionar evidencia visual

- **Estado:** `[ ]`
- **Objetivo:** producir una captura de viewport o render preview y revisar la escena.
- **Evidencia esperada:** captura/render identificable de la habitación sintética.
- **Validación:** inspección visual explícita de suelo, paredes, puerta, ventana, sofá, cámara y luz; sin render final pesado.
- **Autorización del usuario:** sí antes de conservar capturas o iniciar una operación costosa.

## T2.12 — Documentar la réplica en sobremesa

- **Estado:** `[ ]`
- **Objetivo:** documentar versiones, fuentes, rutas variables, orden de arranque y diferencias entre equipos.
- **Evidencia esperada:** procedimiento que otra persona pueda seguir sin secretos ni rutas absolutas personales.
- **Validación:** revisión de reproducibilidad y lista de controles que deben repetirse en el PC.
- **Autorización del usuario:** no para documentar; sí antes de instalar o ejecutar el procedimiento en el sobremesa.

## T2.13 — Cierre del T2 y PR

- **Estado:** `[ ]`
- **Objetivo:** cerrar la fundación con evidencia, riesgos, limitaciones y documentación alineadas.
- **Evidencia esperada:** checklist de aceptación, resultados reales, evidencia visual y diff completo.
- **Validación:** todos los gates aplicables en `PASS`; el resto marcado como `NO APLICA`, `PENDIENTE DE INFRAESTRUCTURA` o `NO EJECUTADO` con explicación.
- **Autorización del usuario:** sí para abrir PR, merge, instalación posterior y cualquier cambio de política.
