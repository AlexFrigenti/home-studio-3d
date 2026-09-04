# AGENTS.md

Política operativa para Home Studio 3D. Estas reglas se aplican a Codex y a cualquier agente que trabaje en este repositorio.

## 1. Flujo de trabajo

- No modificar `main` directamente para cambios funcionales o estructurales salvo autorización expresa.
- Trabajar con objetivos acotados.
- Leer `README.md`, `PROJECT_CONTEXT.md`, `.quality/QUALITY.md`, `CONTRIBUTING.md` y cualquier documentación específica relevante antes de editar.
- Clasificar el cambio como T0, T1 o T2 según `.quality/QUALITY.md` antes de modificar archivos.
- Para cambios T1 o T2, crear y mantener `specs/NNN-feature-name/spec.md`, `plan.md` y `tasks.md`.
- No ampliar el alcance con refactors, reorganizaciones o experimentos no solicitados.
- Preferir cambios pequeños, reversibles y verificables.
- No afirmar que algo funciona sin evidencia ni declarar terminado un cambio sin cumplir los gates aplicables.
- No inventar validaciones. Un control no disponible debe quedar marcado como `No aplica` o `Pendiente de infraestructura`, nunca como `PASS`.

## 2. Ejecución agentic proporcional

El control del usuario y el consumo razonable de cuota tienen prioridad sobre maximizar el paralelismo o la autonomía.

Por defecto:

- Usar el agente principal para tareas sencillas.
- No crear subagentes por cada microtarea.
- No desplegar enjambres de agentes.
- No encadenar automáticamente múltiples rondas completas de implementación → revisión → corrección → nueva revisión.
- No usar subagentes solo porque estén disponibles.
- No permitir que un subagente cree otros subagentes salvo autorización explícita del usuario.
- Evitar polling, esperas repetitivas, comprobaciones de estado frecuentes o bucles de consulta de MCP.
- Si una herramienta, MCP, comando o subagente devuelve esencialmente el mismo fallo dos veces, considerar que existe un bloqueo y no seguir reintentando indefinidamente.
- Si no hay progreso material tras dos intentos razonables sobre el mismo bloqueo, detenerse, resumir lo probado y devolver el control al usuario.
- No repetir análisis, renders, capturas, imports, pruebas o verificaciones costosas si la evidencia anterior sigue siendo válida.
- Reutilizar la información ya obtenida dentro de la tarea.
- Cerrar o liberar subagentes terminados cuando el runtime lo permita.

Para trabajo no trivial, el patrón preferido es:

1. Una implementación coherente.
2. Como máximo una revisión independiente cuando aporte valor.
3. Una ronda agrupada de correcciones.
4. Verificación final.

Si después de esa ronda fuese necesaria otra revisión integral, otra ronda sustancial de correcciones, ampliar el número de agentes, cambiar significativamente la estrategia o continuar tras un bloqueo repetido, detenerse, informar del estado y solicitar autorización explícita antes de seguir.

La paralelización solo se permite cuando las tareas sean realmente independientes y el beneficio sea claro. Nunca se debe paralelizar por defecto.

## 3. Blender / MCP — seguridad

Cuando Blender MCP esté disponible:

- Tratar `execute_blender_code` y `bpy` como capacidades privilegiadas.
- No ejecutar código descargado o copiado de fuentes externas sin inspeccionarlo.
- No usar Python para acceder, modificar o borrar archivos fuera del workspace salvo autorización explícita.
- No lanzar procesos externos desde Blender salvo que la tarea lo requiera y esté autorizada.
- Mantener el servidor MCP limitado a localhost.
- No exponer el servidor Blender/MCP a la red local o Internet.
- No introducir secretos ni credenciales en escenas, scripts o configuración versionada.
- No activar telemetría opcional si puede deshabilitarse razonablemente.
- No instalar addons, paquetes o servicios externos sin informar antes de qué se instalará y por qué.

## 4. Operaciones destructivas en Blender

Una vez haya escenas reales:

- Guardar antes de operaciones destructivas importantes.
- Preferir duplicación, colecciones alternativas o snapshots frente a destrucción irreversible.
- No eliminar en masa objetos, colecciones, materiales o assets sin verificar el alcance.
- No sobrescribir una escena canónica con un experimento.
- Las propuestas de decoración deben ser variantes separables y reversibles cuando sea razonable.
- Nunca sustituir medidas reales por aproximaciones silenciosas.

## 5. Medidas como fuente de verdad

Las dimensiones reales registradas en `measurements/` son la fuente de verdad.

- Blender representa esas medidas; no las redefine.
- No cambiar una medida canónica para hacer que una geometría “encaje”.
- Si hay discrepancia entre datos y escena, informar de ella.
- Mantener unidades explícitas.
- Preferir metros como unidad interna de Blender y documentar cualquier excepción.
- No inventar medidas faltantes como si fueran reales. Las aproximaciones deben quedar marcadas como tales.

## 6. Assets externos

Antes de incorporar un asset externo:

- Identificar su procedencia.
- Conocer la licencia o las condiciones relevantes.
- Registrar sus dimensiones cuando sean importantes.
- No añadir assets comerciales o premium al repositorio si su licencia no lo permite.
- No descargar grandes cantidades de assets automáticamente.
- No utilizar servicios de pago o créditos de generación sin autorización explícita.

## 7. Feedback visual y validación

Para cambios visuales relevantes futuros:

- Inspeccionar la escena.
- Verificar transformaciones y dimensiones numéricamente cuando corresponda.
- Obtener una captura del viewport o un render.
- Comprobar visualmente el resultado.
- Corregir solo si existe una desviación concreta.
- Evitar iterar indefinidamente buscando mejoras subjetivas marginales.

Un resultado visual no se considera validado solo porque un script terminó sin errores.

## 8. Coste computacional

- No lanzar renders finales cuando un preview sea suficiente.
- Usar resoluciones y calidad de preview durante la iteración.
- Reservar Cycles de alta calidad para verificaciones o entregables que lo justifiquen.
- No generar múltiples renders pesados sin necesidad.
- Informar antes de iniciar operaciones excepcionalmente costosas o masivas.

## 9. Git

- No hacer `push --force`, reescritura de historia, reset destructivo o borrado de ramas sin autorización explícita.
- No hacer merge a `main` sin autorización explícita.
- No asumir que un archivo binario puede fusionarse correctamente.
- Tratar los archivos `.blend` como binarios.
- No añadir Git LFS hasta que exista una decisión explícita sobre su estrategia.

## 10. Entrega

Al terminar cada tarea, informar de forma compacta:

- Rama y HEAD.
- Archivos modificados.
- Qué cambió.
- Validaciones ejecutadas.
- Evidencia visual si aplica.
- Riesgos, limitaciones o bloqueos.
- Cualquier operación que requiera autorización posterior.
