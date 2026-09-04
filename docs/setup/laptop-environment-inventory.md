# Inventario del entorno del portátil

Fecha de inventario: 2026-09-04.

Este inventario corresponde a T2.02, T2.03 y T2.04. Se obtuvo mediante comprobaciones de lectura, salvo la descarga y extracción autorizadas del artefacto de T2.03/T2.04 y los arranques controlados de Blender. No se guardó ninguna escena `.blend`, no se instaló ningún addon o paquete, no se modificó PATH ni se configuraron MCP/Codex. Las rutas se expresan con variables sanitizadas para no registrar nombres de usuario ni rutas personales innecesarias.

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
| Codex CLI | PRESENTE PERO NO VALIDADO | Hay launchers, pero `--version` no pudo validarse por el entorno de ejecución. |
| Configuración de Codex | PRESENTE PERO NO VALIDADO | Existe configuración con MCP de otros proyectos; no se identificó una entrada de Blender. |
| Blender MCP | NO DISPONIBLE | No se identificó instalación, addon o proceso de Blender MCP. |
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
- La extracción creó `<BLENDER_HOME>` fuera del repositorio. No se creó la carpeta propuesta `<BLENDER_HOME>` dentro del repo.
- Python embebido: `3.13.13 (MSC v.1944 64 bit (AMD64))`, runtime bajo `<BLENDER_HOME>\blender-5.2.1-windows-x64\5.2\python`; `sys.executable` es el `python.exe` embebido de esa distribución. El Python global del portátil sigue siendo `3.14.6` en `<USERPROFILE>\AppData\Local\Python\bin\python.exe`.
- Smoke headless: exit code `0`; `bpy.app.version_string=5.2.1 LTS`, escena activa `Scene`, unidades `METRIC`, escala `1.0`; no se guardó ningún `.blend`.
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
| Portable ZIP | `blender-5.2.1-windows-x64.zip`; `404851964` bytes (aprox. 386 MiB) | No requiere instalador ni privilegios administrativos para una carpeta escribible por el usuario; no crea asociaciones de `.blend` por sí solo. Cualquier asociación o acceso directo sería una decisión posterior. | Rollback simple eliminando o sustituyendo la carpeta versionada; facilita repetir la misma carpeta y versión en el sobremesa. | **Opción propuesta** para Home Studio 3D por menor impacto global y mejor pin de versión. |

Artefacto objetivo propuesto: `blender-5.2.1-windows-x64.zip`.

- URL canónica propuesta: `https://download.blender.org/release/Blender5.2/blender-5.2.1-windows-x64.zip`.
- Fichero oficial de checksums: `https://download.blender.org/release/Blender5.2/blender-5.2.1.sha256`.
- SHA-256 local: `0e631dad7d0cad6d5d18abdd2e2550f6c0213215334eda00ddbd3d22b96ecb2c`.
- Entrada relevante del checksum oficial: `0e631dad7d0cad6d5d18abdd2e2550f6c0213215334eda00ddbd3d22b96ecb2c  blender-5.2.1-windows-x64.zip`.
- SHA-256 oficial: `0e631dad7d0cad6d5d18abdd2e2550f6c0213215334eda00ddbd3d22b96ecb2c`.
- Tamaño descargado: `404851964` bytes; coincide con el tamaño esperado.
- Resultado: **PASS** para procedencia, nombre, tamaño, hash local, hash oficial y hash de referencia.
- Ubicación sanitizada del ZIP: `<T2_03_DOWNLOAD_DIR>\blender-5.2.1-windows-x64.zip`.
- El ZIP se conserva sin extraer. La extracción y ejecución requieren autorización separada.

Ubicación portable propuesta, aún no creada: `<LOCALAPPDATA>\Programs\Blender\5.2.1`, documentada operacionalmente como `<BLENDER_HOME>`. Debe quedar fuera de `<REPO_ROOT>`, sin versionarse y con la misma convención de variable en el sobremesa.

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

## Codex CLI y configuración MCP existente

- El launcher `codex` está presente en `<CODEX_BIN>\codex.ps1`.
- `codex --version` no pudo ejecutarse porque la política de PowerShell impide cargar el script `.ps1`.
- También existe `<CODEX_BIN>\codex.cmd`; `codex.cmd --version` no devolvió una versión y mostró un aviso del launcher sobre la imposibilidad de crear aliases PATH por no encontrar el home directory.
- Existe `<USERPROFILE>\.codex\config.toml`. Se inspeccionó únicamente su estructura; no se mostraron ni registraron valores.
- Se identificaron las secciones MCP existentes `[mcp_servers.node_repl]` y `[mcp_servers.unity]`, junto con sus secciones de herramientas. No se identificó una sección `mcp_servers` de Blender.
- La configuración no se modificó. La integración de un MCP local de Blender requerirá una decisión separada y autorización explícita.

## MCP, procesos y listeners

- No se identificaron procesos cuyo nombre indicase MCP o Blender.
- No se identificaron archivos de configuración MCP en el repositorio.
- El addon MCP de Blender no puede validarse sin iniciar Blender y, al no estar Blender instalado, queda `NO APLICA`.
- Se observaron 27 listeners TCP en loopback durante la consulta local; no se registraron puertos ni PIDs y ninguno pudo atribuirse a Blender MCP porque no hay instalación/proceso/configuración identificados.
- No se abrió ningún puerto ni se probó conectividad externa.
- Había una interfaz activa de categoría `Native 802.11`; no se recopilaron direcciones, MAC ni otros identificadores.

Para la validación futura de localhost se podrán usar, en modo read-only:

- `Get-NetTCPConnection -State Listen`, filtrando `LocalAddress` a `127.0.0.1` y `::1`;
- `netstat.exe -ano`, filtrando endpoints loopback y relacionando un PID solo cuando sea necesario.

La comprobación de listeners demuestra bindings observables en ese momento. No demuestra por sí sola que el código de Blender/Python esté técnicamente sandboxeado respecto al filesystem; esa garantía depende de permisos, sandbox o auditoría disponibles, además de la política del proyecto.

## Git y Git LFS

- Git: `git version 2.55.0.windows.3`, ejecutable bajo `<PROGRAMFILES>\Git\cmd\git.exe`.
- Git LFS: `git-lfs/3.7.1` para Windows amd64.
- `.gitattributes`: no existe en el repositorio.
- No se ejecutaron `git lfs install`, inicialización, configuración ni migraciones.

## Límites y decisiones pendientes

- T2.03 queda documentado con la opción portable ZIP como distribución verificada; la extracción y ejecución requieren autorización separada.
- La discrepancia entre la resolución de `python` en PowerShell y `where python` queda caracterizada: PowerShell resuelve el ejecutable real `<USERPROFILE>\AppData\Local\Python\bin\python.exe` (Python 3.14.6), sin alias de PowerShell, shim de WindowsApps ni `py`; `where.exe` no devuelve una ruta en este entorno. No se modificó PATH.
- La versión efectiva de Codex CLI no quedó validada por ejecución: el paquete local declara `@openai/codex` `0.153.1`, pero el launcher PowerShell está bloqueado por ExecutionPolicy y el `.cmd` no completó la prueba por una incidencia de entorno/home. No se modificaron ExecutionPolicy, PATH ni configuración.
- El pin exacto de `ahujasid/blender-mcp` sigue pendiente de T2.05; no se ha instalado ningún MCP.
- Las comprobaciones de apertura de Blender, ejecución `bpy`, handshake MCP, addon, escena, dimensiones, captura visual y rendimiento quedan pendientes de infraestructura y de autorización para las siguientes tareas.
