# Decisión: distribución de Blender

Estado: distribución adoptada y validada en el portátil. Blender 5.2.1 LTS Portable ZIP se desplegó fuera del repositorio y su ejecución quedó validada; la conexión con Blender MCP también está validada en loopback.

## Decisión

Adoptar como distribución inicial **Blender 5.2.1 LTS Windows x64 Portable ZIP** para el portátil y su posterior reproducción en el sobremesa.

La decisión mantiene Blender 5.2 LTS como línea de soporte y fija `5.2.1 LTS` como versión inicial. No depende de GPT-6 Astra; cualquier instalación o cambio posterior requiere su autorización correspondiente.

## Motivos

- Es un artefacto oficial para Windows x64.
- No requiere un instalador ni privilegios administrativos cuando se usa una carpeta escribible por el usuario.
- Reduce cambios globales y evita depender de asociaciones automáticas de `.blend`.
- Permite rollback sustituyendo o retirando una carpeta versionada.
- Facilita fijar versión, ruta lógica y procedimiento para dos equipos.

La opción MSI sigue siendo válida como alternativa si una validación posterior demuestra una necesidad concreta de integración de Windows.

## Artefacto y verificación

Fuentes oficiales: [página de descargas de Blender](https://www.blender.org/download/) y [archivo oficial Blender 5.2](https://download.blender.org/release/Blender5.2/).

- Nombre exacto: `blender-5.2.1-windows-x64.zip`.
- URL canónica: `https://download.blender.org/release/Blender5.2/blender-5.2.1-windows-x64.zip`.
- Tamaño publicado: `404851964` bytes (aprox. 386 MiB).
- Fichero oficial de checksum: `https://download.blender.org/release/Blender5.2/blender-5.2.1.sha256`.
- SHA-256 local: `0e631dad7d0cad6d5d18abdd2e2550f6c0213215334eda00ddbd3d22b96ecb2c`.
- Entrada relevante del fichero oficial: `0e631dad7d0cad6d5d18abdd2e2550f6c0213215334eda00ddbd3d22b96ecb2c  blender-5.2.1-windows-x64.zip`.
- SHA-256 oficial: `0e631dad7d0cad6d5d18abdd2e2550f6c0213215334eda00ddbd3d22b96ecb2c`.
- Resultado de comparación: **PASS**; el hash local coincide con el oficial y con la referencia autorizada. El tamaño local es `404851964` bytes y también coincide.
- Ubicación sanitizada del ZIP descargado: `<T2_03_DOWNLOAD_DIR>\blender-5.2.1-windows-x64.zip`.

El procedimiento autorizado para T2.03/T2.04 fue:

1. descargar exclusivamente desde la URL canónica;
2. obtener el checksum oficial;
3. calcular el SHA-256 local y comprobar también el tamaño;
4. rechazar el artefacto ante cualquier discrepancia;
5. registrar versión, URL, tamaño y hash aceptado.

Estos pasos se ejecutaron en T2.03 y resultaron PASS. El ZIP se extrajo y se ejecutó posteriormente en T2.04; Blender reportó `5.2.1 LTS` y quedó disponible para la validación live con el MCP.

## Ubicación

La ubicación efectiva de la instalación portable es:

`<LOCALAPPDATA>\Programs\Blender\5.2.1`

En la documentación operativa se referencia como `<BLENDER_HOME>`. Queda fuera de `<REPO_ROOT>`, no se versiona y puede reproducirse en el sobremesa estableciendo la misma variable lógica, sin registrar una ruta personal absoluta.

## Comparativa resumida

| Criterio | MSI/Installer | Portable ZIP |
| --- | --- | --- |
| Artefacto oficial | `blender-5.2.1-windows-x64.msi`, `365113344` bytes | `blender-5.2.1-windows-x64.zip`, `404851964` bytes |
| Administración | Puede requerir privilegios según destino/opciones | No requiere instalador ni privilegios para carpeta de usuario |
| Estado global | Puede registrar instalación, desinstalación y asociaciones | No registra asociaciones por sí solo |
| Rollback | Desinstalar y revisar estado residual | Retirar o sustituir la carpeta versionada |
| Segundo equipo | Repetir instalador y decisiones de ruta/asociación | Repetir artefacto, hash y convención `<BLENDER_HOME>` |

La ejecución portable se validó en T2.04. No se crearon asociaciones de `.blend` ni se modificaron configuraciones globales como parte de esta foundation.

## Límites

- En T2.03 no se extrajo ni ejecutó Blender; la descarga quedó verificada y conservada fuera del repositorio. T2.04 cubrió la extracción y ejecución autorizadas.
- T2.03/T2.04 no modificaron PATH, ExecutionPolicy, configuración de Blender ni Git LFS. La configuración local de Codex se integró posteriormente en T2.07 y se documenta en la decisión 002.
- El pin de `ahujasid/blender-mcp` y su validación están documentados en `docs/decisions/002-blender-mcp-selection.md`.
