# Inventario del entorno del sobremesa

Fecha del inventario: 2026-09-05.

Esta actualización corresponde únicamente a T2.12. Se desplegaron Blender
portable y la réplica local del MCP fijado, y se ejecutaron las validaciones
autorizadas. La reanudación mínima POST-CONFIG confirmó la entrada del MCP en
Codex, creó un snapshot externo del `config.toml` actual y pasó `codex mcp list`.
La validación runtime inició Blender 5.2.1 LTS, confirmó el listener loopback,
completó el handshake y obtuvo `get_scene_info` de la escena inicial.
Después se ejecutó `execute_blender_code` únicamente para abrir y leer el
fixture cross-machine, sin escribir ni guardar datos; no se creó ni guardó
ningún `.blend` ni startup file. Tras detectar drift de aprobación MCP, se
aplicó únicamente el rollback mínimo documentado más abajo; no se
configuró Git LFS, no se cambió PATH ni se instaló ningún addon distinto del
addon fijado. Se persistió únicamente la preferencia local de seguridad del
addon (`telemetry_consent=false`). Las rutas se expresan con
variables sanitizadas:
`<REPO_ROOT>`, `<USERPROFILE>`, `<APPDATA>`, `<LOCALAPPDATA>`,
`<PROGRAMFILES>`, `<PROGRAMFILES_X86>`, `<CODEX_BIN>`, `<BLENDER_HOME>`,
`<MCP_HOME>` y `<UV_PACKAGE>`.

## Precheck Git

| Comprobación | Resultado |
| --- | --- |
| Raíz | `<REPO_ROOT>` |
| `origin` | `https://github.com/AlexFrigenti/home-studio-3d.git` |
| Rama actual | `spec/001-blender-codex-mcp-foundation` |
| HEAD | `1ee128bc4147f5f48afd3101f5ca7a2ebeb68f85` |
| `origin/main` | `b7880295085e70418f616a125e732df358aeb7f5` |
| `origin/spec/001-blender-codex-mcp-foundation` | `1ee128bc4147f5f48afd3101f5ca7a2ebeb68f85` |
| Upstream | `origin/spec/001-blender-codex-mcp-foundation` |
| Ahead/behind frente al upstream | `0/0` |
| Working tree | solo `docs/setup/desktop-environment-inventory.md` sin seguimiento |

## Clasificación resumida

| Componente | Estado read-only | Resultado |
| --- | --- | --- |
| Windows, CPU, RAM y GPU | DISPONIBLE | Windows 11 Pro x64; Ryzen 7 5800X; RTX 3080 con VRAM fiable observada. |
| Unidad del repo | DISPONIBLE | NTFS sobre SSD NVMe; el clon activo está en `<REPO_ROOT>` fuera de OneDrive; quedan aproximadamente 195 GiB libres. |
| Blender | DISPONIBLE | Portable Blender 5.2.1 LTS desplegado bajo `<BLENDER_HOME>`; validación binaria y primer arranque GUI PASS; no se añadió a PATH. |
| Python del sistema | DISPONIBLE | Python 3.14.7; `py` no está disponible. |
| Python embebido de Blender | DISPONIBLE | Python 3.13.13 AMD64 incluido en el portable; no se instalaron paquetes. |
| Python MCP 3.11.x gestionado por uv | DISPONIBLE | Python 3.11.15 gestionado por uv dentro del `.venv` bloqueado del checkout MCP; separado del global y del embebido de Blender. |
| `uv` / `uvx` | DISPONIBLE | `0.12.5` en ambos comandos. |
| Codex CLI | DISPONIBLE | `codex.cmd` confirma `codex-cli 0.153.3`. |
| Configuración Codex | PRESENTE, ENTRADA BLENDER VALIDADA | Existe `config.toml`; `node_repl` y `blender` están presentes y `codex mcp list` termina correctamente. |
| Blender MCP | DISPONIBLE, REGISTRADO EN CODEX | Checkout fijado, dependencias bloqueadas y addon exacto; Blender, handshake y `get_scene_info` validados. |
| Git | DISPONIBLE | Git `2.55.0.windows.3`. |
| Git LFS | DISPONIBLE, SIN CONFIGURAR | Git LFS `3.7.1`; `.gitattributes` no existe. |
| Herramientas de listeners | DISPONIBLE | `Get-NetTCPConnection` y `netstat.exe` están disponibles. |

## Windows y hardware

- Edición: Windows 11 Pro.
- Versión/build: `10.0.26200`, build `26200`.
- Arquitectura: 64 bits.
- CPU: AMD Ryzen 7 5800X 8-Core Processor; 8 núcleos y 16 procesadores lógicos.
- RAM total: aproximadamente `31.93 GiB`.
- GPU: NVIDIA GeForce RTX 3080.
- VRAM: `10240 MiB`, obtenida mediante `nvidia-smi`, la fuente fiable usada para esta cifra.

No se recopilaron números de serie, UUID, claves, MAC ni identificadores de
hardware innecesarios.

## Repositorio, almacenamiento y permisos

- Ruta sanitizada del clon activo: `<REPO_ROOT>`.
- Unidad: `C:`, filesystem NTFS, SSD con bus NVMe.
- Capacidad aproximada: `930.0 GiB`; libres aproximadamente `195.0 GiB`.
- El clon activo está fuera de OneDrive. La copia antigua bajo
  `<USERPROFILE>\OneDrive\...` no se usa ni modifica en esta réplica.
- Se observaron clientes de sincronización activos en el equipo, pero no
  constituyen un bloqueo operativo para `<REPO_ROOT>`.
- La ACL de la raíz contiene reglas Allow de `Modify` y `FullControl`, además
  de reglas heredadas de lectura/ejecución. En `.git` también aparecen reglas
  Deny explícitas relacionadas con escritura/borrado junto a permisos Allow;
  por ello no se infiere el permiso efectivo únicamente a partir de una regla
  aislada.
- No se creó ni modificó ningún `.blend` durante esta réplica. Las operaciones
  Git autorizadas se verifican al cierre con el working tree esperado.

### Evaluación específica de OneDrive: NO BLOQUEANTE

El riesgo previo aplicaba a la copia antigua sincronizada. El clon activo está
en `<REPO_ROOT>`, fuera de OneDrive, y no presenta ese bloqueo operativo para
esta réplica. La copia antigua no debe reutilizarse ni modificarse. Se mantiene
la práctica normal de copias de seguridad para escenas y otros binarios.

## Blender

- Distribución: Blender 5.2.1 LTS Portable ZIP para Windows x64.
- `<BLENDER_HOME>`: `<LOCALAPPDATA>\Programs\Blender\5.2.1`.
- El ZIP se extrajo únicamente después de verificar nombre, tamaño, hash local
  y coincidencia con el checksum oficial; despliegue: **PASS**.
- Ejecutable: `<BLENDER_HOME>\blender-5.2.1-windows-x64\blender.exe`.
- `--version` mediante ruta absoluta: exit code `0`; `Blender 5.2.1 LTS`,
  plataforma Windows y link flags `/MACHINE:X64`.
- No se añadió Blender a PATH, no se crearon asociaciones `.blend` ni se
  modificó el registro. El único addon instalado en la fase MCP se documenta
  en su sección específica y corresponde exactamente al commit fijado.

### Descarga y verificación

- Artefacto: `blender-5.2.1-windows-x64.zip`.
- URL efectiva del ZIP: `https://download.blender.org/release/Blender5.2/blender-5.2.1-windows-x64.zip`.
- Checksum oficial: `https://download.blender.org/release/Blender5.2/blender-5.2.1.sha256`.
- Tamaño esperado y local: `404851964` bytes.
- SHA-256 esperado y local: `0e631dad7d0cad6d5d18abdd2e2550f6c0213215334eda00ddbd3d22b96ecb2c`.
- Entrada oficial coincidente: `0e631dad7d0cad6d5d18abdd2e2550f6c0213215334eda00ddbd3d22b96ecb2c  blender-5.2.1-windows-x64.zip`.
- Resultado de nombre, tamaño, hash local y comparación oficial: **PASS**.
- Ubicación temporal sanitizada del artefacto: `<T2_12_DOWNLOAD_DIR>\blender-5.2.1-windows-x64.zip`.

### Smoke y primer arranque GUI

- Smoke headless: **PASS**, con `--background --factory-startup
  --disable-autoexec`, sin guardar `.blend`:
  `bpy.app.version_string=5.2.1 LTS`, escena activa `Scene`, unidades
  `METRIC` y `scale_length=1.0`.
- Primer arranque GUI controlado: **PASS**. Título observado:
  `(Unsaved) - Blender 5.2.1 LTS`; ventana visible con handle no nulo,
  aplicación respondía y la interfaz principal con viewport estuvo disponible.
- No aparecieron diálogos iniciales ni títulos de ventana secundarios que
  requirieran decisiones persistentes. En ese primer arranque de Blender no se
  interactuó con preferencias, escena ni startup file; cierre limpio confirmado.
- Los logs stdout/stderr del arranque GUI no mostraron errores de startup,
  GPU o driver. No se obtuvo captura pixel-level porque el helper CUA no expuso
  APIs nativas de aplicaciones; la evidencia GUI es de proceso/ventana y no una
  inspección visual independiente.

### Rollback

- Cerrar Blender y retirar únicamente `<BLENDER_HOME>` para deshacer el
  despliegue portable.
- Eliminar, si procede, únicamente el directorio temporal sanitizado
  `<T2_12_DOWNLOAD_DIR>` después de conservar la evidencia de hash; no tocar el
  repo, sus escenas ni las medidas.

## Python

- `python --version`: `Python 3.14.7`.
- Python embebido de Blender: `3.13.13 (MSC v.1944 64 bit (AMD64))`; consulta
  `python.exe --version` y `sys.executable`: **PASS**.
- Ruta sanitizada del runtime embebido: `<BLENDER_HOME>\blender-5.2.1-windows-x64\5.2\python\bin\python.exe`.
- No se instalaron paquetes en el Python embebido.
- Resolución efectiva de PowerShell, en este orden:
  1. `<USERPROFILE>\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\python.exe`.
  2. `<USERPROFILE>\AppData\Local\Microsoft\WindowsApps\python.exe`.
- `where.exe python`: no devuelve una ruta en este entorno.
- `py --version`: no disponible; `where.exe py` tampoco encuentra el comando.
- No se modificó Python, PATH ni la ExecutionPolicy.

La versión global 3.14.7 no sustituye al runtime objetivo del servidor MCP:
la réplica usa un Python externo 3.11.15 aislado y gestionado por uv,
separado del Python embebido de Blender.

## Cycles y GPU

- GPU detectada por Cycles: `NVIDIA GeForce RTX 3080`.
- CUDA: disponible; backend consultado en un proceso headless efímero.
- OptiX: disponible; backend consultado en un proceso headless efímero.
- No se hizo benchmark ni render pesado; esta consulta no cambió preferencias.
- Warning observado durante la consulta: `HIPEW initialization failed: Error
  opening HIP dynamic library`. Se considera no bloqueante para CUDA/OptiX y
  no se modificó ni instaló nada para resolverlo.

## uv / uvx

- `uv --version`: `uv 0.12.5 (210d1f678 2026-08-14 x86_64-pc-windows-msvc)`.
- `uvx --version`: `uvx 0.12.5 (210d1f678 2026-08-14 x86_64-pc-windows-msvc)`.
- Rutas sanitizadas: `<USERPROFILE>\AppData\Local\Microsoft\WinGet\Packages\<UV_PACKAGE>\uv.exe` y `uvx.exe`.
- Python MCP gestionado: `3.11.15`, instalado mediante uv sin modificar el
  Python global 3.14.7 ni el Python embebido de Blender.
- El checkout MCP usa un entorno `.venv` reproducible creado con
  `uv sync --locked --python 3.11.15`; la sincronización terminó con exit code
  `0` y sin cambios en el lockfile ni en el árbol Git.

## Codex CLI y configuración

- Versión efectiva: `codex-cli 0.153.3` mediante `codex.cmd --version`.
- Launcher efectivo sanitizado: `<CODEX_BIN>\codex.cmd`.
- También existe un launcher PowerShell `<CODEX_BIN>\codex.ps1`, pero su
  ejecución está bloqueada por la ExecutionPolicy vigente; no se modificó.
- Configuración existente: `<USERPROFILE>\.codex\config.toml`.
- Se inspeccionaron solo los encabezados y las variables esperadas, sin mostrar
  tokens, claves ni secretos. Se observaron:
  - `[mcp_servers.node_repl]`
  - `[mcp_servers.node_repl.env]`
  - `[mcp_servers.blender]`
  - `[mcp_servers.blender.env]`
- Las variables de `blender` son `BLENDER_MCP_SAFE_MODE=1`,
  `DISABLE_TELEMETRY=true`, `BLENDER_HOST=127.0.0.1` y `BLENDER_PORT=9876`.
- `codex mcp list`: **PASS**, exit code `0`; reconoció `node_repl` y `blender`.
- La validación estática pre-rollback pasó; después del rollback el TOML
  volvió a coincidir byte a byte con el snapshot POST-CONFIG.

### Snapshot POST-CONFIG

- Snapshot creado fuera del repositorio: `<USERPROFILE>/.codex/backups/home-studio-3d-t2-12-POST-CONFIG-20260905-151853.toml.bak`.
- Naturaleza: copia posterior a la configuración de Codex; no es un backup pre-change y no sobrescribe backups antiguos.
- Tamaño del original y snapshot: `5680` bytes.
- SHA-256 del original y snapshot: `2d08bdecb8afac19fe7f08a7cf060ed0d76ad996314dac561c9890545139eb`.
- Coincidencia byte a byte: **PASS**.

### Drift y rollback mínimo de configuración

- Drift detectado: se añadieron las tablas
  `[mcp_servers.blender.tools.execute_blender_code]` y
  `[mcp_servers.blender.tools.get_viewport_screenshot]`, ambas con
  `approval_mode = "approve"`.
- Naturaleza e impacto: son overrides oficiales de aprobación por herramienta
  MCP; no modifican sandbox, política global, rutas, flags, autenticación ni
  credenciales. La persistencia de `approve` para `execute_blender_code` era
  relevante para seguridad porque reducía la aprobación interactiva de una
  capacidad privilegiada.
- Rollback mínimo aplicado: eliminación exclusiva de esas dos tablas y sus
  claves `approval_mode`; `[mcp_servers.blender]`, `node_repl` y el resto del
  archivo no se modificaron.
- Restauración exacta: `config.toml` quedó en `5680` bytes y coincidió byte a
  byte con el snapshot POST-CONFIG, SHA-256
  `2D08BDEFCB8AFAC19FE7F08A7CF060ED0D76AD9963141DAC561C9890545139EB`.
- Causa: no atribuida con certeza; existe correlación temporal con la sesión
  T2.12, pero no evidencia local concluyente del escritor.
- Recomendación: vigilar si Codex vuelve a persistir automáticamente
  `approval_mode` específico de herramienta.

### Validación runtime Codex → Blender MCP

- Blender portable 5.2.1 LTS se inició con la escena inicial por defecto;
  ventana `(Unsaved) - Blender 5.2.1 LTS`.
- Listener: **PASS**, únicamente `127.0.0.1:9876`, asociado al proceso de
  Blender; no apareció binding en `0.0.0.0`, `[::]` ni IP LAN.
- Conexiones atribuibles a Blender/MCP: únicamente loopback; cero conexiones
  externas.
- Codex CLI → MCP: **PASS**; `blender` reconocido y llamada MCP completada con
  `isError=false`.
- Handshake: **PASS**.
- `get_scene_info`: **PASS**. Escena `Scene`, exactamente `Cube`, `Light` y
  `Camera`; `object_count=3` y `materials_count=2`.
- Después del smoke inicial se ejecutó `execute_blender_code` únicamente para
  abrir y leer el fixture; no se escribió ni guardó ningún dato Blender.
- Seguridad post: `BLENDER_MCP_SAFE_MODE=1`, `DISABLE_TELEMETRY=true`,
  consentimiento de telemetría `false` e integraciones externas `false`, sin
  cambios de preferencias durante esta validación. `get_addon_status` no se
  utilizó por la deuda conocida de `blender_mcp.config`.

### Validación cross-machine del fixture

- Fixture abierto exclusivamente: `blender/scenes/tests/001-foundation-room.blend`.
- Hash PRE-OPEN y POST-OPEN: `7304c737f5c329c936559850f3ae2b4debe27f4b7855ceb325d67318f517c8e6`.
- Tamaño PRE/POST: `103445` bytes; coincidencia con el blob de `HEAD`: **PASS**.
- Blender 5.2.1 LTS; filepath exacto del fixture; escena limpia (`is_dirty=false`)
  inmediatamente después de abrir y después de reabrir.
- Unidades: `METRIC`, `scale_length=1.0`.
- Estructura: colección `HS3D_T2_09_FOUNDATION_ROOM`, exactamente 10 objetos
  contractuales; `Cube`, `Camera` y `Light` ausentes.
- Geometría: volumen interior `5.00 × 4.00 × 2.50 m`; caras interiores
  `X=0/5`, `Y=0/4`, `Z=0`; paredes de `0.10 m` creciendo hacia fuera; todas
  las desviaciones numéricas observadas fueron inferiores a `1e-6 m`.
- `door`: dimensiones `0.90 × 0.05 × 2.10 m`, centro geométrico
  `(1.45,-0.025,1.05)`; `window`: `0.05 × 1.20 × 1.00 m`, centro
  `(5.025,2.00,1.50)`; ambas **PASS** en sus paredes contractuales.
- `sofa_proxy`: dimensiones `1.80 × 0.80 × 0.90 m`, `location=(2.50,2.00,0.45)`,
  rotación y escala unitarias, bbox local recentrado y totalmente dentro del
  volumen; la corrección del portátil persistió.
- Cámara activa `HS3D_TEST_CAMERA` y luz `HS3D_TEST_LIGHT` presentes con tipos
  correctos y transformaciones persistidas.
- Reapertura controlada: filepath, unidades, estructura, geometría, sofá,
  cámara activa y escena limpia confirmados nuevamente.
- Inspección visual: captura temporal MCP no persistida; volumen, suelo,
  paredes, puerta, ventana, cámara y luz coherentes, sin artefactos graves.
- Integridad de configuración: la comprobación final encontró que
  `config.toml` actual (`5835` bytes, SHA-256
  `21BEBFADE6E8A0D2913231EB0CFB560B88E584426D9320829C5AE695D2E51853`) ya no
  coincide con el snapshot POST-CONFIG (`5680` bytes, SHA-256
  `2D08BDEFCB8AFAC19FE7F08A7CF060ED0D76AD9963141DAC561C9890545139EB`); el cambio aparece como dos secciones
  `approval_mode` bajo tools MCP, sin valores sensibles registrados aquí.
  El rollback mínimo posterior restauró el snapshot exactamente.
- Resultado del fixture cross-machine: **PASS**. Resultado global de esta
  validación: **PASS** tras el rollback mínimo. No se guardó
  el fixture, no se creó ningún `.blend` ni asset y no se sobrescribió el
  preview versionado.

## Git y Git LFS

- Git: `git version 2.55.0.windows.3`.
- Git LFS: `git-lfs/3.7.1` para Windows amd64.
- `.gitattributes`: no existe en el repo.
- No se ejecutaron `git lfs install`, migraciones ni configuración de LFS.

## Blender MCP, procesos y red local

- Repositorio oficial: `https://github.com/ahujasid/blender-mcp`.
- `<MCP_HOME>`: `<LOCALAPPDATA>\Programs\HomeStudio3D\MCP\blender-mcp\5866814479b4e2ca674d8d44969a9a2a78fdc8bb`.
- Remote verificado contra el repositorio oficial; checkout detached en el
  commit exacto; HEAD y working tree del checkout están limpios.
- `pyproject.toml`: paquete `blender-mcp`, versión `1.9.1`; `.python-version`:
  `3.11`.
- Dependencias: entorno `.venv` creado en `<MCP_HOME>` con
  `uv sync --locked --python 3.11.15`; `uv` y `uvx` son `0.12.5`; no se
  modificó el lockfile ni el árbol del checkout.
- Addon fuente: `<MCP_HOME>\addon.py`.
- Addon instalado: `<APPDATA>\Blender Foundation\Blender\5.2\scripts\addons\blender_mcp.py`.
  Fuente e instalado tienen `179358` bytes y SHA-256
  `e9eae227d94875d6b8ed208f11a9628101ef4f579bfc614ab31af296cb88afce`;
  la coincidencia es exacta.
- Preferencias mínimas del addon: habilitado; autoarranque activo; puerto
  `9876`; consentimiento de telemetría `false`; Poly Haven, Sketchfab, Poly
  Pizza, Hyper3D/Rodin y Hunyuan3D deshabilitados; campos de credenciales
  vacíos. No se instaló ningún addon adicional.
- Contrato de lanzamiento comprobado en el entorno bloqueado:
  `BLENDER_MCP_SAFE_MODE=1`, `DISABLE_TELEMETRY=true`,
  `BLENDER_HOST=127.0.0.1` y `BLENDER_PORT=9876`. Safe mode y la desactivación
  de telemetría resultaron activos; no se guardaron secretos.
- Arranque GUI/addon controlado: **PASS**. Título `(Unsaved) - Blender 5.2.1
  LTS`, ventana visible y con respuesta; listener actual exclusivamente en
  `127.0.0.1:9876`, asociado al proceso de Blender.
- La validación runtime Codex → MCP → Blender y `get_scene_info` resultó
  **PASS**; `execute_blender_code` se usó después únicamente para abrir y leer
  el fixture, y no se usó `get_addon_status`.
- `[mcp_servers.blender]` está presente. La reanudación no hizo una edición
  manual de `config.toml`, pero la comparación final contra el snapshot detectó
  las dos secciones `approval_mode` añadidas; el fixture se abrió y reabrió sin
  guardar ningún `.blend`.
- Deuda conocida no bloqueante: `get_addon_status` puede fallar porque el pin
  no contiene `src/blender_mcp/config.py`, aunque `telemetry.py` lo importa.
  No se parcheó upstream ni se cambió el pin.

### Rollback de la réplica MCP

1. Detener cualquier proceso MCP y Blender.
2. Desactivar/eliminar únicamente `<APPDATA>\Blender Foundation\Blender\5.2\scripts\addons\blender_mcp.py`.
3. Eliminar únicamente la configuración local atribuible a esta réplica; en
   esta instalación la preferencia de usuario se creó para el addon y no se
   debe tocar otra configuración.
4. Eliminar `<MCP_HOME>` completo, incluido su `.venv`.
5. Verificar que `127.0.0.1:9876` deja de escuchar.

## Comparación breve con el portátil

La comparación usa `docs/setup/laptop-environment-inventory.md` y los
resultados posteriores documentados en `docs/decisions/002-blender-mcp-selection.md`.
Cuando la documentación del portátil conserva un baseline anterior, se indica
la limitación en lugar de ocultarla.

| Área | Portátil documentado | Sobremesa inventariado |
| --- | --- | --- |
| CPU | Intel i7-13650HX, 14 núcleos/20 lógicos | AMD Ryzen 7 5800X, 8/16 |
| RAM | aproximadamente 15.63 GiB | aproximadamente 31.93 GiB |
| GPU/VRAM | Intel UHD + RTX 4070 Laptop, 8188 MiB fiables | RTX 3080, 10240 MiB fiables |
| Almacenamiento | NTFS local NVMe; aproximadamente 121.8 GiB libres; ruta sin indicadores visibles de sincronización | NTFS NVMe; aproximadamente 195.0 GiB libres; clon activo fuera de OneDrive; copia antigua no utilizada |
| Blender | Portable 5.2.1 LTS en `<BLENDER_HOME>`; ejecutable fuera del repo | Portable 5.2.1 LTS desplegado en `<BLENDER_HOME>`; `--version`, smoke headless y primer arranque GUI PASS |
| Python | Global 3.14.6; embebido Blender 3.13.13; MCP externo 3.11.15 | Global 3.14.7; embebido Blender 3.13.13 AMD64; MCP externo 3.11.15 en `.venv` gestionado por uv; no hay `py` |
| uv / uvx | 0.12.4 | 0.12.5 |
| Codex | Los resultados posteriores registran `codex-cli 0.153.1` y entrada MCP lógica `blender`; el inventario inicial no pudo validar el launcher | `codex-cli 0.153.3` mediante `codex.cmd`; entrada `blender` presente y reconocida |
| MCP | `ahujasid/blender-mcp` instalado en `<MCP_HOME>`, pin `5866814479b4e2ca674d8d44969a9a2a78fdc8bb`, addon y listener loopback validados | Mismo checkout/pin, versión 1.9.1, addon, listener loopback, handshake y `get_scene_info` validados |
| Rutas relevantes | `<REPO_ROOT>`, `<BLENDER_HOME>`, `<MCP_HOME>`, `<USERPROFILE>\.codex\config.toml` | Misma convención lógica; `<BLENDER_HOME>` y `<MCP_HOME>` fuera del repo; clon activo fuera de OneDrive |

Las diferencias de CPU, RAM y VRAM no impiden por sí mismas repetir una escena
de prueba ligera. El portátil tiene una diferencia de uv (`0.12.4` frente a
`0.12.5`) y la documentación de Codex conserva estados de fechas distintas;
deben tratarse como datos a comprobar durante la réplica, no como una
justificación para modificar ahora el entorno.

## Decisión de réplica y bloqueos actuales

| Objetivo de la réplica | Estado del sobremesa | Decisión / siguiente paso |
| --- | --- | --- |
| Blender 5.2.1 LTS portable ZIP | Desplegado y validado; `--version`, smoke headless y primer arranque GUI PASS | Réplica de Blender completada en `<BLENDER_HOME>`; rollback limitado a retirar esa carpeta. |
| MCP `ahujasid/blender-mcp` en `5866814479b4e2ca674d8d44969a9a2a78fdc8bb` | Checkout exacto, versión 1.9.1, addon y dependencias validados | Réplica local completada; `[mcp_servers.blender]`, handshake y `get_scene_info` validados. |
| Python MCP 3.11.x gestionado por uv | Python 3.11.15 en `.venv`, creado con `uv sync --locked`; separado del global y del embebido | PASS para la réplica local; registro en Codex y handshake validados. |
| Safe mode, telemetría, loopback e integraciones deshabilitadas | Flags de lanzamiento y preferencias del addon validados; sin API keys | PASS local; conservar el contrato al registrar el MCP en Codex. |
| Entrada Codex MCP `blender` | Presente; `codex mcp list` **PASS** | Handshake, `get_scene_info` y fixture cross-machine **PASS**; rollback mínimo de drift de aprobación verificado. |
| Riesgo de almacenamiento OneDrive | Clon activo fuera de OneDrive; la copia antigua no se usa | No constituye bloqueo operativo para el clon activo. |

No hay un bloqueo de hardware ni de OneDrive para mantener esta réplica en el
clon activo: la RTX 3080 dispone de 10 GB de VRAM y el sobremesa tiene
aproximadamente 32 GiB de RAM. La entrada Codex está registrada; Blender, el
handshake, `get_scene_info` y la validación cross-machine del fixture pasan. La
deuda conocida del pin (`get_addon_status` no puede importar
`blender_mcp.config`) debe mantenerse documentada y no se corrige en esta tarea.
El cierre global queda desbloqueado: `config.toml` coincide exactamente con el
snapshot POST-CONFIG tras retirar únicamente las dos secciones `approval_mode`.
La causa de la persistencia automática no quedó atribuida con certeza y debe
vigilarse en futuras sesiones.

## Operaciones excluidas y validación de este inventario

- Se desplegó Blender 5.2.1 LTS portable desde el ZIP oficial verificado y se
  instaló únicamente el MCP fijado y su `addon.py` exacto; las dependencias se
  limitaron al lockfile mediante `uv sync --locked`.
- No se editaron PATH, ExecutionPolicy ni el registro del sistema;
  `[mcp_servers.blender]` ya estaba presente. Se aplicó únicamente el
  rollback autorizado de las dos tablas `approval_mode` y se restauró el
  snapshot POST-CONFIG byte a byte.
  Se creó únicamente el snapshot POST-CONFIG externo descrito arriba; Git LFS
  sigue sin configurarse.
- Se persistieron únicamente las preferencias de seguridad necesarias del
  addon: consentimiento de telemetría `false`, autoarranque/puerto local e
  integraciones externas deshabilitadas. No se guardó startup file.
- El smoke headless y el arranque GUI/addon pasan; `execute_blender_code` se
  usó únicamente para abrir y leer el fixture sin escritura ni guardado, y no
  se hizo render pesado ni benchmark.
- En esta reanudación Blender se inició, el handshake y `get_scene_info`
  resultaron **PASS**; también se ejecutaron lecturas deterministas del
  fixture y una captura temporal de viewport, sin tools de escritura.
- El listener post-runtime permanece exclusivamente en `127.0.0.1:9876`; no
  hubo conexiones externas atribuibles a Blender/MCP. No se hizo commit ni
  push.
- La evidencia visual del sobremesa es una captura MCP temporal no persistida;
  el preview versionado del portátil no se sobrescribió.
- La validación documental aplicable es la revisión del diff, `git diff
  --check` y `git status --short`.
