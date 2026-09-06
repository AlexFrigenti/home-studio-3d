# Plan: Blender + Codex + MCP Foundation

Estado de ejecución: las fases de inventario, distribución, MCP, integración, smoke y habitación sintética se ejecutaron y validaron. El fixture se probó entre portátil y sobremesa. Este documento conserva el procedimiento para futuras repeticiones; no inicia producción 3D.

## Especificación relacionada

- `spec.md`

## Enfoque

Construir la fundación de forma incremental, primero con inventario y decisiones reproducibles, después con instalación y configuración local controladas, y finalmente con un smoke técnico y una escena sintética de aceptación. Este plan se ejecutó con ese orden. Cada fase produjo evidencia concreta y mantiene la separación entre la escena de prueba, las medidas canónicas y cualquier escena futura de la vivienda.

La planificación no instala ni configura nada por sí misma. Las acciones de instalación, ejecución privilegiada, configuración de MCP y modificación de ajustes globales requieren autorización explícita en el punto indicado.

## Archivos y áreas afectadas

- Crear o actualizar documentación operativa en `docs/setup/` y decisiones en `docs/decisions/` cuando una fase produzca información estable.
- Usar `blender/scenes/` para la escena sintética desechable y sus variantes, nunca para sustituir escenas canónicas.
- Usar `blender/scripts/` únicamente para scripts inspeccionados y necesarios para la validación.
- Usar `renders/previews/` para evidencia visual de preview cuando deba conservarse.
- No modificar `measurements/` en este slice.
- No incorporar assets externos, modelos descargados, `.blend` canónicos ni Git LFS como parte del setup.

## Fases

### Fase 1 — Inventario del entorno actual del portátil

**Objetivo:** conocer el punto de partida sin cambiar el sistema ni introducir datos sensibles.

**Acciones:**

- Registrar sistema operativo, arquitectura, GPU, VRAM, RAM, rutas del repo y permisos relevantes.
- Comprobar si existen Blender, Python, Codex CLI, MCP u otros componentes previamente instalados, sin asumir que sean utilizables.
- Registrar versiones y rutas solo cuando sean necesarias y seguras; no capturar secretos, tokens ni rutas privadas que no deban versionarse.
- Identificar diferencias que podrían afectar a una futura réplica en el sobremesa.

**Validaciones:** inventario revisable, sin cambios de archivos fuera de la documentación autorizada y con ausencias diferenciadas de fallos.

**Rollback:** ninguno; la fase es de lectura. Eliminar del registro cualquier dato local que no sea necesario, sin tocar instalaciones.

**Autorización:** no requiere autorización adicional si permanece en lectura; requiere aprobación si se pretende modificar o limpiar instalaciones existentes.

### Fase 2 — Instalación reproducible de Blender 5.2.1 LTS

**Objetivo:** instalar y verificar Blender 5.2.1 LTS, dentro de la línea de soporte Blender 5.2 LTS, en el portátil de forma repetible.

**Acciones:**

- Antes de descargar o instalar, comparar explícitamente en Windows el instalador tradicional y la distribución portable ZIP oficial.
- Se adoptó la opción portable porque inicia la versión esperada, permite rutas reproducibles y configuración separada, evita cambios globales innecesarios y facilita un rollback limpio. T2.03 registró la decisión y su justificación.
- Obtener Blender 5.2.1 LTS de una fuente aprobada y registrar versión, fuente y hash cuando sea posible.
- Elegir una ruta documentada y evitar rutas absolutas personales en el repo.
- Mantener separadas las configuraciones de prueba de cualquier escena canónica.
- No se instalaron addons ni paquetes adicionales en esta fase; la instalación posterior del addon y del servidor MCP quedó autorizada y documentada en T2.06.

**Validaciones:** la modalidad elegida y sus criterios quedan documentados antes de la descarga; Blender inicia, reporta Blender 5.2.1 LTS, abre una escena vacía, puede guardar en un área de pruebas y no expone servicios no solicitados.

**Rollback:** para ZIP portable, retirar únicamente el directorio de instalación verificado; para instalador tradicional, desinstalar siguiendo el procedimiento documentado. En ambos casos, conservar el repo y cualquier escena canónica y eliminar solo archivos de prueba verificados.

**Autorización:** obligatoria antes de descargar o instalar Blender y antes de modificar configuraciones locales de Blender.

### Fase 3 — Instalación y configuración del MCP

**Objetivo:** seleccionar y ejecutar el candidato MCP de Blender con una frontera local verificable.

**Acciones:**

- Inspeccionar procedencia, licencia, versión, código y compatibilidad de `ahujasid/blender-mcp`.
- Consultar `webita/blender-codex-mcp` como referencia concreta para el acoplamiento con Codex, sin copiar código sin revisión.
- No instalar desde una rama mutable sin pin. T2.05 fijó y registró el commit exacto `5866814479b4e2ca674d8d44969a9a2a78fdc8bb` antes de la instalación autorizada.
- Determinar cómo arranca el servidor y cómo se conecta Blender, manteniendo el binding en localhost.
- Deshabilitar telemetría opcional si existe una opción soportada.
- Documentar la configuración como proyecto/local cuando el producto lo permita; no modificar configuración global sin aprobación.
- Cualquier actualización del pin aprobado obliga a repetir el smoke técnico y el test de aceptación.

**Validaciones:** procedencia, licencia y pin exacto registrados antes de instalar; arranque local, handshake MCP, puerto escuchando solo en loopback, ausencia de credenciales versionadas y comprobación de que no se expone a LAN/Internet. El límite de archivos se valida con la evidencia técnica disponible; la prohibición operativa de `AGENTS.md` no se presenta como sandbox técnico.

**Rollback:** detener el servidor, retirar la configuración local y desinstalar el componente aprobado si procede; conservar la evidencia y no borrar escenas fuera del área de pruebas.

**Autorización:** obligatoria antes de instalar el MCP, addon o servicio, ejecutar su código y abrir cualquier puerto local.

### Fase 4 — Integración con Codex CLI

**Objetivo:** permitir que Codex CLI trabaje desde el repo y acceda al MCP local con un alcance explícito.

**Acciones:**

- Ejecutar Codex desde el workspace y comprobar que el contexto del repo está disponible.
- Implementar únicamente la configuración de integración local soportada por Codex/MCP.
- Usar `webita/blender-codex-mcp` para contrastar nombres, transporte y secuencia de conexión antes de adoptar valores.
- Mantener la configuración reproducible y separada de credenciales o ajustes globales.

**Validaciones:** Codex obtiene información de la escena, la conexión se mantiene local, las rutas son reproducibles y ningún secreto aparece en archivos o logs versionables. Se inspeccionan scripts, rutas, permisos o auditoría del proceso cuando existan; sin esa evidencia, el control de acceso al workspace queda `PENDIENTE DE INFRAESTRUCTURA` o `NO EJECUTADO`, nunca `PASS` por la sola política.

**Rollback:** retirar la configuración de integración del proyecto y desconectar MCP; restaurar la capacidad de trabajar con el repo sin cambiar la instalación global de Codex.

**Autorización:** obligatoria antes de modificar configuración global de Codex, permitir herramientas privilegiadas o ejecutar acciones que puedan escribir en Blender.

### Fase 5 — Smoke técnico

**Objetivo:** demostrar el camino mínimo de comunicación y una operación controlada.

**Acciones:**

- Abrir Blender con una escena de prueba vacía.
- Pedir información básica de la escena a través de Codex/MCP.
- Como primera operación `bpy`, ejecutar una inspección de solo lectura, inocua y reversible (no cambia el estado), por ejemplo consultar el nombre de la escena y el número de objetos. No debe leer/escribir filesystem, red ni lanzar procesos externos.
- Tras esa comprobación, ejecutar solo una operación de escena simple, inspeccionada y reversible, y limpiar el estado temporal. El guardado de la escena de aceptación dentro del área de pruebas del repo corresponde a la Fase 6.

**Validaciones:** información recibida, primera operación `bpy` de solo lectura, operación reversible, limpieza del estado temporal, y comprobación técnica de las rutas y permisos observables. La apertura/guardado del fixture se valida en la Fase 6. La política de no acceder fuera del workspace se mantiene aunque no exista sandbox técnico; no se marca como `PASS` una limitación que no pueda demostrarse.

**Rollback:** cerrar Blender sin sobrescribir escenas canónicas y eliminar o aislar la escena de smoke solo después de verificar su alcance.

**Autorización:** obligatoria para ejecutar el primer código `bpy` mediante MCP y para cualquier escritura en el workspace desde Blender.

### Fase 6 — Test de aceptación funcional de la habitación

**Objetivo:** validar el flujo completo con una habitación mínima sintética y sin assets externos.

**Acciones:**

- Crear suelo, paredes, puerta, ventana, `sofa_proxy`, cámara y luz con geometría simple.
- Aplicar el volumen interior exacto `X: 0.00..5.00 m`, `Y: 0.00..4.00 m`, `Z: 0.00..2.50 m`; validar esas caras interiores aunque las paredes tengan grosor hacia fuera.
- Crear la puerta sintética de `0.90 × 0.05 × 2.10 m` en `(1.45, -0.025, 1.05) m`, la ventana sintética de `0.05 × 1.20 × 1.00 m` en `(5.025, 2.00, 1.50) m` y `sofa_proxy` de `1.80 × 0.80 × 0.90 m` en `(2.50, 2.00, 0.45) m`, con rotación cero.
- Recrear la escena con las mismas constantes, nombres y transformaciones en portátil y sobremesa, sin aleatoriedad ni assets externos.
- Guardar la escena en `blender/scenes/tests/001-foundation-room.blend` o área de pruebas equivalente.
- Obtener captura de viewport o render preview.
- Medir largo, ancho, altura, posición y tamaño del sofá proxy desde Blender/MCP.

**Validaciones:** las caras interiores y los valores de puerta, ventana y `sofa_proxy` coinciden con el contrato, las unidades son metros, la escena abre/guarda, la evidencia visual se inspecciona y el rendimiento es suficiente para preview.

**Rollback:** tratar la escena como desechable, conservarla solo como evidencia o fixture explícitamente identificado y nunca usarla como escena canónica.

**Autorización:** obligatoria antes de ejecutar la prueba completa y generar cualquier render/captura que deba conservarse.

### Fase 7 — Documentación reproducible para el segundo equipo

**Objetivo:** permitir repetir la validación del fixture en el PC de sobremesa sin depender de memoria implícita ni de rutas del portátil.

**Estado:** la reproducción del fixture se probó entre portátil y sobremesa. Se conservan variables sanitizadas y no se añaden rutas ni un inventario del sobremesa que no estén documentados.

**Acciones:**

- Documentar versiones, fuentes, hashes, rutas configurables, orden de arranque y comprobaciones.
- Separar hechos comunes de diferencias de hardware, GPU, VRAM, RAM y sistema operativo.
- Registrar cómo repetir el smoke y el test de habitación sin modificar medidas canónicas.
- Indicar qué configuración no se versiona y cómo se valida localmente.

**Validaciones:** una persona puede seguir los pasos, reproducir la conexión local y obtener la misma evidencia funcional con variaciones de ruta documentadas.

**Rollback:** revertir únicamente documentación o configuración local de la segunda máquina; conservar el repositorio y no sincronizar secretos ni preferencias personales.

**Autorización:** obligatoria antes de repetir instalaciones o ejecutar el test en el sobremesa; la documentación puede prepararse sin instalar nada.

## Validaciones transversales

- `git diff --check` y revisión del diff completo.
- Validación sintáctica de scripts Python cuando existan.
- Ejecución real de scripts `bpy` relacionados cuando Blender esté disponible.
- Smoke de Blender/MCP/Codex y apertura/guardado de la escena de prueba.
- Verificación de loopback, secretos, rutas, licencias, archivos binarios y tamaños.
- Verificación del acceso a archivos: inspeccionar código, rutas y permisos/auditoría disponibles; distinguir evidencia técnica de la política del proyecto y marcar controles no demostrables como `PENDIENTE DE INFRAESTRUCTURA` o `NO EJECUTADO`.
- Contraste numérico con el contrato sintético y, para espacios reales futuros, con `measurements/`.
- Captura e inspección visual para el test de habitación.
- Preview y comprobación proporcional de VRAM/RAM/tiempo; no renders finales pesados durante setup.

Todo control aún no disponible se marca como `PENDIENTE DE INFRAESTRUCTURA` o `NO APLICA`; nunca como `PASS` inventado.

## Estrategia de reversión y compatibilidad

La integración se mantiene en una rama específica. Las escenas de smoke y aceptación viven en áreas de prueba y se duplican antes de operaciones destructivas. Las medidas canónicas no se editan. La configuración local usa rutas relativas o variables documentadas y no se convierte en una dependencia global del portátil. Una actualización de Blender 5.2.1 LTS o del pin del MCP requiere repetir el smoke y el test funcional antes de aceptarse.

## Dependencias externas

Foundation instalada y validada: Blender 5.2.1 LTS mediante Portable ZIP, Codex CLI y `ahujasid/blender-mcp` fijado al commit `5866814479b4e2ca674d8d44969a9a2a78fdc8bb`. La referencia `webita/blender-codex-mcp` se usó solo para contrastar la integración. No se incorporaron assets externos ni dependencias de producción.
