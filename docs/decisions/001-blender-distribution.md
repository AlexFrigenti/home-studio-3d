# Decisión propuesta: distribución de Blender

Estado: distribución propuesta, artefacto descargado/verificado en T2.03 y portable desplegado/validado en T2.04; MCP aún no configurado.

## Decisión

Adoptar como distribución inicial propuesta **Blender 5.2.1 LTS Windows x64 Portable ZIP** para el portátil y su posterior reproducción en el sobremesa.

La decisión mantiene Blender 5.2 LTS como línea de soporte, pero fija `5.2.1 LTS` como versión inicial objetivo. No depende de GPT-6 Astra ni autoriza ninguna instalación.

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

Antes de extraer o ejecutar, el procedimiento autorizado deberá:

1. descargar exclusivamente desde la URL canónica;
2. obtener el checksum oficial;
3. calcular el SHA-256 local y comprobar también el tamaño;
4. rechazar el artefacto ante cualquier discrepancia;
5. registrar versión, URL, tamaño y hash aceptado.

Estos pasos se ejecutaron en T2.03 y resultaron PASS. El ZIP no se ha extraído ni ejecutado.

## Ubicación

No se creará la carpeta durante T2.03. La ubicación propuesta es:

`<LOCALAPPDATA>\Programs\Blender\5.2.1`

En la documentación operativa se referenciará como `<BLENDER_HOME>`. Queda fuera de `<REPO_ROOT>`, no se versiona y puede reproducirse en el sobremesa estableciendo la misma variable lógica, sin registrar una ruta personal absoluta.

## Comparativa resumida

| Criterio | MSI/Installer | Portable ZIP |
| --- | --- | --- |
| Artefacto oficial | `blender-5.2.1-windows-x64.msi`, `365113344` bytes | `blender-5.2.1-windows-x64.zip`, `404851964` bytes |
| Administración | Puede requerir privilegios según destino/opciones | No requiere instalador ni privilegios para carpeta de usuario |
| Estado global | Puede registrar instalación, desinstalación y asociaciones | No registra asociaciones por sí solo |
| Rollback | Desinstalar y revisar estado residual | Retirar o sustituir la carpeta versionada |
| Segundo equipo | Repetir instalador y decisiones de ruta/asociación | Repetir artefacto, hash y convención `<BLENDER_HOME>` |

Las propiedades operativas de instalación y asociaciones se validarán durante la ejecución autorizada; no se ha ejecutado Blender ni el instalador.

## Límites

- No se extrae ni ejecuta Blender como parte de T2.03; la descarga autorizada quedó verificada y conservada en una ubicación temporal.
- No se modifica PATH, ExecutionPolicy, configuración de Codex, configuración de Blender ni Git LFS.
- No se fija aún el commit de `ahujasid/blender-mcp`; corresponde a T2.05.
