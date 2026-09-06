# Decisión 002 — Selección del MCP de Blender

Estado: selección, instalación, integración y validación live completadas para el portátil. El pin está instalado y validado solo en loopback; Codex reconoce el servidor y obtuvo información de escena mediante tools de lectura. El fixture de foundation también se probó entre portátil y sobremesa. La tool `get_addon_status` mantiene una deuda conocida de importación, no bloqueante para la comunicación ni para el smoke, documentada más abajo.

Fecha de revisión: 2026-09-05.

## Decisión adoptada

Adoptar inicialmente el candidato canónico **`ahujasid/blender-mcp`**, fijado al commit exacto:

`5866814479b4e2ca674d8d44969a9a2a78fdc8bb`

- Repositorio canónico: <https://github.com/ahujasid/blender-mcp>.
- Propietario: `ahujasid`.
- Rama por defecto observada: `main`.
- Fecha del commit: 2026-09-02.
- Metadato de paquete en ese commit: `blender-mcp` `1.9.1`.
- Tag/release: no se observó un tag o release oficial utilizable como pin; se usará el SHA completo.
- Licencia: MIT, según el [LICENSE del repositorio](https://github.com/ahujasid/blender-mcp/blob/main/LICENSE).
- Evidencia del pin: [commit exacto](https://github.com/ahujasid/blender-mcp/commit/5866814479b4e2ca674d8d44969a9a2a78fdc8bb) y [metadatos del paquete](https://github.com/ahujasid/blender-mcp/blob/5866814479b4e2ca674d8d44969a9a2a78fdc8bb/pyproject.toml).

El commit elegido es el estado observado de `main` y contiene el cambio de versión a `1.9.1`; su padre inmediato incorpora el modo seguro de validación AST (`BLENDER_MCP_SAFE_MODE`) y sus pruebas. Esto justifica usar el SHA completo y no una rama mutable. Cualquier actualización posterior exige repetir revisión, smoke técnico y aceptación funcional.

La actividad reciente del repositorio es una señal de mantenimiento, no una garantía de compatibilidad: la revisión del historial mostró commits recientes el 1 y 2 de septiembre de 2026. No se considera una certificación de calidad ni sustituye la validación local.

## Resultado de T2.06 — configuración local

La instalación se realizó únicamente desde el SHA autorizado, sin actualizar desde `main` ni desde otra rama mutable.

- `<MCP_HOME>`: `<LOCALAPPDATA>\Programs\HomeStudio3D\MCP\blender-mcp\5866814479b4e2ca674d8d44969a9a2a78fdc8bb`.
- `HEAD` del checkout: `5866814479b4e2ca674d8d44969a9a2a78fdc8bb`.
- Entorno MCP: `<MCP_HOME>\.venv`.
- Python efectivo: CPython `3.11.15`, gestionado por `uv`.
- `uv`: `0.12.4`.
- Dependencias: instaladas con `uv sync --locked`; no se instalaron paquetes en el Python embebido de Blender.

### Addon

Se instaló únicamente `<MCP_HOME>\addon.py`, procedente del mismo `HEAD`, mediante el instalador oficial `blender-mcp install-addon`.

- Destino sanitizado: `<APPDATA>\Blender Foundation\Blender\5.2\scripts\addons\blender_mcp.py`.
- SHA-256 del archivo fuente e instalado: `e9eae227d94875d6b8ed208f11a9628101ef4f579bfc614ab31af296cb88afce`.
- El handshake local confirmó addon protocolo `5`, addon `[1, 6]` y Blender `5.2.1 LTS`.

### Seguridad, integraciones y telemetría

- Servidor MCP iniciado con `BLENDER_HOST=127.0.0.1`, `BLENDER_PORT=9876`, `BLENDER_MCP_SAFE_MODE=1` y `DISABLE_TELEMETRY=true`.
- El consentimiento persistente del addon se estableció en `false` y se leyó de nuevo con resultado `false`.
- Poly Haven, Sketchfab, Poly Pizza, Hyper3D/Rodin y Hunyuan3D devolvieron `enabled=false`.
- No se configuraron API keys ni otras credenciales.
- Safe mode mantiene disponible `execute_blender_code`, pero valida su código antes de cruzar el socket. Bloquea, entre otros, `open`, `eval`/`exec`, imports peligrosos, procesos, red, handlers/timers/drivers, registros persistentes y carga de datablocks externos; permite operaciones Blender explícitamente incluidas por su política, como modelado, materiales, render, guardado e import/export.
- Safe mode no es un sandbox técnico: el addon sigue siendo un proceso Blender con los permisos del usuario y su socket local acepta `execute_code` de cualquier proceso local que alcance el puerto. Esta fase no ejecutó `execute_blender_code`.

Con safe mode activo siguen disponibles las tools de estado/lectura (`get_addon_status`, `get_scene_info`, `get_object_info`), la captura (`get_viewport_screenshot`), el control de telemetría (`disable_telemetry`) y `execute_blender_code` sujeto al validador. Las tools de integraciones externas siguen formando parte de la superficie del servidor, pero sus handlers del addon permanecen inactivos mientras los flags de Poly Haven, Sketchfab, Poly Pizza, Hyper3D/Rodin y Hunyuan3D sean `false`; no se probaron ni se invocaron.

### Listener y smoke del addon

- Blender GUI está ejecutándose con el addon cargado.
- Listener observado: `127.0.0.1:9876`, PID de Blender.
- Conexión observada: `127.0.0.1:9876` ↔ `127.0.0.1:<puerto efímero>`.
- No apareció listener en `0.0.0.0`, una IP LAN ni una interfaz pública.
- El servidor MCP conectó correctamente y obtuvo el handshake del addon. La lectura de escena se validó después mediante `get_scene_info` en T2.07/T2.08.

La variable de entorno y el consentimiento del addon son controles de configuración; el binding se consideró PASS por la dirección observada, no por la palabra `localhost` ni por `AGENTS.md`.

## Compatibilidad y límites conocidos

| Área | Hallazgo | Decisión para Home Studio 3D |
| --- | --- | --- |
| Blender | El README del candidato declara compatibilidad general desde Blender 3.0; no se encontró una matriz específica que certifique Blender 5.2.x. | Blender 5.2.1 LTS queda dentro del mínimo declarado y la compatibilidad operativa quedó validada mediante handshake, lectura de escena y smoke real. |
| Python del servidor MCP | `pyproject.toml` requiere Python `>=3.10`; el README recomienda Python 3.11 gestionado por `uv`. | Usar el Python externo gestionado por `uv`, preferentemente 3.11; no instalar paquetes en Python global ni en el Python embebido de Blender. |
| Python embebido de Blender | El addon se ejecuta dentro de Blender y el servidor MCP es un proceso Python separado. El Python embebido 3.13.13 de Blender no satisface por sí solo la instalación del servidor externo ni debe recibir paquetes. | Mantener separadas ambas runtimes. La compatibilidad del addon con Blender 5.2.1 quedó validada con el smoke; no se infiere solo de `requires-python`. |
| Dependencias | El paquete declara `mcp>=1.9.0,<2` y `httpx>=0.27.0`, además de requerir `uv`/`uvx` en el flujo documentado. | Se instalaron únicamente en el entorno externo aislado del MCP y con lockfile. |
| Codex | La documentación del candidato usa el comando `uvx blender-mcp`; el fork usa una ejecución desde su checkout mediante `uv --directory`. | La ejecución validada usa el checkout externo del SHA elegido con `uv ... run --locked`; no se usa un paquete mutable sin pin. |

Fuentes: [README fijado al commit](https://github.com/ahujasid/blender-mcp/blob/5866814479b4e2ca674d8d44969a9a2a78fdc8bb/README.md) y [pyproject.toml fijado](https://github.com/ahujasid/blender-mcp/blob/5866814479b4e2ca674d8d44969a9a2a78fdc8bb/pyproject.toml).

## Arquitectura y transporte

La cadena objetivo es:

```text
Codex CLI
  └─ MCP por stdin/stdout (proceso hijo)
       └─ blender-mcp fijado al SHA
            └─ TCP JSON hacia el addon de Blender
                 └─ Blender / bpy
                      └─ viewport, render y verificación numérica
```

El servidor se crea con FastMCP y termina llamando a `mcp.run()` sin seleccionar otro transporte, por lo que el lanzamiento desde Codex se trata como MCP sobre stdin/stdout. El servidor MCP actúa como cliente TCP; el addon abre el listener en Blender y usa sockets `AF_INET` con mensajes JSON que contienen `type`, `params` y una respuesta con `status`/resultado. No es un servicio HTTP ni un MCP remoto. Véanse [server.py](https://github.com/ahujasid/blender-mcp/blob/5866814479b4e2ca674d8d44969a9a2a78fdc8bb/src/blender_mcp/server.py) y [addon.py](https://github.com/ahujasid/blender-mcp/blob/5866814479b4e2ca674d8d44969a9a2a78fdc8bb/addon.py).

### Puerto y binding

- Defaults documentados: host `localhost`, puerto `9876`.
- El cliente MCP lee `BLENDER_HOST` y `BLENDER_PORT`.
- El addon construye su servidor con `host='localhost'` y expone en la interfaz el puerto, no un campo de host; el código hace `bind((host, port))`.
- Configuración utilizada y validada: `BLENDER_HOST=127.0.0.1` y `BLENDER_PORT=9876` para el cliente, manteniendo el addon en su default y verificando el listener real.

`localhost` no se considera por sí solo una prueba técnica de loopback. En T2.06 se comprobó el `LocalAddress` real con `Get-NetTCPConnection`: el listener de Blender apareció en `127.0.0.1:9876`, sin binding en `0.0.0.0`, una IP LAN o una interfaz pública.

## Superficie de herramientas y privilegios

La superficie relevante observada en el commit fijado incluye:

- `get_addon_status`, `get_scene_info` y `get_object_info`: lectura de estado de addon, escena y objetos.
- `get_viewport_screenshot`: captura del viewport; el servidor crea y elimina un PNG temporal en el directorio temporal del sistema y puede subirlo para telemetría si existe consentimiento.
- `execute_blender_code`: ejecución de Python arbitrario dentro del proceso de Blender.
- `disable_telemetry`: cambia el consentimiento de telemetría del addon.
- Materiales y texturas: `set_texture`, además de consultas y descargas de recursos Poly Haven.
- Assets externos: búsquedas, previews, descargas e importación desde Poly Haven, Sketchfab y Poly Pizza.
- Generación/importación externa: operaciones para Hyper3D/Rodin y Hunyuan3D, incluyendo consultas de estado, creación/consulta de trabajos e importación de resultados.

Se consideran privilegiadas o de alto impacto:

1. `execute_blender_code`, porque puede cambiar cualquier dato accesible al proceso Blender y, sin modo seguro, ejecutar Python arbitrario.
2. Descargas/importaciones y `set_texture`, porque escriben temporales, cargan datos y alteran la escena o materiales.
3. `get_viewport_screenshot`, por su escritura temporal y posible salida de imagen a telemetría.
4. Las integraciones externas y las operaciones de generación, por su red, credenciales potenciales, coste y efectos de importación.
5. Cualquier uso de `bpy` que guarde, importe, exporte, renderice o elimine datos.

La lista anterior describe capacidades observadas, no autoriza su uso. El primer setup debe mantener deshabilitadas las integraciones de assets/generación y no usar API keys.

## Seguridad

### Garantías técnicas observadas

- El addon escucha mediante un socket TCP local y el servidor MCP se conecta a ese socket; el código no proporciona autenticación fuerte ni aislamiento de usuario.
- `execute_blender_code` envía `execute_code` al addon. Sin safe mode, es una capacidad de Python arbitrario.
- El modo seguro es opt-in mediante `BLENDER_MCP_SAFE_MODE=1`. Valida el código del camino MCP con una lista de permisos y bloqueos AST, pero el propio proyecto declara que no es un sandbox de Blender: el socket del addon acepta `execute_code` de cualquier proceso local. Véase [safe_mode.py](https://github.com/ahujasid/blender-mcp/blob/5866814479b4e2ca674d8d44969a9a2a78fdc8bb/src/blender_mcp/safe_mode.py).
- El addon contiene integraciones que pueden hacer solicitudes HTTP y escribir temporales. También puede ejecutar operaciones Blender de importación/exportación y guardar escenas.
- La ausencia de `subprocess` en el flujo normal del addon no limita lo que podría hacer `bpy`/Python arbitrario cuando safe mode está desactivado.

### Política del proyecto

La política de `AGENTS.md` prohíbe acceder fuera del workspace sin autorización y prohíbe exponer el MCP fuera de loopback. Eso es una restricción operativa, no un sandbox técnico: Blender/Python pueden tener acceso al filesystem, procesos y red que el proceso tenga permitido. La validación debe separar:

- **Comprobable técnicamente:** SHA/checkout del candidato, versión del addon y servidor, `BLENDER_MCP_SAFE_MODE`, dirección local del listener, procesos/puerto, ausencia de claves en configuración, smoke y comportamiento observado.
- **Dependiente de política/permisos:** que ningún agente solicite o ejecute acceso fuera del workspace, que se revisen los scripts antes de ejecutarlos y que no se habiliten integraciones externas. Nunca se marcará “workspace-only” como PASS solo por leer `AGENTS.md`.

### Telemetría

El commit contiene telemetría que puede registrar uso, prompts, código, errores, metadatos de escena y capturas cuando hay consentimiento; el servidor usa HTTP hacia el backend configurado. La propia documentación ofrece dos controles:

1. iniciar el proceso con `DISABLE_TELEMETRY=true`;
2. desmarcar el consentimiento en las preferencias del addon; también existe la tool `disable_telemetry`.

La implementación acepta además `BLENDER_MCP_DISABLE_TELEMETRY` y `MCP_DISABLE_TELEMETRY`. En esta foundation se estableció `DISABLE_TELEMETRY=true` antes de iniciar el servidor y se dejó desmarcado el consentimiento del addon. La verificación se hizo directamente mediante la configuración live y `bpy`, no mediante `get_addon_status`, que conserva la deuda de importación documentada abajo. El mensaje de `disable_telemetry` advierte que el opt-out por consentimiento puede conservar contadores anónimos mínimos; el flag de entorno deshabilita el collector del servidor.

Fuente: [control de telemetría en README](https://github.com/ahujasid/blender-mcp/blob/5866814479b4e2ca674d8d44969a9a2a78fdc8bb/README.md#telemetry-control) y [implementación de telemetría](https://github.com/ahujasid/blender-mcp/blob/5866814479b4e2ca674d8d44969a9a2a78fdc8bb/src/blender_mcp/telemetry.py).

## Comparación con `webita/blender-codex-mcp`

La referencia secundaria es [webita/blender-codex-mcp](https://github.com/webita/blender-codex-mcp). Su `main` observado tiene como commit más reciente visible `7b959c51fc4c166dc8b7ff4e85f989fa726f655c` (2026-04-26) y no aporta una ventaja suficiente para sustituir al candidato canónico.

| Aspecto | `ahujasid/blender-mcp` elegido | `webita/blender-codex-mcp` |
| --- | --- | --- |
| Configuración Codex | README usa `uvx blender-mcp`; para este proyecto se adaptará a checkout/lockfile fijado. | Usa `[mcp_servers.blender]`, `uv --directory <checkout> run blender-codex-mcp` y variables en `~/.codex/config.toml`. |
| Addon | Instalación documentada mediante `uvx blender-mcp install-addon`; UI actual “MCP for Blender”. | Instalación manual de `addon.py`; UI “Blender Codex MCP”. |
| Transporte | MCP por stdin/stdout y socket TCP JSON hacia Blender, `localhost:9876` por defecto. | Mismo patrón local y mismo puerto por defecto. |
| Capacidades útiles | Inspección, screenshot, Python, materiales/texturas y varias integraciones externas; incluye safe mode opt-in. | Añade en su README `blender_health_check`, `sync_camera_to_viewport` y `export_glb`, además de integraciones opcionales. |
| Telemetría | `DISABLE_TELEMETRY=true`, preferencia del addon y tool de opt-out; el commit incluye safe mode. | Documenta `DISABLE_TELEMETRY=true`, pero el fork no ofrece una ventaja técnica clara frente al upstream. |
| Riesgo de mantenimiento | Upstream más activo y pin directo a su historial canónico. | Fork pequeño, con scaffold de plugin experimental y divergencia que habría que mantener. |

La comparación se limita a configuración, transporte, secuencia y capacidades declaradas; no se adopta ningún código del fork ni se instala como dependencia.

## Estrategia de instalación ejecutada para T2.06

La estrategia se ejecutó después de fijar el pin en T2.05 y con la autorización correspondiente.

1. **Servidor externo.** Crear `<MCP_HOME>` fuera de `<REPO_ROOT>` y obtener un checkout/artefacto del commit exacto `586...`. Ejecutar con la ruta absoluta de `uv` y `--locked` desde ese checkout, o validar antes un `uvx --from` que incluya el SHA. No usar un paquete mutable de PyPI como pin final.
2. **Addon.** Desde el mismo checkout fijado, usar el instalador oficial documentado (`install-addon`) o instalar manualmente el `addon.py` equivalente del mismo SHA en la carpeta de addons de usuario de Blender. El addon queda fuera del repositorio Home Studio 3D; no se copiará a `blender/` del proyecto.
3. **Codex.** Añadir únicamente en la configuración local de Codex, y solo con autorización, una entrada `[mcp_servers.blender]` que invoque el servidor fijado con rutas absolutas. No versionar esta configuración ni secretos. No usar un plugin de Codex del fork.
4. **Variables iniciales.** Usar `BLENDER_HOST=127.0.0.1`, `BLENDER_PORT=9876`, `BLENDER_MCP_SAFE_MODE=1` y `DISABLE_TELEMETRY=true`. Mantener desactivadas Poly Haven, Sketchfab, Poly Pizza, Hyper3D y Hunyuan3D; no introducir credenciales.
5. **Verificación.** Con Blender GUI y el addon activo, comprobar proceso, listener, `LocalAddress`, handshake/versiones, `get_scene_info`, una operación `bpy` inocua y reversible, screenshot y verificación numérica. Ejecutar `Get-NetTCPConnection -State Listen`/`netstat -ano` y rechazar cualquier binding no-loopback. El modo seguro y la política del agente se validan por separado.
6. **Segundo equipo.** Repetir el mismo SHA, lockfile, versión de Blender, convención `<BLENDER_HOME>`/`<MCP_HOME>` y checklist, sustituyendo solo rutas locales expresadas mediante variables. El fixture se probó entre portátil y sobremesa; no se registran rutas personales adicionales del sobremesa.

## Rollback

El rollback completo propuesto es:

1. detener la conexión del addon y cerrar Blender;
2. verificar la procedencia antes de quitar el archivo del addon; restaurar un `.bak` solo si fue creado por esta instalación y su origen es inequívoco;
3. retirar únicamente la entrada `[mcp_servers.blender]` de la configuración local de Codex, sin alterar otros servidores;
4. eliminar el checkout de `<MCP_HOME>` y cualquier entorno/cache temporal aislado creado para este pin, solo después de confirmar sus rutas;
5. retirar configuraciones/archivos de telemetría creados por esta prueba únicamente si se identifican con seguridad;
6. comprobar que Blender ya no está ejecutándose, que el puerto 9876 no tiene listener y que no quedan procesos MCP;
7. conservar intactos el repositorio, las medidas, las escenas canónicas y cualquier backup no atribuido inequívocamente a esta prueba.

No se usará rollback destructivo si la procedencia de un archivo o configuración no es segura.

## Resultado de T2.07 — integración Codex CLI

- Se añadió únicamente el servidor lógico `blender` a `<USERPROFILE>\.codex\config.toml` mediante `codex mcp add`; no se alteraron modelo, autenticación, política persistente de aprobación, sandbox, ni las entradas existentes.
- Método de lanzamiento resumido: `<USER_LOCAL_BIN>\uv.exe run --locked --directory <MCP_HOME> blender-mcp`, desde el checkout fijado al commit `5866814479b4e2ca674d8d44969a9a2a78fdc8bb`.
- Variables fijadas en la entrada: `BLENDER_MCP_SAFE_MODE=1`, `DISABLE_TELEMETRY=true`, `BLENDER_HOST=127.0.0.1` y `BLENDER_PORT=9876`. No hay credenciales ni integraciones externas habilitadas.
- La copia de seguridad reversible quedó fuera del repositorio en `<USERPROFILE>\\.codex\\backups\\home-studio-3d-t2-07-config-20260904-192701.toml.bak`; se verificó que coincidía con la configuración previa.
- `codex mcp list` terminó correctamente y reconoció `blender`. La comparación TOML demostró que `node_repl` y `unity` permanecen idénticos a la copia previa; la entrada nueva es la única adición.

### Smoke desde Codex

- Codex CLI `0.153.1`, lanzado mediante el `.cmd` efectivo, inició el proceso MCP configurado y completó la comunicación MCP con Blender. La sesión de prueba fue efímera y no dejó proceso MCP huérfano.
- `get_scene_info`: **PASS**. Devolvió la escena `Scene`, tres objetos (`Cube`, `Light`, `Camera`) y dos materiales; no modificó la escena ni el repositorio.
- `get_addon_status`: **LIMITACIÓN**. Respondió `No module named 'blender_mcp.config'`; no se usó este error para declarar un PASS. La conectividad y la lectura de escena se validaron por separado.
- Listener observado después de la sesión: únicamente `127.0.0.1:9876`, asociado a Blender. No apareció binding en `0.0.0.0`, LAN ni interfaz pública.
- No se ejecutó `execute_blender_code`, no se usaron tools de escritura y no se creó ni modificó ningún `.blend`.

## Resultado de T2.08 — smoke técnico y validación live

Fecha de ejecución inicial: 2026-09-04. Revalidación del guardado independiente: 2026-09-05.

### Precheck

- Repositorio: `home-studio-3d`; rama: `spec/001-blender-codex-mcp-foundation`; `HEAD`: `e32733970fd03828f86498af678cc3a0b4cf24c4`.
- El working tree contenía los cambios documentales previos y los artefactos de T2.08; esta tarea no modificó código upstream, addon, configuración de Codex ni escenas persistentes.
- Blender portable 5.2.1 LTS quedó arrancado y el proceso live confirmó la versión `5.2.1 LTS`; el pin es `5866814479b4e2ca674d8d44969a9a2a78fdc8bb` y el paquete `1.9.1`.
- La configuración local de Codex existe y conserva la entrada lógica `blender`; las entradas `node_repl` y `unity` no se tocaron. No se registran rutas personales ni valores sensibles.
- La configuración live mantuvo `BLENDER_MCP_SAFE_MODE="1"`, `DISABLE_TELEMETRY="true"`, `BLENDER_HOST="127.0.0.1"` y `BLENDER_PORT="9876"`, con integraciones externas deshabilitadas. Durante T2.08 no se modificó la configuración.
- En el precheck de T2.08 no había una escena canónica abierta. `get_scene_info` confirmó entonces la escena inicial `Scene` con exactamente `Cube`, `Camera` y `Light`; el fixture se creó posteriormente en T2.09.

### `get_addon_status` y diagnóstico

- La reproducción registrada de `get_addon_status` devolvió inicialmente `Error checking addon status: Could not connect to Blender. Make sure the Blender addon is running.` porque Blender no estaba activo en ese momento; no se volvió a usar como prueba de telemetría.
- El resultado histórico de T2.07 fue `No module named 'blender_mcp.config'`. Se mantiene documentado sin repetir la tool.
- Causa concreta: el commit fijado no contiene `src/blender_mcp/config.py` ni la ruta aparece en su árbol Git; `src/blender_mcp/telemetry.py` hace `from .config import telemetry_config` al inicializar `TelemetryCollector`, y `get_addon_status` invoca `get_telemetry().check_user_consent()` al construir la respuesta. Es un bug de empaquetado/import del pin, no una incompatibilidad de Blender, un cambio de configuración ni un fallo de protocolo.
- Clasificación: **DEUDA CONOCIDA NO BLOQUEANTE PARA EL SMOKE**. Limita la consulta de telemetría de `get_addon_status`, pero no afecta a conexión MCP, handshake, `get_scene_info`, socket Blender, safe mode u operaciones `bpy`. No se creó `config.py`, no se parcheó upstream, no se cambió el commit y no se reinstaló nada.

### Lectura, escritura y verificación

- `get_scene_info`: **PASS**, escena `Scene`, exactamente `Cube`, `Light` y `Camera`, 3 objetos.
- La comunicación live `Codex → Blender MCP → Blender` quedó validada end-to-end; la lectura de escena no modificó Blender, el repositorio ni ningún archivo `.blend`.
- Primera llamada `execute_blender_code` read-only: **PASS**. Devolvió Blender `5.2.1 LTS`, escena `Scene`, 3 objetos, `METRIC`, `scale_length=1.0`; sin filesystem, red, subprocess, escritura, preferencias, render o guardado.
- Creación controlada: **PASS**. `HS3D_T2_08_SMOKE_CUBE`, tipo `MESH` con topología de cubo, cero materiales.
- Verificación independiente: **PASS**, tolerancia `1e-6 m`; `location=(0,0,0.5)`, `dimensions=(1,1,1)`, `rotation=(0,0,0)`, `scale=(1,1,1)`.
- Captura de viewport: **PASS**, captura de 800 px con el cubo temporal seleccionado; sin Cycles ni cambios persistentes.
- Cleanup: **PASS**. Eliminado exclusivamente el objeto temporal.

### Post-smoke y red

- Listener: **PASS**, únicamente `127.0.0.1:9876`.
- Red antes y después: **PASS**, cero conexiones TCP establecidas no-loopback atribuibles a MCP/Blender; solo se observaron conexiones loopback internas. No se hizo escaneo de red.
- Safe mode: **PASS configurado**, `BLENDER_MCP_SAFE_MODE="1"`.
- Telemetría: **PASS**, `DISABLE_TELEMETRY="true"` y consentimiento del addon `False`, verificado directamente mediante `bpy`; `get_addon_status` no se utilizó para esta conclusión.
- Integraciones: **PASS**, Poly Haven, Sketchfab, Poly Pizza, Hyper3D y Hunyuan3D `False`, verificado directamente mediante `bpy`.
- Procesos MCP: árbol esperado activo (`uv` → `blender-mcp` → Python), sin procesos MCP huérfanos inesperados observados.
- En la ejecución inicial de T2.08 el estado final conservaba exactamente `Cube`, `Light` y `Camera` y no se creó `.blend`; el fixture se creó y validó posteriormente en T2.09/T2.10. La revalidación del guardado independiente se documenta a continuación y no altera el fixture.

### Revalidación T2.08 — guardado independiente

- La cadena live `Codex CLI → MCP local → Blender` resultó PASS en el PORTÁTIL. La primera operación mediante MCP fue read-only y no realizó llamadas de filesystem, red ni procesos externos.
- Se creó `T2_08_TEMP_REVERSIBLE_CUBE`, se verificó como `MESH` con 8 vértices, 12 aristas, 6 polígonos, ubicación `(0, 0, 0.5)`, rotación cero y escala `(1, 1, 1)`, y se eliminó completamente antes de guardar.
- Se guardó `blender/scenes/tests/003-codex-mcp-smoke.blend` (`96929` bytes; SHA-256 `E55AE5C1DEA4C814D6FA3286F6232D2056FAED58EBD44286B4352912F2D995B4`). La escena `T2_08_CODEX_MCP_SMOKE` reabrió correctamente con Blender `5.2.1 LTS`, 0 objetos, 0 mallas, 0 materiales, unidades `METRIC`, `scale_length = 1.0` y sin cambios pendientes.
- La comprobación read-only de red observó únicamente listeners loopback en `127.0.0.1:9876`, cero listeners no-loopback en ese puerto y cero conexiones establecidas no-loopback atribuibles a Blender/MCP. No se reutilizó `001-foundation-room.blend`, no se modificó código upstream ni configuración global.

### Rollback de la integración Codex

1. Cerrar la sesión Codex y el proceso MCP asociado.
2. Restaurar la copia de seguridad o retirar únicamente la sección `[mcp_servers.blender]`.
3. Comprobar que `node_repl` y `unity` siguen intactos.
4. Verificar que no queda proceso MCP huérfano ni listener MCP adicional; conservar Blender y el addon sin cambios.
5. Mantener el backup hasta confirmar la reversión y no eliminar archivos fuera de las rutas identificadas de esta fase.

## Riesgos y estado de cierre

Riesgos principales: Python arbitrario y acceso potencial a filesystem/procesos/red; falta de sandbox técnico; binding no-loopback por resolución de `localhost`; integraciones externas y credenciales; cambios upstream; ausencia de una matriz upstream específica para Blender 5.2.1, aunque la compatibilidad operativa local quedó validada; instalaciones no reproducibles; rutas diferentes entre equipos; corrupción de escenas; y coste de generación/render/VRAM.

No hay bloqueo para mantener este candidato y este pin como decisión adoptada. La foundation queda validada para el flujo local y el fixture sintético. Permanece la deuda conocida de `get_addon_status`: el pin no contiene `src/blender_mcp/config.py`, por lo que la consulta de estado/telemetría falla por importación. Esta deuda no bloquea el handshake, `get_scene_info`, el listener loopback ni la validación del fixture.

Las futuras operaciones de producción, cualquier actualización de Blender o del pin, y cualquier cambio de configuración deberán repetir los gates que correspondan; no se consideran autorizadas por esta documentación.
