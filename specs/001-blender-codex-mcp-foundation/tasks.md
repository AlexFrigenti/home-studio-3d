# Tareas: Blender + Codex + MCP Foundation

Las tareas siguientes registran el estado validado del slice T2. La evidencia operativa queda en los inventarios, decisiones y validaciones enlazados en cada tarea; T2.01 conserva una excepción documental explícita y T2.13 está cerrada. La política de `AGENTS.md` sigue vigente: no convertir cada microtarea en un subagente; usar el agente principal y mantener el proceso proporcional.

Estados: `[ ]` pendiente · `[~]` en curso · `[x]` validada · `[!]` bloqueada.

## T2.01 — Aprobar alcance y contrato

- **Estado:** `[x]` — cerrada el 2026-09-05 **CON EXCEPCIÓN DOCUMENTAL**.
- **Objetivo:** confirmar que `spec.md`, `plan.md` y `tasks.md` reflejan un único objetivo y todos los límites T2.
- **Evidencia esperada:** aprobación del alcance, exclusiones, criterios, riesgos e invariantes.
- **Validación:** revisión cruzada de los tres artefactos y del diff completo.
- **Autorización del usuario:** sí, aprobación de la especificación antes de instalar o configurar.

**Excepción documental T2.01:** la aprobación previa exigida originalmente no quedó registrada a tiempo; no se afirma que esa aprobación existiera. El propietario del proyecto acepta formalmente esta desviación de proceso, confirma retrospectivamente que el alcance, las exclusiones, los riesgos, los criterios y las invariantes de T2 fueron respetados, y autoriza cerrar T2.01 como completada **CON EXCEPCIÓN DOCUMENTAL**.

**Autorización formal del propietario:** “Autorizo la excepción formal de T2.01: acepto que la aprobación previa no quedó registrada, confirmo retrospectivamente que el alcance, exclusiones, riesgos, criterios e invariantes de T2 fueron respetados y autorizo cerrar T2.01 como completada con excepción documental.”

## T2.02 — Inventariar el portátil

- **Estado:** `[x]` — validada el 2026-09-04.
- **Objetivo:** registrar sistema, hardware, rutas y componentes existentes sin cambiar el entorno.
- **Evidencia esperada:** inventario reproducible sin secretos ni rutas privadas innecesarias.
- **Validación:** comprobación de versiones, rutas y ausencia/presencia documentada; `NO APLICA` para componentes no instalados.
- **Autorización del usuario:** no para lectura; sí para modificar o limpiar instalaciones existentes.

## T2.03 — Fijar la distribución de Blender

- **Estado:** `[x]` — validada el 2026-09-04.
- **Objetivo:** confirmar Blender 5.2.1 LTS, fuente aprobada, ruta reproducible y modalidad de distribución para Windows.
- **Evidencia esperada:** comparación del instalador tradicional y ZIP portable oficial; fuente, versión, hash cuando sea posible, criterios aplicados y decisión registrada antes de descargar o instalar.
- **Validación:** revisión de procedencia y compatibilidad con el portátil; se adoptó el ZIP portable por su funcionamiento, ausencia de cambios globales innecesarios y rollback/reproducibilidad.
- **Autorización del usuario:** sí antes de descargar o instalar.

## T2.04 — Instalar y verificar Blender

- **Estado:** `[x]` — validada el 2026-09-05.
- **Objetivo:** instalar Blender 5.2.1 LTS en el portátil usando la modalidad aprobada en T2.03.
- **Evidencia esperada:** Blender inicia, muestra la versión esperada y guarda una escena vacía en el área de pruebas.
- **Validación:** smoke de apertura/guardado y comprobación de no exposición de servicios no solicitados.
- **Autorización del usuario:** sí.

**Resultado T2.04:** Blender inició y reportó `5.2.1 LTS`. Se creó y guardó de forma independiente `blender/scenes/tests/002-blender-empty-save-smoke.blend` con la escena `T2_04_EMPTY_SAVE_SMOKE`: 0 objetos, 0 materiales, unidades `METRIC`, `scale_length = 1.0` y sin assets externos. El archivo se cerró y reabrió correctamente; el contenido persistió y no quedaron cambios pendientes. La comprobación read-only de red observó únicamente loopback y ningún listener o conexión establecida no-loopback atribuible a Blender/MCP.

**Definición factual de “escena vacía” T2.04:** escena independiente sin objetos ni materiales, equivalente al estado mínimo de Blender usado para esta prueba; no se reutilizó `001-foundation-room.blend`.

## T2.05 — Revisar el MCP candidato

- **Estado:** `[x]` — validada el 2026-09-04.
- **Objetivo:** inspeccionar `ahujasid/blender-mcp` y contrastar su integración con la referencia `webita/blender-codex-mcp`, sin aceptar una rama mutable sin pin.
- **Evidencia esperada:** procedencia, licencia, versión/tag/commit exacto aprobado, permisos, transporte y compatibilidad documentados antes de instalar.
- **Validación:** revisión del código y de la configuración; no ejecutar código externo sin inspección; cualquier actualización posterior repite smoke y aceptación.
- **Autorización del usuario:** sí antes de instalar o ejecutar el MCP.

**Resultado T2.05:** se revisó `ahujasid/blender-mcp`, se comparó con `webita/blender-codex-mcp` como referencia y se fijó el commit `5866814479b4e2ca674d8d44969a9a2a78fdc8bb` antes de instalarlo.

## T2.06 — Configurar el MCP solo en localhost

- **Estado:** `[x]` — validada el 2026-09-04.
- **Objetivo:** arrancar el MCP candidato con una frontera de red local.
- **Evidencia esperada:** configuración local, telemetría opcional deshabilitada si procede y puerto identificado.
- **Validación:** handshake real y comprobación de binding solo en `localhost`/loopback; rechazo de LAN/Internet; revisión de la evidencia técnica disponible sobre rutas/permisos, sin declarar sandbox del workspace por la sola política.
- **Autorización del usuario:** sí antes de abrir el servicio local.

**Resultado T2.06:** Blender MCP quedó instalado y operativo con `BLENDER_MCP_SAFE_MODE=1`, `DISABLE_TELEMETRY=true`, `BLENDER_HOST=127.0.0.1` y `BLENDER_PORT=9876`. El handshake y el listener `127.0.0.1:9876` resultaron PASS; no se observó binding fuera de loopback.

## T2.07 — Integrar Codex CLI desde el repo

- **Estado:** `[x]` — validada el 2026-09-04.
- **Objetivo:** permitir que Codex opere desde el workspace y conecte con el MCP local.
- **Evidencia esperada:** configuración reproducible y separada de credenciales/globales.
- **Validación:** Codex obtiene información de la escena y no requiere GPT-6 Astra para funcionar.
- **Autorización del usuario:** sí antes de modificar configuración global o habilitar capacidades privilegiadas.

**Resultado T2.07:** Codex CLI `0.153.1` reconoció el servidor lógico `blender` y completó la comunicación con Blender MCP. `get_scene_info` devolvió la escena `Scene` y los tres objetos iniciales; no se introdujeron secretos ni se modificaron las entradas MCP existentes.

## T2.08 — Ejecutar el smoke técnico

- **Estado:** `[x]` — validada el 2026-09-05.
- **Objetivo:** probar la cadena Codex CLI → MCP local → Blender con una escena vacía/desechable.
- **Evidencia esperada:** primera operación `bpy` de solo lectura (nombre de escena y/o número de objetos), una operación de escena simple y reversible y archivo de smoke guardado.
- **Validación:** la primera operación no usa filesystem, red ni procesos externos; el guardado posterior es explícito dentro del workspace; apertura/guardado, operación reversible, rutas/permisos observables y diff/artefactos revisados. La ausencia de sandbox técnico se registra como limitación, no como PASS.
- **Autorización del usuario:** sí antes de ejecutar `execute_blender_code`/`bpy`.

**Resultado T2.08:** `get_addon_status` permanece como `DEUDA CONOCIDA NO BLOQUEANTE PARA EL SMOKE`: `src/blender_mcp/config.py` no existe en el pin y la tool no se usa para validar telemetría. La cadena live `Codex CLI → MCP local → Blender` resultó PASS; la primera operación mediante MCP fue read-only y consultó escena, objetos y unidades sin filesystem, red ni procesos externos. Se creó el cubo temporal `T2_08_TEMP_REVERSIBLE_CUBE`, se verificó mediante MCP (`MESH`, 8 vértices, 12 aristas, 6 polígonos, ubicación `(0, 0, 0.5)`) y se eliminó completamente antes del guardado. Se guardó de forma independiente `blender/scenes/tests/003-codex-mcp-smoke.blend` con la escena `T2_08_CODEX_MCP_SMOKE`, 0 objetos, 0 mallas, 0 materiales, unidades `METRIC` y `scale_length = 1.0`; el archivo se cerró y reabrió correctamente con Blender `5.2.1 LTS` y sin cambios pendientes. La comprobación read-only de red observó únicamente loopback y ningún listener o conexión establecida no-loopback atribuible a Blender/MCP. No se reutilizó `001-foundation-room.blend`, no se modificó código upstream ni configuración global.

## T2.09 — Crear la habitación sintética mínima

- **Estado:** `[x]` — validada el 2026-09-04
- **Objetivo:** crear suelo, paredes, puerta, ventana, `sofa_proxy`, cámara y luz con el volumen interior `X 0.00..5.00 m`, `Y 0.00..4.00 m`, `Z 0.00..2.50 m`.
- **Evidencia esperada:** escena determinista en `blender/scenes/tests/001-foundation-room.blend` o área equivalente, con `door` de `0.90 × 0.05 × 2.10 m` en `(1.45, -0.025, 1.05) m`, `window` de `0.05 × 1.20 × 1.00 m` en `(5.025, 2.00, 1.50) m` y `sofa_proxy` de `1.80 × 0.80 × 0.90 m` en `(2.50, 2.00, 0.45) m`, rotación cero.
- **Validación:** caras interiores exactas, grosor hacia fuera sin alterar el volumen, escena recreable con las mismas constantes en ambos equipos, abrible/guardable, sin assets externos y sin sobrescribir escenas canónicas.
- **Autorización del usuario:** sí antes de crear y guardar la escena de aceptación.

**Resultado T2.09:** se creó la colección `HS3D_T2_09_FOUNDATION_ROOM` con `floor`, `wall_south`, `wall_north`, `wall_west`, `wall_east`, `door`, `window`, `sofa_proxy`, `HS3D_TEST_CAMERA` y `HS3D_TEST_LIGHT`. La escena usa `METRIC` y `scale_length = 1.0`, y se guardó inicialmente en `blender/scenes/tests/001-foundation-room.blend` con tamaño `103358` bytes; el fixture versionado final tras T2.10 tiene `103445` bytes. Los objetos iniciales `Cube`, `Camera` y `Light` fueron confirmados como la escena por defecto y retirados; no se añadieron materiales ni assets externos. Se obtuvo una captura rápida de viewport sin render; la validación geométrica exhaustiva queda para T2.10 y la inspección visual formal para T2.11.

## T2.10 — Validar dimensiones y transformaciones

- **Estado:** `[x]` — validada el 2026-09-04
- **Objetivo:** comprobar largo, ancho, altura, caras interiores y dimensiones/posiciones sintéticas de puerta, ventana y `sofa_proxy`.
- **Evidencia esperada:** valores numéricos registrados con unidad metros, incluida la posición y tamaño del `sofa_proxy`.
- **Validación:** contraste con `X 0.00..5.00`, `Y 0.00..4.00`, `Z 0.00..2.50`, el contrato de aperturas y las transformaciones documentadas; comprobación de unidades y tolerancias del test.
- **Autorización del usuario:** no adicional si la tarea T2.09 fue aprobada; sí si aparece una discrepancia que requiera cambiar el contrato.

**Resultado T2.10:** se corrigió exclusivamente `sofa_proxy`, recenterizando su geometría respecto al origen y fijando `location = (2.50, 2.00, 0.45)`, sin cambiar el contrato ni los demás objetos. La validación completa pasó con tolerancia `1e-6 m`: caras interiores `5.00 × 4.00 × 2.50 m`, espesores y orientación exterior correctos, `door`, `window` y `sofa_proxy` dentro de contrato, cámara activa y luz correctas, rotaciones cero y escalas aplicadas. El fixture se guardó en `blender/scenes/tests/001-foundation-room.blend`, se reabrió con éxito y todos los valores persistieron; la escena quedó sin cambios pendientes. Seguridad post validada: listener loopback, sin conexiones externas atribuibles, safe mode activo, telemetría deshabilitada e integraciones externas deshabilitadas.

## T2.11 — Obtener e inspeccionar evidencia visual

- **Estado:** `[x]` — validada el 2026-09-04
- **Objetivo:** producir una captura de viewport o render preview y revisar la escena.
- **Evidencia esperada:** captura/render identificable de la habitación sintética.
- **Validación:** inspección visual explícita de suelo, paredes, puerta, ventana, sofá, cámara y luz; sin render final pesado.
- **Autorización del usuario:** sí antes de conservar capturas o iniciar una operación costosa.

**Resultado T2.11:** se conservaron capturas MCP de viewport y un preview Workbench ligero en `renders/previews/001-foundation-room/viewport-overview.png` (`800 × 600`, `297438` bytes). La inspección visual confirmó volumen de habitación coherente, suelo alineado, cuatro paredes, `door` en pared sur, `window` en pared este, `sofa_proxy` dentro del volumen y sin artefactos graves ni objetos residuales. El encuadre elevado y la vista de cámara usados para la evidencia fueron temporales; el fixture se reabrió y quedó limpio, sin cambios persistentes de cámara, render o geometría. No se usaron Cycles, HDRI, assets externos ni texturas externas.

## T2.12 — Documentar la réplica en sobremesa

- **Estado:** `[x]` — validada el 2026-09-05.
- **Objetivo:** documentar versiones, fuentes, rutas variables, orden de arranque y diferencias entre equipos.
- **Evidencia esperada:** procedimiento que otra persona pueda seguir sin secretos ni rutas absolutas personales.
- **Validación:** revisión de reproducibilidad y lista de controles que deben repetirse en el PC.
- **Autorización del usuario:** no para documentar; sí antes de instalar o ejecutar el procedimiento en el sobremesa.

**Resultado T2.12:** la infraestructura de Blender/Codex/MCP se preparó en ambos equipos y el fixture creado en el portátil se validó correctamente en el sobremesa. La validación del sobremesa quedó documentada en `docs/setup/desktop-environment-inventory.md`, que registra Blender 5.2.1 LTS, RTX 3080, el pin exacto de `ahujasid/blender-mcp`, Codex CLI, safe mode, telemetría, loopback, integraciones deshabilitadas, handshake, `get_scene_info`, validación cross-machine, rollback de `approval_mode`, snapshot de configuración, la deuda conocida de `get_addon_status` y el clon activo fuera de OneDrive. La documentación conserva el contrato, el orden de validación y las variables sanitizadas; las rutas personales y los secretos quedan sanitizados o excluidos, y no se afirma equivalencia absoluta de los detalles locales.

## T2.13 — Cierre del T2 y PR

- **Estado:** `[x]` — cerrada el 2026-09-06.
- **Objetivo:** cerrar la fundación con evidencia, riesgos, limitaciones y documentación alineadas.
- **Evidencia esperada:** checklist de aceptación, resultados reales, evidencia visual y diff completo.
- **Validación:** todos los gates aplicables en `PASS`; el resto marcado como `NO APLICA`, `PENDIENTE DE INFRAESTRUCTURA` o `NO EJECUTADO` con explicación.
- **Autorización del usuario:** sí para abrir PR, merge, instalación posterior y cualquier cambio de política.

**Checklist final T2.13 (2026-09-06):**

- Revisión final contra `.quality/QUALITY.md` y `CONTRIBUTING.md`, incluyendo `spec.md`, `plan.md`, `tasks.md`, la documentación de setup/decisions y el diff completo contra `origin/main`: **PASS**; los 13 criterios aplicables tienen evidencia PASS o disposición explícita.
- Criterios aplicables del T2: **PASS** o disposición explícita; T2.01 conserva su excepción documental, T2.04 y T2.08 tienen smoke independiente con guardado/reapertura, y T2.12 documenta la validación del fixture entre portátil y sobremesa sin afirmar equivalencia absoluta de los entornos.
- Diff final: **PASS**; `git diff --check` sin errores.
- Commits: **REALIZADOS**; la foundation y el cierre documental quedan trazables en la historia de esta rama.
- Push: **REALIZADO**; la rama remota coincide con el HEAD local.
- PR #2: **ABIERTA** hacia `main` como parte de este cierre; el merge queda fuera de alcance y requiere autorización explícita.
- CI/merge: **NO APLICA** a este cierre documental mientras no exista una política o check de CI configurado que ejecutar; el merge queda fuera de este paso y requiere checks verdes y autorización explícita.
- Deuda de `get_addon_status`: **ACEPTADA COMO NO BLOQUEANTE** y conservada en la documentación.
- Producción 3D real: **NO INICIADA**; el fixture y los smoke `.blend` son evidencia de foundation.
