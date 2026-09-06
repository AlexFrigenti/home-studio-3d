# Inventario del entorno del portátil

Fecha de inventario: 2026-09-04.

Este inventario corresponde a T2.02, T2.03 y T2.04. Su baseline inicial se obtuvo mediante comprobaciones de lectura, salvo la descarga y extracción autorizadas del artefacto de T2.03/T2.04 y los arranques controlados de Blender. En fases posteriores se instalaron el addon y el servidor MCP, y se añadió la entrada local de Blender a Codex; esas configuraciones permanecen fuera del repositorio. Las rutas se expresan con variables sanitizadas para no registrar nombres de usuario ni rutas personales innecesarias.

## Clasificación resumida

| Componente | Estado | Resultado |
| --- | --- | --- |
| Windows, CPU, RAM y GPU | DISPONIBLE | Inventario del sistema obtenido. |
| Espacio y tipo de unidad del repo | DISPONIBLE | Unidad local fija NTFS sobre bus NVMe; espacio libre registrado. |
| Permiso de escritura del repo | PRESENTE PERO NO VALIDADO | La ACL muestra derechos de escritura; no se hizo una prueba creando archivos. |
| Blender | DISPONIBLE | Portable Blender 5.2.1 LTS desplegado fuera del repo; no se añadió a PATH. |
| Python del sistema | DISPONIBLE | `python --version` devuelve Python 3.14.6. |
| Python Launcher (`py`) | NO DISPONIBLE | `py --version` y `where py` no encuentran el comando. |
| Python embebido de Blender | DISPONIBLE | Python 3.13.13 incluido en el portable; no se instalaron paquetes. |
| `uv` / `uvx` | DISPONIBLE | Versión 0.12.4 en ambos comandos; no se instalaron ni actualizaron. |
| Codex CLI | OPERATIVO | La versión observada durante T2.07/T2.08 fue `0.153.1`; la comunicación con Blender MCP quedó validada en esas tareas. |
| Configuración de Codex | CONFIGURADA LOCALMENTE | La entrada lógica `blender` quedó añadida fuera del repositorio; las entradas previas permanecieron intactas. |
| Blender MCP | INSTALADO Y OPERATIVO | Pin `5866814479b4e2ca674d8d44969a9a2a78fdc8bb`, addon instalado y listener validado en `127.0.0.1:9876`. |
| Git | DISPONIBLE | Git 2.55.0.windows.3. |
| Git LFS | DISPONIBLE | Git LFS 3.7.1; no se inicializó ni configuró. |
| Herramientas de listeners locales | DISPONIBLE | `Get-NetTCPConnection` y `netstat.exe` están disponibles. |

## Sistema

- Edición: Windows 11 Home.
- Versión/build: `10.0.26200`, build `26200`.
- Arquitectura: 64 bits.
- CPU: 13th Gen Intel(R) Core(TM) i7-13650HX; 14 núcleos, 20 procesadores lógicos.
- RAM total: aproximadamente 15.63 GB.
- GPU integrada: Intel(R) UHD Graphics. No se adopta una VRAM fiable a partir del dato WMI.
- GPU dedicada: NVIDIA GeForce RTX 4070 Laptop GPU; `8188 MiB` según `nvidia-smi`, única fuente considerada fiable para esta cifra.

## Repositorio y almacenamiento

- Ruta: `<REPO_ROOT>`.
- Unidad: `C:`, filesystem NTFS, disco local fijo, bus NVMe.
- Capacidad aproximada: 952.8 GB; libres aproximadamente 121.8 GB.
- La ruta no contiene indicadores visibles de OneDrive, Dropbox, Google Drive, iCloud, Box, pCloud u otro proveedor conocido. Esto no demuestra que no exista una sincronización personalizada fuera de la ruta.
- La ACL del directorio es legible y contiene derechos de escritura/modificación. No se realizó una prueba de escritura para mantener la comprobación sin cambios.

## Blender

- PATH: no se añadió el portable y `blender` no se usa como comando global.
- `<BLENDER_HOME>`: `<LOCALAPPDATA>\Programs\Blender\5.2.1`.
- Ejecutable efectivo: `<BLENDER_HOME>\blender-5.2.1-windows-x64\blender.exe`.
- `--version`: exit code `0`; `Blender 5.2.1 LTS`; build hash `9e2066aef7ef`; plataforma Windows; link flags `/MACHINE:X64`.
- El análisis PE confirmó máquina `0x8664` (`x64/AMD64`).
- El ZIP verificado se conserva fuera del repo en `<T2_03_DOWNLOAD_DIR>\blender-5.2.1-windows-x64.zip`.

## T2.04 — Despliegue portable y validación

- El destino no existía antes de extraer y no se sobrescribió ninguna instalación previa.
- La extracción creó `<BLENDER_HOME>` fuera del repositorio y no creó ninguna instalación dentro del repo.
- Python embebido: `3.13.13 (MSC v.1944 64 bit (AMD64))`, runtime bajo `<BLENDER_HOME>\blender-5.2.1-windows-x64\5.2\python`; `sys.executable` es el `python.exe` embebido de esa distribución. El Python global del portátil sigue siendo `3.14.6` en `<USERPROFILE>\AppData\Local\Python\bin\python.exe`.
- Smoke headless: exit code `0`; `bpy.app.version_string=5.2.1 LTS`, escena activa `Scene`, unidades `METRIC`, escala `1.0`; esta comprobación inicial no guardó ningún `.blend`.
- Guardado independiente T2.04: se creó `blender/scenes/tests/002-blender-empty-save-smoke.blend` (`99838` bytes; SHA-256 `3B4C9DCDEDDE2939FC3A919CDD866D22D20129958B371BF4D2D4B0D907C748C`). La escena `T2_04_EMPTY_SAVE_SMOKE` se define factual y explícitamente como vacía: 0 objetos, 0 materiales, unidades `METRIC`, `scale_length = 1.0` y sin assets externos. Se guardó, se cerró y se reabrió con Blender `5.2.1 LTS`; el archivo abrió correctamente, el contenido persistió y no quedó dirty.
- Red T2.04: comprobación read-only posterior con listener únicamente en `127.0.0.1:9876`, cero listeners no-loopback en ese puerto y cero conexiones establecidas no-loopback atribuibles a Blender/MCP.
- Primer arranque GUI: una única ventana `(Unsaved) - Blender 5.2.1 LTS`, con handle de ventana y respuesta positiva; se cerró dentro de 10 segundos. No se interactuó con diálogos ni se cambiaron preferencias. No se obtuvo captura pixel-level; la evidencia GUI es de proceso/ventana y el viewport no se marca como inspección visual independiente.
- GPU/Cycles read-only: NVIDIA GeForce RTX 4070 Laptop GPU detectada como `CUDA` y `OPTIX`; también apareció el dispositivo `CPU`. Se registró un warning de inicialización HIP, no aplicable a la GPU NVIDIA. No se cambió el backend, no se hicieron benchmarks ni renders.
- El primer arranque dejó observados 15 archivos `*.blend.index.json` de caché de Asset Library bajo `<LOCALAPPDATA>\Blender Foundation\Blender\Cache\asset-library-indices\...`, con marcas de tiempo inmediatamente posteriores al arranque. No se observaron archivos `userpref` ni `startup`; al no existir un snapshot previo de la caché, no se atribuye causalidad absoluta, pero queda registrado como cambio persistente observable.

### Rollback de T2.04

El rollback documentado consiste en cerrar Blender, eliminar `<BLENDER_HOME>` y eliminar cualquier configuración/cache local únicamente después de identificarla con seguridad como perteneciente a esta instalación o prueba. No se ejecutó rollback.

## T2.03 — Distribución de Blender

La comparación se limita a los artefactos oficiales Windows x64 de Blender 5.2.1 LTS publicados por [Blender](https://www.blender.org/download/) y su [archivo oficial de releases](https://download.blender.org/release/Blender5.2/). No se consultaron mirrors de terceros. La descarga autorizada se realizó únicamente desde `download.blender.org`.

| Opción | Artefacto y tamaño publicado | Privilegios/cambios globales | Rollback y reproducibilidad | Adecuación provisional |
| --- | --- | --- | --- | --- |
| MSI/Installer | `blender-5.2.1-windows-x64.msi`; `365113344` bytes (aprox. 348 MiB) | El instalador puede requerir privilegios administrativos y puede registrar instalación, desinstalación y asociaciones de `.blend` según opciones de Windows; debe confirmarse antes de ejecutar. | Desinstalación disponible, pero con más estado global y rutas dependientes del instalador. | Válido si se requiere integración de Windows y se acepta ese impacto. |
| Portable ZIP | `blender-5.2.1-windows-x64.zip`; `404851964` bytes (aprox. 386 MiB) | No requiere instalador ni privilegios administrativos para una carpeta escribible por el usuario; no crea asociaciones de `.blend` por sí solo. | Rollback simple eliminando o sustituyendo la carpeta versionada; facilita repetir la misma carpeta y versión en el sobremesa. | **Opción adoptada y validada** para Home Studio 3D por menor impacto global y mejor pin de versión. |

Artefacto objetivo y adoptado: `blender-5.2.1-windows-x64.zip`.

- URL canónica: `https://download.blender.org/release/Blender5.2/blender-5.2.1-windows-x64.zip`.
- Fichero oficial de checksums: `https://download.blender.org/release/Blender5.2/blender-5.2.1.sha256`.
- SHA-256 local: `0e631dad7d0cad6d5d18abdd2e2550f6c0213215334eda00ddbd3d22b96ecb2c`.
- Entrada relevante del checksum oficial: `0e631dad7d0cad6d5d18abdd2e2550f6c0213215334eda00ddbd3d22b96ecb2c  blender-5.2.1-windows-x64.zip`.
- SHA-256 oficial: `0e631dad7d0cad6d5d18abdd2e2550f6c0213215334eda00ddbd3d22b96ecb2c`.
- Tamaño descargado: `404851964` bytes; coincide con el tamaño esperado.
- Resultado: **PASS** para procedencia, nombre, tamaño, hash local, hash oficial y hash de referencia.
- Ubicación sanitizada del ZIP: `<T2_03_DOWNLOAD_DIR>\blender-5.2.1-windows-x64.zip`.
- El ZIP fue extraído y ejecutado en T2.04 con autorización separada; la validación de Blender 5.2.1 quedó registrada allí.

Ubicación portable efectiva: `<LOCALAPPDATA>\Programs\Blender\5.2.1`, documentada operacionalmente como `<BLENDER_HOME>`. Queda fuera de `<REPO_ROOT>`, no se versiona y la misma convención de variable se usa al documentar la réplica en el sobremesa.

## Python y herramientas auxiliares

- `python --version`: Python 3.14.6.
- Ruta resuelta por PowerShell: `<USERPROFILE>\AppData\Local\Python\bin\python.exe`.
- `where python`: no encontró una ruta, aunque PowerShell sí resolvió el comando; esta discrepancia debe aclararse antes de fijar el procedimiento reproducible.
- `py --version`: no disponible.
- `where py`: no encontrado.
- `uv --version`: `uv 0.12.4 (77803aa22 2026-08-13 x86_64-pc-windows-msvc)`.
- `uvx --version`: `uvx 0.12.4 (77803aa22 2026-08-13 x86_64-pc-windows-msvc)`.
- Rutas de `uv`/`uvx`: `<USERPROFILE>\.local\bin\uv.exe` y `<USERPROFILE>\.local\bin\uvx.exe`.

La presencia de Python o `uv` es un dato del entorno actual, no una autorización ni una decisión de instalación para T2.03.

## Baseline T2.02 — Codex CLI y configuración MCP existente

- En el inventario inicial, el launcher `codex` estaba presente en `<CODEX_BIN>\codex.ps1`.
- En ese snapshot, `codex --version` no pudo ejecutarse porque la política de PowerShell impedía cargar el script `.ps1`.
- También existía `<CODEX_BIN>\codex.cmd`; el intento inicial de `codex.cmd --version` no devolvió una versión y mostró un aviso del launcher sobre la imposibilidad de crear aliases PATH por no encontrar el home directory. La operación efectiva de Codex CLI se validó posteriormente en T2.07/T2.08.
- Existe `<USERPROFILE>\.codex\config.toml`. Se inspeccionó únicamente su estructura; no se mostraron ni registraron valores.
- En el snapshot T2.02 se identificaron las secciones MCP existentes `[mcp_servers.node_repl]` y `[mcp_servers.unity]`, junto con sus secciones de herramientas; todavía no había una sección `mcp_servers` de Blender.
- Durante ese inventario no se modificó la configuración. La integración local de Blender se decidió, autorizó y ejecutó posteriormente en T2.07; su estado actual figura en la tabla de clasificación y en la decisión 002.

## Baseline T2.02 — MCP, procesos y listeners

- En el inventario inicial no se identificaron procesos cuyo nombre indicase MCP o Blender.
- No se identificaron archivos de configuración MCP en el repositorio.
- El addon MCP de Blender no estaba validable durante el inventario inicial; la validación posterior se documenta en la decisión 002.
- Se observaron 27 listeners TCP en loopback durante la consulta local; no se registraron puertos ni PIDs y ninguno pudo atribuirse a Blender MCP porque no hay instalación/proceso/configuración identificados.
- No se abrió ningún puerto ni se probó conectividad externa.
- Había una interfaz activa de categoría `Native 802.11`; no se recopilaron direcciones, MAC ni otros identificadores.

Para la validación futura de localhost se podrán usar, en modo read-only:

- `Get-NetTCPConnection -State Listen`, filtrando `LocalAddress` a `127.0.0.1` y `::1`;
- `netstat.exe -ano`, filtrando endpoints loopback y relacionando un PID solo cuando sea necesario.

La comprobación de listeners demuestra bindings observables en ese momento. La validación posterior confirmó el listener de Blender MCP en `127.0.0.1:9876`; esto no demuestra por sí solo que el código de Blender/Python esté técnicamente sandboxeado respecto al filesystem.

## Estado validado posteriormente

- Blender 5.2.1 LTS, Blender MCP y Codex CLI quedaron instalados y operativos en el portátil.
- La comunicación live `Codex → Blender MCP → Blender` quedó validada mediante `get_scene_info`.
- El fixture `blender/scenes/tests/001-foundation-room.blend` quedó validado y fue probado entre portátil y sobremesa. No se registran rutas ni inventario adicionales del sobremesa en este documento.

## Git y Git LFS

- Git: `git version 2.55.0.windows.3`, ejecutable bajo `<PROGRAMFILES>\Git\cmd\git.exe`.
- Git LFS: `git-lfs/3.7.1` para Windows amd64.
- `.gitattributes`: no existe en el repositorio.
- No se ejecutaron `git lfs install`, inicialización, configuración ni migraciones.

## Límites y decisiones pendientes

- T2.03/T2.04 quedan documentados con la distribución portable ZIP adoptada y validada.
- La discrepancia entre la resolución de `python` en PowerShell y `where python` queda caracterizada: PowerShell resuelve el ejecutable real `<USERPROFILE>\AppData\Local\Python\bin\python.exe` (Python 3.14.6), sin alias de PowerShell, shim de WindowsApps ni `py`; `where.exe` no devuelve una ruta en este entorno. No se modificó PATH.
- El launcher PowerShell mantiene la limitación histórica de ExecutionPolicy; la operación efectiva de Codex CLI se validó mediante el launcher `.cmd` en T2.07/T2.08, sin modificar ExecutionPolicy ni PATH.
- El pin exacto de `ahujasid/blender-mcp`, el addon y el listener local están instalados y validados; la deuda conocida de `get_addon_status` se conserva en `docs/decisions/002-blender-mcp-selection.md`.
- No se registra aquí un inventario completo del sobremesa; solo queda documentada la prueba cruzada del fixture.
